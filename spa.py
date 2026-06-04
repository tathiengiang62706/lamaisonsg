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

st.set_page_config(page_title="La Maison Beauté - Booking System", layout="wide")

# Khởi tạo trạng thái bộ nhớ
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "editing_customer_id" not in st.session_state:
    st.session_state.editing_customer_id = None
if "is_admin_mode" not in st.session_state:
    st.session_state.is_admin_mode = False

DUY_NHAT_SERVICE = "Chăm sóc da mặt chuyên sâu"
TEN_SPA = "La Maison Beauté"

URL_LOGO_SPA = "https://i.imgur.com/your-logo-link.png" 
URL_NỀN_SPA = "https://images.unsplash.com/photo-1540555700478-4be289fbecef?q=80&w=1920" 

DANH_SACH_QUAN_HCM = [
    "Quận 1, TP. HCM", "Quận 3, TP. HCM", "Quận 4, TP. HCM", "Quận 5, TP. HCM",
    "Quận 6, TP. HCM", "Quận 7, TP. HCM", "Quận 8, TP. HCM", "Quận 10, TP. HCM",
    "Quận 11, TP. HCM", "Quận 12, TP. HCM", "Quận Bình Tân, TP. HCM", "Quận Bình Thạnh, TP. HCM",
    "Quận Gò Vấp, TP. HCM", "Quận Phú Nhuận, TP. HCM", "Quận Tân Bình, TP. HCM", "Quận Tân Phú, TP. HCM",
    "TP. Thủ Đức, TP. HCM", "Huyện Bình Chánh, TP. HCM", "Huyện Cần Giờ, TP. HCM", "Huyện Củ Chi, TP. HCM",
    "Huyện Hóc Môn, TP. HCM", "Huyện Nhà Bè, TP. HCM"
]

def generate_ics_download_link(summary, start_dt, end_dt):
    s_str = start_dt.strftime("%Y%m%dT%H%M%SZ")
    e_str = end_dt.strftime("%Y%m%dT%H%M%SZ")
    ics_content = f"BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//{TEN_SPA}//NONSGML Event//EN\nBEGIN:VEVENT\nSUMMARY:{summary}\nDTSTART:{s_str}\nDTEND:{e_str}\nDESCRIPTION:Hẹn gặp bạn tại {TEN_SPA}!\nSTATUS:CONFIRMED\nEND:VEVENT\nEND:VCALENDAR"
    b64 = base64.b64encode(ics_content.encode('utf-8')).decode()
    href = f'<a href="data:text/calendar;charset=utf-8;base64,{b64}" download="lich_hen_spa.ics" style="display: inline-block; padding: 12px 24px; background-color: #D4AF37; color: white; text-decoration: none; border-radius: 50px; font-weight: bold; margin-top: 10px; box-shadow: 0 4px 15px rgba(212,175,55,0.3);">📅 Thêm Vào Lịch iPhone (Apple Calendar)</a>'
    return href

# -------------------------------------------------------------------------
# 2. XỬ LÝ ĐƯỜNG DẪN ẨN
# -------------------------------------------------------------------------
if st.query_params.get("page") == "admin":
    st.session_state.is_admin_mode = True

# =========================================================================
# LUỒNG 1: GIAO DIỆN CHỦ SPA
# =========================================================================
if st.session_state.is_admin_mode:
    st.markdown(f"<h2 style='color: #af9444; font-family: \"Playfair Display\", serif;'>💆‍♂️ HỆ THỐNG QUẢN TRỊ NỘI BỘ - {TEN_SPA.upper()}</h2>", unsafe_allow_html=True)
    st.write("---")

    if not st.session_state.logged_in:
        st.subheader("🔑 Đăng nhập quyền quản trị")
        with st.container(border=True):
            username = st.text_input("Tài khoản admin:")
            password = st.text_input("Mật khẩu admin:", type="password")
            if st.button("Đăng nhập ngay", type="primary"):
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu!")
    else:
        st.write(f"Chào mừng chủ tiệm đăng nhập hệ thống quản lý của **{TEN_SPA}**")
        if st.button("🚪 Đăng xuất khỏi Admin"):
            st.session_state.logged_in = False
            st.session_state.is_admin_mode = False
            st.query_params.clear()
            st.rerun()
            
        tab1, tab2, tab3 = st.tabs(["➕ Tạo & Xóa Lịch Trống", "👤 Quản Lý Khách Hàng", "📋 Quản Lý Đặt Lịch"])
        
        # ---- TAB 1: QUẢN LÝ LỊCH TRỐNG ----
        with tab1:
            st.markdown("#### Tạo khung giờ mở cửa cho Spa")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                date = st.date_input("Chọn ngày làm việc", datetime.today(), key="adm_date")
            with col_t2:
                start_time = st.time_input("Giờ bắt đầu đón khách", datetime.now().time(), key="adm_time")
                
            if st.button("Xác Nhận Tạo Khung Giờ", type="primary"):
                start_dt = datetime.combine(date, start_time)
                end_dt = start_dt + timedelta(minutes=90)
                data = {"start_time": start_dt.isoformat(), "end_time": end_dt.isoformat(), "status": "available"}
                if supabase:
                    supabase.table("slots").insert(data).execute()
                    st.success(f"✅ Đã tạo lịch trống thành công!")
                    st.rerun()

            st.write("---")
            st.markdown("#### 📋 Danh sách các khung giờ đã tạo")
            if supabase:
                all_slots_res = supabase.table("slots").select("*").order("start_time").execute()
                all_slots = all_slots_res.data if all_slots_res.data else []
                
                bookings_map = {}
                bookings_res = supabase.table("bookings").select("*, customers(*)").execute()
                if bookings_res.data:
                    for b in bookings_res.data:
                        bookings_map[b["slot_id"]] = b
                
                if not all_slots:
                    st.info("Hiện tại chưa có khung giờ nào được tạo.")
                else:
                    filter_status = st.radio("Lọc danh sách theo trạng thái:", ["Tất cả", "Chưa ai đặt (Trống)", "Đã có người đặt (Kín)"], horizontal=True)
                    for s in all_slots:
                        if filter_status == "Chưa ai đặt (Trống)" and s["status"] != "available": continue
                        if filter_status == "Đã có người đặt (Kín)" and s["status"] != "booked": continue
                        
                        s_obj = datetime.fromisoformat(s["start_time"])
                        e_obj = datetime.fromisoformat(s["end_time"])
                        time_display = f"⏱️ **{s_obj.strftime('%H:%M')} - {e_obj.strftime('%H:%M')}** ngày `{s_obj.strftime('%d/%m/%Y')}`"
                        
                        customer_info_str = ""
                        if s["status"] == "available":
                            badge = "🔵 Trống (Chờ đặt)"
                        else:
                            badge = "🟢 Đã có khách book"
                            b_detail = bookings_map.get(s["id"])
                            if b_detail and b_detail.get("customers"):
                                c_info = b_detail["customers"]
                                customer_info_str = f"👤 Khách: **{c_info['full_name']}** - SĐT: `{c_info['phone']}`"
                            
                        with st.container(border=True):
                            c_slot1, c_slot2, c_slot3 = st.columns([3, 2, 1])
                            c_slot1.markdown(time_display)
                            if customer_info_str: c_slot1.markdown(customer_info_str)
                            c_slot2.markdown(f"Trạng thái: **{badge}**")
                            
                            if c_slot3.button("🗑️ Xóa", key=f"del_slot_{s['id']}", type="secondary"):
                                supabase.table("slots").delete().eq("id", s["id"]).execute()
                                st.rerun()

        # ---- TAB 2: QUẢN LÝ KHÁCH HÀNG ----
        with tab2:
            st.markdown("### ➕ Tạo tài khoản mới cho khách hàng")
            with st.container(border=True):
                c_name = st.text_input("Họ và tên khách hàng:")
                c_phone = st.text_input("Số điện thoại khách:")
                
                region_option = st.radio("Khu vực sinh sống của khách:", ["📍 Thuộc TP. Hồ Chí Minh", "✈️ Tỉnh thành khác"], horizontal=True)
                
                if region_option == "📍 Thuộc TP. Hồ Chí Minh":
                    c_address = st.selectbox("Chọn quận/huyện tại TP.HCM:", DANH_SACH_QUAN_HCM)
                else:
                    c_address = st.text_input("Nhập tên Tỉnh/Thành phố của khách ở xa:")
                
                if st.button("Tạo tài khoản khách", type="primary"):
                    if not c_name.strip() or not c_phone.strip():
                        st.error("Vui lòng điền đầy đủ Họ tên và Số điện thoại khách!")
                    elif supabase:
                        try:
                            final_address = c_address.strip() if c_address else "Chưa cập nhật"
                            supabase.table("customers").insert({
                                "full_name": c_name.strip(), 
                                "phone": c_phone.strip(),
                                "address": final_address
                            }).execute()
                            st.success(f"🎉 Đã tạo thành công tài khoản!")
                            st.rerun()
                        except Exception:
                            st.error("Số điện thoại này đã tồn tại trên hệ thống!")

            st.write("---")
            st.markdown("### 👤 Danh sách khách hàng hiện có")
            
            if supabase:
                cust_res = supabase.table("customers").select("*").order("full_name").execute()
                customers_list = cust_res.data if cust_res.data else []
                
                if not customers_list:
                    st.info("Hiện chưa có tài khoản khách hàng nào.")
                else:
                    # GIAO DIỆN SỬA ĐỊA CHỈ KHÁCH HÀNG 
                    if st.session_state.editing_customer_id:
                        current_edit_id = st.session_state.editing_customer_id
                        edit_cust = next((c for c in customers_list if c["id"] == current_edit_id), None)
                        
                        if edit_cust:
                            st.markdown(f"#### 🛠️ Cập nhật thông tin: **{edit_cust['full_name']}**")
                            
                            with st.form(key=f"form_edit_cust"):
                                new_name = st.text_input("Sửa Họ và Tên:", value=edit_cust["full_name"])
                                new_phone = st.text_input("Sửa Số điện thoại:", value=edit_cust["phone"])
                                
                                current_addr = edit_cust.get("address", "")
                                st.caption(f"Địa chỉ hiện tại: **{current_addr}**")
                                
                                is_hcm_addr = current_addr in DANH_SACH_QUAN_HCM
                                default_hcm_idx = DANH_SACH_QUAN_HCM.index(current_addr) if is_hcm_addr else 0
                                
                                st.write("**Thay đổi địa chỉ mới:**")
                                new_hcm_addr = st.selectbox("1. Nếu ở TP.HCM, chọn tại đây:", ["-- Khách không ở TP.HCM --"] + DANH_SACH_QUAN_HCM, index=(default_hcm_idx + 1 if is_hcm_addr else 0))
                                new_other_addr = st.text_input("2. Hoặc nhập Tỉnh/Thành phố khác:", value="" if is_hcm_addr else current_addr)
                                
                                submit_edit = st.form_submit_button("💾 Lưu thay đổi", type="primary")
                                
                                if submit_edit:
                                    if new_name.strip() and new_phone.strip():
                                        if new_other_addr.strip():
                                            final_edited_address = new_other_addr.strip()
                                        elif new_hcm_addr != "-- Khách không ở TP.HCM --":
                                            final_edited_address = new_hcm_addr
                                        else:
                                            final_edited_address = "Chưa cập nhật"
                                            
                                        supabase.table("customers").update({
                                            "full_name": new_name.strip(), 
                                            "phone": new_phone.strip(),
                                            "address": final_edited_address
                                        }).eq("id", current_edit_id).execute()
                                        
                                        st.session_state.editing_customer_id = None
                                        st.rerun()
                                    else:
                                        st.error("Không được để trống Tên hoặc Số điện thoại!")
                            
                            if st.button("❌ Đóng Form Sửa"):
                                st.session_state.editing_customer_id = None
                                st.rerun()
                            st.write("---")

                    # Vòng lặp hiển thị danh sách khách hàng
                    for cust in customers_list:
                        with st.container(border=True):
                            c_col1, c_col2, c_col3 = st.columns([3, 1, 1])
                            addr_display = cust.get("address") if cust.get("address") else "Chưa cập nhật địa chỉ"
                            
                            c_col1.markdown(f"👤 Tên khách: **{cust['full_name']}**")
                            c_col1.markdown(f"📱 SĐT: `{cust['phone']}` | 🏠 Đ/C: ` {addr_display} `")
                            
                            if c_col2.button("✏️ Sửa", key=f"edit_cust_{cust['id']}", use_container_width=True):
                                st.session_state.editing_customer_id = cust["id"]
                                st.rerun()
                                
                            if c_col3.button("🗑️ Xóa", key=f"del_cust_{cust['id']}", type="secondary", use_container_width=True):
                                supabase.table("customers").delete().eq("id", cust["id"]).execute()
                                st.rerun()

        # ---- TAB 3: QUẢN LÝ LỊCH HẸN & ĐIỂM DANH ----
        with tab3:
            st.markdown("#### Quản lý danh sách đặt lịch và điểm danh")
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
                            status_label = "🟢 Đã tham gia" if current_status == "completed" else "🔴 Không đến" if current_status == "no_show" else "🔵 Chờ đến hẹn"

                            with st.container(border=True):
                                c1, c2, c3 = st.columns([2, 2, 1])
                                c1.markdown(f"👤 **Khách:** {cust_info['full_name']} ({cust_info['phone']})")
                                c1.markdown(f"🏠 **Địa chỉ:** {cust_info.get('address', 'Chưa cập nhật')}")
                                c1.markdown(f"Trạng thái: **{status_label}**")
                                c2.markdown(f"🕒 **Thời gian:** {view_admin_time}")
                                if current_status == "confirmed":
                                    col_btn1, col_btn2 = c2.columns(2)
                                    if col_btn1.button("✅ Có tham gia", key=f"att_done_{b['id']}"):
                                        supabase.table("bookings").update({"status": "completed"}).eq("id", b["id"]).execute()
                                        st.rerun()
                                    if col_btn2.button("❌ Không đến", key=f"att_abs_{b['id']}"):
                                        supabase.table("bookings").update({"status": "no_show"}).eq("id", b["id"]).execute()
                                        st.rerun()
                                            
                                msg = f"Chào {cust_info['full_name']}, {TEN_SPA} xác nhận lịch hẹn dịch vụ [{b['service_name']}] của bạn vào lúc {zalo_msg_time}. Hẹn gặp bạn nhé!"
                                c3.markdown(f"[💬 Nhắc Zalo](https://zalo.me/{cust_info['phone']})")
                                c3.code(msg, language="text")

# =========================================================================
# LUỒNG 2: GIAO DIỆN KHÁCH HÀNG
# =========================================================================
else:
    from streamlit_calendar import calendar

    style_html = f"""
    <style>
        .stApp {{
            background-image: linear-gradient(rgba(255, 255, 255, 0.82), rgba(245, 240, 230, 0.88)), url("{URL_NỀN_SPA}");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        [data-testid="stForm"], .stForm, [data-testid="stExpander"], .element-container div.stMarkdown {{
            background-color: rgba(255, 255, 255, 0.65) !important;
            backdrop-filter: blur(10px); border-radius: 16px !important; border: 1px solid rgba(212, 175, 55, 0.2) !important;
        }}
    </style>
    """
    st.markdown(style_html, unsafe_allow_html=True)

    st.markdown("<div style='text-align: center; margin-bottom: 20px;'>", unsafe_allow_html=True)
    st.image(URL_LOGO_SPA, width=180, caption=None) 
    st.markdown(f"<h1 style='text-align: center; color: #af9444; font-family: \"Playfair Display\", serif; letter-spacing: 2px; margin-top:10px;'>{TEN_SPA.upper()}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-style: italic; color: #8A7322;'>Không gian chăm sóc sắc đẹp cao cấp độc bản</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    tab_cust1, tab_cust2 = st.tabs(["✨ ĐẶT LỊCH HẸN MỚI", "📋 LỊCH SỬ BUỔI HẸN ĐÃ THAM GIA"])

    with tab_cust1:
        if supabase:
            slot_res = supabase.table("slots").select("*").eq("status", "available").order("start_time").execute()
            available_slots = slot_res.data if slot_res.data else []
            
            if not available_slots:
                st.warning(f"Hiện tại {TEN_SPA} đã kín lịch. Bạn vui lòng quay lại sau nhé!")
            else:
                st.markdown(f"<div style='background-color: rgba(212,175,55,0.1); padding: 15px; border-radius: 12px; border-left: 5px solid #D4AF37; margin-bottom:15px;'>✨ Gói dịch vụ độc quyền: <b>{DUY_NHAT_SERVICE}</b> (Liệu trình trọn gói 75 phút)</div>", unsafe_allow_html=True)
                st.markdown("### 📅 Chọn mốc giờ trống trực tiếp trên bộ lịch tháng")

                calendar_events = []
                for slot in available_slots:
                    start_obj = datetime.fromisoformat(slot["start_time"])
                    calendar_events.append({
                        "id": str(slot["id"]),
                        "title": f"🕒 {start_obj.strftime('%H:%M')}",
                        "start": slot["start_time"],
                        "end": slot["end_time"],
                        "color": "#af9444", 
                        "textColor": "#ffffff"
                    })

                calendar_options = {
                    "initialView": "dayGridMonth",
                    "headerToolbar": {"left": "prev,next", "center": "title", "right": ""},
                    "locale": "vi", "selectable": True, "contentHeight": "auto", "displayEventTime": False 
                }
                
                custom_css = """
                    .fc .fc-daygrid-body { width: 100% !important; }
                    .fc-daygrid-day-number { color: #555 !important; font-weight: bold !important; font-size: 14px !important; }
                    .fc-daygrid-day { background: rgba(255,255,255,0.3) !important; }
                    .fc-daygrid-event {
                        white-space: normal !important; display: inline-block !important; margin: 3px 2px !important; padding: 4px 8px !important;
                        border-radius: 30px !important; font-size: 12px !important; font-weight: bold !important; text-align: center !important; 
                        box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important; border: none !important; width: calc(100% - 4px) !important;
                    }
                    @media (max-width: 768px) {
                        .fc-daygrid-event { width: auto !important; display: inline-block !important; float: left !important; }
                    }
                """
                
                state = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key="spa_calendar_responsive")
                
                selected_slot = None
                if state.get("eventClick"):
                    clicked_event_id = int(state["eventClick"]["event"]["id"])
                    selected_slot = next((s for s in available_slots if s["id"] == clicked_event_id), None)

                if selected_slot:
                    st_obj = datetime.fromisoformat(selected_slot["start_time"])
                    en_obj = st_obj + timedelta(minutes=90)
                    
                    st.write("---")
                    st.markdown("### 📝 Xác nhận tài khoản và đặt lịch")
                    st.success(f"🎯 Khung giờ bạn chọn: **{st_obj.strftime('%H:%M')} - {en_obj.strftime('%H:%M')}** ngày **{st_obj.strftime('%d/%m/%Y')}**")
                    
                    with st.form("booking_form_luxury"):
                        input_phone = st.text_input("Nhập Số điện thoại của bạn (đã được Spa kích hoạt):")
                        btn_booking = st.form_submit_button("Xác Nhận Đăng Ký Đặt Lịch")
                        
                        if btn_booking:
                            if not input_phone.strip():
                                st.error("Vui lòng nhập Số điện thoại!")
                            else:
                                check_cust = supabase.table("customers").select("*").eq("phone", input_phone.strip()).execute()
                                if not check_cust.data:
                                    st.error(f"❌ Số điện thoại này chưa được kích hoạt thành viên tại {TEN_SPA}!")
                                else:
                                    info_khach = check_cust.data[0]
                                    booking_data = {"slot_id": selected_slot["id"], "customer_id": info_khach["id"], "service_name": DUY_NHAT_SERVICE, "status": "confirmed"}
                                    supabase.table("bookings").insert(booking_data).execute()
                                    supabase.table("slots").update({"status": "booked"}).eq("id", selected_slot["id"]).execute()
                                    
                                    st.balloons()
                                    st.success(f"🎉 Đặt lịch thành công! Hân hạnh được đón tiếp chị {info_khach['full_name']}.")
                                    
                                    summary_text = f"Lịch hẹn {TEN_SPA} - {DUY_NHAT_SERVICE}"
                                    ics_button_html = generate_ics_download_link(summary_text, st_obj, en_obj)
                                    st.markdown(ics_button_html, unsafe_allow_html=True)
                else:
                    st.warning("👈 Chạm nhẹ vào ô mốc giờ màu vàng hoàng gia trên bộ lịch để tiến hành điền thông tin đăng ký.")

    with tab_cust2:
        st.markdown(f"#### Xem lịch sử các buổi làm đẹp tại {TEN_SPA}")
        search_phone = st.text_input("Nhập số điện thoại tài khoản để tra cứu:", key="history_phone_input")
        if st.button("Tra cứu ngay", type="primary"):
            if search_phone.strip() and supabase:
                check_user = supabase.table("customers").select("*").eq("phone", search_phone.strip()).execute()
                if not check_user.data:
                    st.error("❌ Số điện thoại không tồn tại!")
                else:
                    user_info = check_user.data[0]
                    st.success(f"Thành viên: **{user_info['full_name']}**")
                    history_res = supabase.table("bookings").select("*, slots(*)").eq("customer_id", user_info["id"]).eq("status", "completed").execute()
                    
                    if not history_res.data:
                        st.info("Bạn chưa có buổi làm đẹp nào được ghi nhận hoàn thành.")
                    else:
                        for idx, h in enumerate(history_res.data):
                            slot_h = h.get("slots")
                            if slot_h:
                                st_obj = datetime.fromisoformat(slot_h["start_time"])
                                with st.container(border=True):
                                    col_h1, col_h2 = st.columns([3, 1])
                                    col_h1.markdown(f"**Buổi {idx + 1}:** `{h['service_name']}`\n\n⏰ {st_obj.strftime('%H:%M')} ngày {st_obj.strftime('%d/%m/%Y')}")
                                    col_h2.markdown("<h5 style='color: #af9444; margin:0;'>✨ Đã hoàn thành</h5>", unsafe_allow_html=True)