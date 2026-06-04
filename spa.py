import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
import urllib.parse
import base64

# -------------------------------------------------------------------------
# 1. CẤU HÌNH BẢO MẬT VÀ KẾT NỐI SUPABASE
# -------------------------------------------------------------------------
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = "https://your-supabase-url.supabase.co"
    SUPABASE_KEY = "your-supabase-anon-key"

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Lỗi khởi tạo kết nối Supabase: {e}")
        return None

supabase: Client = init_supabase()

st.set_page_config(page_title="Private Spa Booking System", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_role" not in st.session_state:
    st.session_state.current_role = "Khách Hàng"

DUY_NHAT_SERVICE = "Chăm sóc da mặt chuyên sâu"

# Hàm sinh file lịch .ics để add thẳng vào iPhone
def generate_ics_download_link(summary, start_dt, end_dt):
    # Định dạng thời gian chuẩn iCalendar (YYYYMMDDTHMMSSZ)
    s_str = start_dt.strftime("%Y%m%dT%H%M%SZ")
    e_str = end_dt.strftime("%Y%m%dT%H%M%SZ")
    
    # Nội dung file cấu hình cấu trúc lịch Apple/Outlook
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Private Spa//NONSGML Event//EN
BEGIN:VEVENT
SUMMARY:{summary}
DTSTART:{s_str}
DTEND:{e_str}
DESCRIPTION:Hẹn gặp bạn tại Private Spa để làm dịch vụ chăm sóc sắc đẹp!
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
    
    # Mã hóa nội dung sang Base64 để Streamlit có thể tạo nút tải/mở trực tiếp
    b64 = base64.b64encode(ics_content.encode('utf-8')).decode()
    href = f'<a href="data:text/calendar;charset=utf-8;base64,{b64}" download="lich_hen_spa.ics" style="display: inline-block; padding: 10px 20px; background-color: #007aff; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 10px;">📅 Thêm Vào Lịch iPhone (Apple Calendar)</a>'
    return href

# --- THANH MENU ĐIỀU HƯỚNG TRÊN CÙNG TRANG WEB ---
st.markdown("### 🌟 HỆ THỐNG ĐẶT LỊCH VÀ QUẢN LÝ PRIVATE SPA")
col_menu1, col_menu2 = st.columns(2)

with col_menu1:
    if st.button("✨ GIAO DIỆN KHÁCH HÀNG", use_container_width=True, type="secondary" if st.session_state.current_role == "Chủ Spa (Admin)" else "primary"):
        st.session_state.current_role = "Khách Hàng"
        st.rerun()

with col_menu2:
    if st.button("💆‍♂️ GIAO DIỆN CHỦ SPA (ADMIN)", use_container_width=True, type="primary" if st.session_state.current_role == "Chủ Spa (Admin)" else "secondary"):
        st.session_state.current_role = "Chủ Spa (Admin)"
        st.rerun()

st.write("---")

# -------------------------------------------------------------------------
# PHẦN A: GIAO DIỆN CHỦ SPA (ADMIN)
# -------------------------------------------------------------------------
if st.session_state.current_role == "Chủ Spa (Admin)":
    if not st.session_state.logged_in:
        st.subheader("🔑 Đăng nhập quyền quản trị Spa")
        with st.container(border=True):
            username = st.text_input("Tài khoản admin:")
            password = st.text_input("Mật khẩu admin:", type="password")
            login_submit = st.button("Đăng nhập ngay", type="primary")
            
            if login_submit:
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.success("Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu!")
    else:
        st.subheader("⚙️ Khu vực quản trị của Chủ Spa")
        if st.button("🚪 Đăng xuất khỏi Admin"):
            st.session_state.logged_in = False
            st.rerun()
            
        tab1, tab2, tab3 = st.tabs(["➕ Tạo & Xóa Lịch Trống (75p)", "👤 Tạo Tài Khoản Khách Hàng", "📋 Quản Lý Lịch Hẹn & Điểm Danh"])
        
        with tab1:
            st.markdown("#### Tạo khung giờ mở cửa cho Spa")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                date = st.date_input("Chọn ngày làm việc", datetime.today(), key="adm_date")
            with col_t2:
                start_time = st.time_input("Giờ bắt đầu đón khách", datetime.now().time(), key="adm_time")
                
            if st.button("Xác Nhận Tạo Khung Giờ", type="primary", key="btn_create_slot"):
                start_dt = datetime.combine(date, start_time)
                end_dt = start_dt + timedelta(minutes=75)
                
                data = {"start_time": start_dt.isoformat(), "end_time": end_dt.isoformat(), "status": "available"}
                if supabase:
                    supabase.table("slots").insert(data).execute()
                    st.success(f"✅ Đã tạo lịch trống thành công: {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')} ngày {date.strftime('%d/%m/%Y')}")
                    st.rerun()

            st.write("---")
            st.markdown("#### 📋 Danh sách các khung giờ đã tạo")
            
            if supabase:
                all_slots_res = supabase.table("slots").select("*").order("start_time", descending=False).execute()
                all_slots = all_slots_res.data if all_slots_res.data else []
                
                if not all_slots:
                    st.info("Hiện tại chưa có khung giờ nào được tạo.")
                else:
                    filter_status = st.radio("Lọc danh sách theo trạng thái:", ["Tất cả", "Chưa ai đặt (Trống)", "Đã có người đặt (Kín)"], horizontal=True, key="filter_slot_status")
                    
                    for s in all_slots:
                        if filter_status == "Chưa ai đặt (Trống)" and s["status"] != "available":
                            continue
                        if filter_status == "Đã có người đặt (Kín)" and s["status"] != "booked":
                            continue
                            
                        s_obj = datetime.fromisoformat(s["start_time"])
                        e_obj = datetime.fromisoformat(s["end_time"])
                        time_display = f"⏱️ **{s_obj.strftime('%H:%M')} - {e_obj.strftime('%H:%M')}** ngày `{s_obj.strftime('%d/%m/%Y')}`"
                        
                        badge = "🔵 Trống (Chờ đặt)" if s["status"] == "available" else "🟢 Đã có khách book"
                            
                        with st.container(border=True):
                            c_slot1, c_slot2, c_slot3 = st.columns([3, 2, 1])
                            c_slot1.markdown(time_display)
                            c_slot2.markdown(f"Trạng thái: **{badge}**")
                            
                            if c_slot3.button("🗑️ Xóa", key=f"del_slot_{s['id']}", type="secondary"):
                                supabase.table("slots").delete().eq("id", s["id"]).execute()
                                st.rerun()

        with tab2:
            st.markdown("#### Tạo tài khoản mới cho khách hàng")
            with st.container(border=True):
                c_name = st.text_input("Họ và tên khách hàng:", key="adm_cust_name")
                c_phone = st.text_input("Số điện thoại khách:", key="adm_cust_phone")
                add_submit = st.button("Tạo tài khoản khách", type="primary", key="btn_save_cust")
                
                if add_submit:
                    if c_name and c_phone and supabase:
                        try:
                            phone_clean = c_phone.strip()
                            supabase.table("customers").insert({"full_name": c_name, "phone": phone_clean}).execute()
                            st.success(f"🎉 Đã tạo thành công tài khoản cho khách: **{c_name}** ({phone_clean})")
                        except Exception:
                            st.error("Số điện thoại này đã tồn tại!")

            st.write("---")
            st.markdown("#### Danh sách tài khoản khách hàng")
            if supabase:
                cust_res = supabase.table("customers").select("*").order("full_name").execute()
                if cust_res.data:
                    for cust in cust_res.data:
                        st.write(f"• 👤 **{cust['full_name']}** - SĐT: `{cust['phone']}`")

        with tab3:
            st.markdown("#### Quản lý danh sách đặt lịch và điểm danh khách đến")
            if supabase:
                booking_res = supabase.table("bookings").select("*, slots(*), customers(*)").execute()
                
                if not booking_res.data:
                    st.info("Hiện chưa có lịch hẹn nào được đăng ký.")
                else:
                    for b in booking_res.data:
                        slot_info = b.get("slots")
                        cust_info = b.get("customers")
                        
                        if slot_info and cust_info:
                            start_obj = datetime.fromisoformat(slot_info["start_time"])
                            end_obj = datetime.fromisoformat(slot_info["end_time"])
                            view_admin_time = f"{start_obj.strftime('%H:%M')} - {end_obj.strftime('%H:%M')} ngày {start_obj.strftime('%d/%m/%Y')}"
                            zalo_msg_time = f"{start_obj.strftime('%H:%M')} ngày {start_obj.strftime('%d/%m/%Y')}"
                            
                            current_status = b.get("status", "confirmed")
                            status_label = "🟢 Đã tham gia" if current_status == "completed" else "🔴 Không tham gia (Vắng)" if current_status == "no_show" else "🔵 Chờ đến hẹn"

                            with st.container(border=True):
                                c1, c2, c3 = st.columns([2, 2, 1])
                                c1.markdown(f"👤 **Khách hàng:** {cust_info['full_name']} ({cust_info['phone']})")
                                c1.markdown(f"Trạng thái: **{status_label}**")
                                c2.markdown(f"🕒 **Thời gian:** {view_admin_time}")
                                
                                if current_status == "confirmed":
                                    col_btn1, col_btn2 = c2.columns(2)
                                    with col_btn1:
                                        if st.button("✅ Có tham gia", key=f"att_done_{b['id']}"):
                                            supabase.table("bookings").update({"status": "completed"}).eq("id", b["id"]).execute()
                                            st.rerun()
                                    with col_btn2:
                                        if st.button("❌ Không đến", key=f"att_abs_{b['id']}"):
                                            supabase.table("bookings").update({"status": "no_show"}).eq("id", b["id"]).execute()
                                            st.rerun()
                                            
                                msg = f"Chào {cust_info['full_name']}, Spa xác nhận lịch hẹn dịch vụ [{b['service_name']}] của bạn vào lúc {zalo_msg_time}. Hẹn gặp bạn nhé!"
                                zalo_url = f"https://zalo.me/{cust_info['phone']}"
                                c3.markdown(f"[💬 Nhắc Zalo]({zalo_url})")
                                c3.code(msg, language="text")

# -------------------------------------------------------------------------
# PHẦN B: GIAO DIỆN KHÁCH HÀNG (ĐẶT LỊCH & XEM LỊCH SỬ THAM GIA)
# -------------------------------------------------------------------------
else:
    from streamlit_calendar import calendar

    tab_cust1, tab_cust2 = st.tabs(["✨ ĐẶT LỊCH HẸN MỚI", "📋 LỊCH SỬ BUỔI HẸN ĐÃ THAM GIA"])

    with tab_cust1:
        if supabase:
            slot_res = supabase.table("slots").select("*").eq("status", "available").order("start_time").execute()
            available_slots = slot_res.data if slot_res.data else []
            
            if not available_slots:
                st.warning("Hiện tại Spa đã kín lịch hoặc chưa mở thêm khung giờ trống mới. Bạn vui lòng quay lại sau nhé!")
            else:
                st.info(f"Spa hiện cung cấp dịch vụ độc quyền: **{DUY_NHAT_SERVICE}** (Thời lượng: 75 phút)")
                st.markdown("### 📅 Chọn mốc giờ trống trực tiếp trên bộ lịch tháng")
                st.caption("💡 Mẹo trên iPhone: Chạm nhẹ vào **Ô mốc giờ màu xanh** trong ngày bạn muốn hẹn.")

                calendar_events = []
                for slot in available_slots:
                    start_obj = datetime.fromisoformat(slot["start_time"])
                    calendar_events.append({
                        "id": str(slot["id"]),
                        "title": f"{start_obj.strftime('%H:%M')}",
                        "start": slot["start_time"],
                        "end": slot["end_time"],
                        "color": "#2e7d32",
                        "textColor": "#ffffff"
                    })

                calendar_options = {"initialView": "dayGridMonth", "headerToolbar": {"left": "prev,next", "center": "title", "right": ""}, "locale": "vi", "selectable": True, "contentHeight": "auto"}
                
                custom_css = """
                    .fc .fc-daygrid-body { width: 100% !important; }
                    .fc-daygrid-day-number { color: #222 !important; font-weight: bold !important; font-size: 14px !important; }
                    .fc-daygrid-event {
                        white-space: normal !important; display: inline-block !important; margin: 2px 1px !important; padding: 2px 4px !important;
                        border-radius: 4px !important; font-size: 11px !important; font-weight: bold !important; text-align: center !important; width: calc(100% - 4px) !important;
                    }
                    @media (max-width: 768px) {
                        .fc-daygrid-event { width: auto !important; display: inline-block !important; float: left !important; }
                        .fc-event-title { font-size: 10px !important; } .fc .fc-toolbar-title { font-size: 16px !important; }
                    }
                """
                
                state = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key="spa_calendar_responsive")
                
                selected_slot = None
                if state.get("eventClick"):
                    clicked_event_id = int(state["eventClick"]["event"]["id"])
                    selected_slot = next((s for s in available_slots if s["id"] == clicked_event_id), None)

                if selected_slot:
                    st_obj = datetime.fromisoformat(selected_slot["start_time"])
                    en_obj = datetime.fromisoformat(selected_slot["end_time"])
                    
                    st.write("---")
                    st.markdown("### 📝 Bước cuối: Xác nhận tài khoản và đặt lịch")
                    st.success(f"🎯 Bạn đang chọn: Khung giờ **{st_obj.strftime('%H:%M')} - {en_obj.strftime('%H:%M')}** ngày **{st_obj.strftime('%d/%m/%Y')}**")
                    
                    with st.container(border=True):
                        input_phone = st.text_input("Nhập Số điện thoại của bạn (đã được Spa kích hoạt):", key="cust_phone_login")
                        btn_booking = st.button("Xác Nhận Đăng Ký Đặt Lịch", type="primary", key="btn_confirm_booking")
                        
                        if btn_booking:
                            if not input_phone.strip():
                                st.error("Vui lòng nhập Số điện thoại!")
                            else:
                                check_cust = supabase.table("customers").select("*").eq("phone", input_phone.strip()).execute()
                                
                                if not check_cust.data:
                                    st.error("❌ Số điện thoại này chưa được đăng ký tài khoản tại Spa!")
                                else:
                                    info_khach = check_cust.data[0]
                                    
                                    booking_data = {"slot_id": selected_slot["id"], "customer_id": info_khach["id"], "service_name": DUY_NHAT_SERVICE, "status": "confirmed"}
                                    supabase.table("bookings").insert(booking_data).execute()
                                    supabase.table("slots").update({"status": "booked"}).eq("id", selected_slot["id"]).execute()
                                    
                                    st.balloons()
                                    st.success(f"🎉 Xin chúc mừng {info_khach['full_name']}! Bạn đã đặt lịch hẹn thành công.")
                                    
                                    # TẠO NÚT BẤM APPLE CALENDAR CHO IPHONE (.ICS)
                                    summary_text = f"Lịch hẹn Spa - {DUY_NHAT_SERVICE}"
                                    ics_button_html = generate_ics_download_link(summary_text, st_obj, en_obj)
                                    
                                    st.markdown("👇 Khách hàng dùng iPhone hãy ấn nút dưới đây để lưu lịch vào máy:")
                                    st.markdown(ics_button_html, unsafe_allow_html=True)
                else:
                    st.warning("👈 Vui lòng bấm chọn trực tiếp vào một ô **Mốc Giờ màu xanh** trên bảng lịch tháng ở trên để bắt đầu điền thông tin.")

    with tab_cust2:
        st.markdown("#### Xem lịch sử các buổi làm Spa của bạn")
        search_phone = st.text_input("Nhập số điện thoại tài khoản của bạn để tra cứu lịch sử:", key="history_phone_input")
        btn_search = st.button("Tra cứu ngay", type="primary")
        
        if btn_search or search_phone:
            if not search_phone.strip():
                st.error("Vui lòng nhập số điện thoại!")
            elif supabase:
                check_user = supabase.table("customers").select("*").eq("phone", search_phone.strip()).execute()
                
                if not check_user.data:
                    st.error("❌ Số điện thoại này không tồn tại trên hệ thống!")
                else:
                    user_info = check_user.data[0]
                    st.success(f"Chào **{user_info['full_name']}**, dưới đây là danh sách các buổi bạn đã tham gia làm đẹp tại Spa:")
                    
                    history_res = supabase.table("bookings").select("*, slots(*)").eq("customer_id", user_info["id"]).eq("status", "completed").execute()
                    
                    if not history_res.data:
                        st.info("Nhật ký hệ thống: Bạn chưa có buổi làm Spa nào được ghi nhận hoàn thành (Đã tham gia).")
                    else:
                        for idx, h in enumerate(history_res.data):
                            slot_h = h.get("slots")
                            if slot_h:
                                st_obj = datetime.fromisoformat(slot_h["start_time"])
                                formatted_date = f"⏰ {st_obj.strftime('%H:%M')} ngày {st_obj.strftime('%d/%m/%Y')}"
                                
                                with st.container(border=True):
                                    col_h1, col_h2 = st.columns([3, 1])
                                    col_h1.markdown(f"**Buổi {idx + 1}:** Gói dịch vụ `{h['service_name']}`")
                                    col_h1.markdown(f"Thời gian làm việc: **{formatted_date}**")
                                    col_h2.markdown("<h4 style='color: green; margin:0;'>✨ Đã tham gia</h4>", unsafe_allow_html=True)