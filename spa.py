import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
import urllib.parse

# -------------------------------------------------------------------------
# 1. CẤU HÌNH BẢO MẬT VÀ KẾT NỐI SUPABASE
# -------------------------------------------------------------------------
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = "https://geowicafkaoqsqkajpae.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdlb3dpY2Fma2FvcXNxa2FqcGFlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA0NjE1NzUsImV4cCI6MjA5NjAzNzU3NX0.MAJM-OLfKU1qHdQvz_4iXHT0HfFv0QpuKAxlIUdcCdc"

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
            
        tab1, tab2, tab3 = st.tabs(["➕ Tạo Lịch Trống (75p)", "👤 Tạo Tài Khoản Khách Hàng", "📋 Danh Sách Đặt Lịch"])
        
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
            st.markdown("#### Danh sách các lịch khách đã book")
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
                            
                            with st.container(border=True):
                                c1, c2, c3 = st.columns([2, 2, 1])
                                c1.markdown(f"👤 **Khách hàng:** {cust_info['full_name']} ({cust_info['phone']})")
                                c1.markdown(f"💆‍♂️ **Dịch vụ:** `{b['service_name']}`")
                                c2.markdown(f"🕒 **Thời gian:** {view_admin_time}")
                                
                                msg = f"Chào {cust_info['full_name']}, Spa xác nhận lịch hẹn dịch vụ [{b['service_name']}] của bạn vào lúc {zalo_msg_time}. Hẹn gặp bạn nhé!"
                                zalo_url = f"https://zalo.me/{cust_info['phone']}"
                                c3.markdown(f"[💬 Nhắc Zalo]({zalo_url})")
                                c3.code(msg, language="text")

# -------------------------------------------------------------------------
# PHẦN B: GIAO DIỆN KHÁCH HÀNG (BẢNG LỊCH THÁNG CO GIÃN THÔNG MINH)
# -------------------------------------------------------------------------
else:
    from streamlit_calendar import calendar

    st.subheader("✨ Đặt lịch hẹn Spa trực tuyến")
    
    if supabase:
        slot_res = supabase.table("slots").select("*").eq("status", "available").order("start_time").execute()
        available_slots = slot_res.data if slot_res.data else []
        
        if not available_slots:
            st.warning("Hiện tại Spa đã kín lịch hoặc chưa mở thêm khung giờ trống mới. Bạn vui lòng quay lại sau nhé!")
        else:
            st.info(f"Spa hiện cung cấp dịch vụ độc quyền: **{DUY_NHAT_SERVICE}** (Thời lượng: 75 phút)")
            st.markdown("### 📅 Chọn mốc giờ trống trực tiếp trên bộ lịch tháng")
            st.caption("💡 Mẹo trên điện thoại: Hãy chạm nhẹ vào **Ô mốc giờ màu xanh** trong ngày bạn muốn hẹn để đăng ký.")

            # Chuẩn bị dữ liệu sự kiện lịch
            calendar_events = []
            for slot in available_slots:
                start_obj = datetime.fromisoformat(slot["start_time"])
                calendar_events.append({
                    "id": str(slot["id"]),
                    "title": f"{start_obj.strftime('%H:%M')}", # Chỉ hiện Giờ:Phút cho gọn gàng
                    "start": slot["start_time"],
                    "end": slot["end_time"],
                    "color": "#2e7d32", # Màu nền xanh lục bảo sang trọng cho Spa
                    "textColor": "#ffffff" # Chữ trắng nổi bật
                })

            # Cấu hình FullCalendar
            calendar_options = {
                "initialView": "dayGridMonth",
                "headerToolbar": {
                    "left": "prev,next",
                    "center": "title",
                    "right": ""
                },
                "locale": "vi",
                "selectable": True,
                "contentHeight": "auto" # Tự co giãn chiều cao theo nội dung ô
            }

            # 🛠️ ĐOẠN CSS THẦN KỲ: Ép bộ lịch tự bẻ dòng và co giãn mượt mà trên Mobile
            custom_css = """
                /* Làm gọn ô chứa ngày trên điện thoại */
                .fc .fc-daygrid-body { width: 100% !important; }
                .fc-daygrid-day-number { color: #222 !important; font-weight: bold !important; font-size: 14px !important; }
                
                /* Biến các mốc giờ thành dạng viên thuốc (Badge) tự động xuống dòng */
                .fc-daygrid-event {
                    white-space: normal !important;
                    display: inline-block !important;
                    margin: 2px 1px !important;
                    padding: 2px 4px !important;
                    border-radius: 4px !important;
                    font-size: 11px !important;
                    font-weight: bold !important;
                    text-align: center !important;
                    width: calc(100% - 4px) !important;
                }
                
                /* Khi màn hình nhỏ (Mobile), cho phép nhiều nút giờ xếp cạnh nhau thay vì kéo dài */
                @media (max-width: 768px) {
                    .fc-daygrid-event {
                        width: auto !important;
                        display: inline-block !important;
                        float: left !important;
                    }
                    .fc-event-title { font-size: 10px !important; }
                    .fc .fc-toolbar-title { font-size: 16px !important; }
                }
            """
            
            # Hiển thị bộ lịch
            state = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key="spa_calendar_responsive")
            
            # Kiểm tra sự kiện bấm chọn giờ
            selected_slot = None
            if state.get("eventClick"):
                clicked_event_id = int(state["eventClick"]["event"]["id"])
                selected_slot = next((s for s in available_slots if s["id"] == clicked_event_id), None)

            # Khối xử lý đặt lịch khi có giờ được lựa chọn
            if selected_slot:
                st_obj = datetime.fromisoformat(selected_slot["start_time"])
                en_obj = datetime.fromisoformat(selected_slot["end_time"])
                
                st.write("---")
                st.markdown("### 📝 Bước cuối: Xác nhận tài khoản và đặt lịch")
                st.success(f"🎯 Bạn đang chọn: **{st_obj.strftime('%H:%M')} - {en_obj.strftime('%H:%M')}** ngày **{st_obj.strftime('%d/%m/%Y')}**")
                
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
                                
                                booking_data = {"slot_id": selected_slot["id"], "customer_id": info_khach["id"], "service_name": DUY_NHAT_SERVICE}
                                supabase.table("bookings").insert(booking_data).execute()
                                supabase.table("slots").update({"status": "booked"}).eq("id", selected_slot["id"]).execute()
                                
                                st.balloons()
                                st.success(f"🎉 Xin chúc mừng {info_khach['full_name']}! Bạn đã đặt lịch hẹn thành công.")
                                
                                s_time = st_obj.strftime("%Y%m%dT%H%M%S")
                                e_time = en_obj.strftime("%Y%m%dT%H%M%S")
                                cal_title = urllib.parse.quote(f"Lịch Hẹn Spa - {DUY_NHAT_SERVICE}")
                                cal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={cal_title}&dates={s_time}/{e_time}"
                                st.markdown(f"[📅 Nhấp vào đây để tự thêm lịch hẹn này vào Google Calendar cá nhân của bạn]({cal_url})")
            else:
                st.warning("👈 Vui lòng bấm chọn trực tiếp vào một ô **Mốc Giờ màu xanh** trên bảng lịch tháng ở trên để bắt đầu điền thông tin.")
    else:
        st.error("Không thể tải thông tin do lỗi kết nối API Supabase.")