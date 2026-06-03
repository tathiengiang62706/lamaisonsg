import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
import urllib.parse

# -------------------------------------------------------------------------
# 1. CẤU HÌNH BẢO MẬT VÀ KẾT NỐI SUPABASE
# -------------------------------------------------------------------------
# Hệ thống sẽ tự động đọc từ st.secrets khi chạy Online trên Streamlit Cloud
# Nếu chạy ở máy cá nhân (Local), bạn có thể thay trực tiếp chuỗi URL/Key vào đây để test
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    # Điền thông tin dự án thật của bạn vào đây nếu chạy dưới máy tính (Local)
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

# Cấu hình hiển thị trang của Streamlit
st.set_page_config(page_title="Private Spa Booking System", layout="wide")

# Khởi tạo các trạng thái bộ nhớ hệ thống (Session State) để tránh lỗi reset trang
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_role" not in st.session_state:
    st.session_state.current_role = "Khách Hàng"

# Định nghĩa gói dịch vụ độc quyền duy nhất của Spa
DUY_NHAT_SERVICE = "Chăm sóc da mặt chuyên sâu"


# -------------------------------------------------------------------------
# 2. THANH MENU ĐIỀU HƯỚNG TRÊN CÙNG TRANG WEB
# -------------------------------------------------------------------------
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
    
    # A.1 Xử lý màn hình CHƯA ĐĂNG NHẬP
    if not st.session_state.logged_in:
        st.subheader("🔑 Đăng nhập quyền quản trị Spa")
        with st.container(border=True):
            username = st.text_input("Tài khoản admin:")
            password = st.text_input("Mật khẩu admin:", type="password")
            login_submit = st.button("Đăng nhập ngay", type="primary")
            
            if login_submit:
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.success("Đăng nhập thành công! Đang tải dữ liệu...")
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu! Vui lòng thử lại.")
                    
    # A.2 Xử lý màn hình ĐÃ ĐĂNG NHẬP THÀNH CÔNG
    else:
        st.subheader("⚙️ Khu vực quản trị của Chủ Spa")
        if st.button("🚪 Đăng xuất khỏi Admin"):
            st.session_state.logged_in = False
            st.rerun()
            
        # Tạo 3 Tab chức năng cho Admin
        tab1, tab2, tab3 = st.tabs(["➕ Tạo Lịch Trống (75p)", "👤 Tạo Tài Khoản Khách Hàng", "📋 Danh Sách Đặt Lịch"])
        
        # ---- TAB 1: TẠO KHUNG GIỜ TRỐNG ----
        with tab1:
            st.markdown("#### Tạo khung giờ mở cửa cho Spa")
            st.caption("💡 Mỗi buổi làm Spa được hệ thống cố định chuẩn là **75 phút**.")
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                date = st.date_input("Chọn ngày làm việc", datetime.today(), key="adm_date")
            with col_t2:
                start_time = st.time_input("Giờ bắt đầu đón khách", datetime.now().time(), key="adm_time")
                
            if st.button("Xác Nhận Tạo Khung Giờ", type="primary", key="btn_create_slot"):
                start_dt = datetime.combine(date, start_time)
                end_dt = start_dt + timedelta(minutes=75)
                
                data = {
                    "start_time": start_dt.isoformat(),
                    "end_time": end_dt.isoformat(),
                    "status": "available"
                }
                if supabase:
                    supabase.table("slots").insert(data).execute()
                    st.success(f"✅ Đã tạo lịch trống thành công: {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')} ngày {date.strftime('%d/%m/%Y')}")
                else:
                    st.error("Chưa kết nối được cơ sở dữ liệu.")
        
        # ---- TAB 2: TẠO TÀI KHOẢN KHÁCH HÀNG ----
        with tab2:
            st.markdown("#### Tạo tài khoản mới cho khách hàng")
            st.caption("💡 Khách hàng phải được tạo tài khoản bằng Số điện thoại ở đây thì mới có thể tự đặt lịch ngoài giao diện.")
            with st.container(border=True):
                c_name = st.text_input("Họ và tên khách hàng:", key="adm_cust_name")
                c_phone = st.text_input("Số điện thoại khách (Nhập chính xác để kiểm tra):", key="adm_cust_phone")
                add_submit = st.button("Tạo tài khoản khách", type="primary", key="btn_save_cust")
                
                if add_submit:
                    if c_name and c_phone and supabase:
                        try:
                            phone_clean = c_phone.strip()
                            supabase.table("customers").insert({"full_name": c_name, "phone": phone_clean}).execute()
                            st.success(f"🎉 Đã tạo thành công tài khoản cho khách: **{c_name}** ({phone_clean})")
                        except Exception:
                            st.error("Số điện thoại này đã tồn tại trên hệ thống tài khoản!")
                    else:
                        st.error("Vui lòng nhập đầy đủ thông tin Tên và Số điện thoại khách.")
            
            st.write("---")
            st.markdown("#### Danh sách tài khoản khách hàng đã tạo")
            if supabase:
                cust_res = supabase.table("customers").select("*").order("full_name").execute()
                if cust_res.data:
                    for cust in cust_res.data:
                        st.write(f"• 👤 **{cust['full_name']}** - Số điện thoại đăng nhập: `{cust['phone']}`")
                else:
                    st.info("Chưa có tài khoản khách hàng nào được tạo.")

        # ---- TAB 3: XEM LỊCH HẸN VÀ LẤY TIN NHẮN ZALO MẪU ----
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
                            
                            # Giao diện nội bộ Admin hiện đủ khoảng thời gian từ mấy giờ tới mấy giờ
                            view_admin_time = f"{start_obj.strftime('%H:%M')} - {end_obj.strftime('%H:%M')} ngày {start_obj.strftime('%d/%m/%Y')}"
                            
                            # Tin nhắn gửi khách hàng CHỈ hiện giờ bắt đầu
                            zalo_msg_time = f"{start_obj.strftime('%H:%M')} ngày {start_obj.strftime('%d/%m/%Y')}"
                            
                            with st.container(border=True):
                                c1, c2, c3 = st.columns([2, 2, 1])
                                c1.markdown(f"👤 **Khách hàng:** {cust_info['full_name']} ({cust_info['phone']})")
                                c1.markdown(f"💆‍♂️ **Dịch vụ:** `{b['service_name']}`")
                                c2.markdown(f"🕒 **Thời gian:** {view_admin_time} *(75 phút)*")
                                
                                # Tạo tin nhắn mẫu gửi khách qua Zalo không kèm giờ kết thúc
                                msg = f"Chào {cust_info['full_name']}, Spa xác nhận lịch hẹn dịch vụ [{b['service_name']}] của bạn vào lúc {zalo_msg_time}. Hẹn gặp bạn nhé!"
                                zalo_url = f"https://zalo.me/{cust_info['phone']}"
                                
                                c3.markdown(f"[💬 Nhắc Zalo]({zalo_url})")
                                c3.caption("Bấm copy text mẫu:")
                                c3.code(msg, language="text")


# -------------------------------------------------------------------------
# PHẦN B: GIAO DIỆN KHÁCH HÀNG (XEM LỊCH THÁNG & ĐẶT LỊCH)
# -------------------------------------------------------------------------
else:
    # Import thư viện giao diện lịch tháng
    from streamlit_calendar import calendar

    st.subheader("✨ Đặt lịch hẹn Spa trực tuyến")
    
    if supabase:
        # Tải toàn bộ danh sách các slot giờ còn trống từ Supabase
        slot_res = supabase.table("slots").select("*").eq("status", "available").order("start_time").execute()
        available_slots = slot_res.data if slot_res.data else []
        
        if not available_slots:
            st.warning("Hiện tại Spa đã kín lịch hoặc chưa mở thêm khung giờ trống mới. Bạn vui lòng quay lại sau nhé!")
        else:
            st.info(f"Spa hiện cung cấp dịch vụ độc quyền: **{DUY_NHAT_SERVICE}** (Thời lượng cố định: 75 phút)")
            st.markdown("### 📅 Bước 1: Chọn một giờ trống trên lịch tháng")
            st.caption("💡 Hướng dẫn: Bấm trực tiếp vào ô **Chữ hiển thị Giờ màu xanh** trong ngày bạn muốn chọn trên bộ lịch.")

            # Chuyển đổi dữ liệu từ Supabase sang định dạng sự kiện của cấu phần Lịch (FullCalendar)
            calendar_events = []
            for slot in available_slots:
                start_obj = datetime.fromisoformat(slot["start_time"])
                calendar_events.append({
                    "id": str(slot["id"]),
                    "title": f"🕒 {start_obj.strftime('%H:%M')}", # Hiển thị mốc giờ bắt đầu lên ô lịch
                    "start": slot["start_time"],
                    "end": slot["end_time"],
                    "color": "#2e7d32", # Màu xanh lá cây trang nhã giống ảnh mẫu của bạn
                })

            # Cấu hình bộ lịch FullCalendar hiển thị bằng ngôn ngữ Việt Nam
            calendar_options = {
                "initialView": "dayGridMonth",
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": ""
                },
                "locale": "vi", # Chuyển thứ/ngày/tháng sang tiếng Việt
                "selectable": True,
            }

            # CSS tùy biến nhỏ cho chữ và số trên ô lịch to, rõ nét hơn
            custom_css = """
                .fc-event-title { font-weight: bold; font-size: 13px; cursor: pointer; }
                .fc-daygrid-day-number { color: #333; font-weight: bold; }
            """
            
            # Khởi tạo vẽ bộ lịch lên màn hình web
            state = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key="spa_calendar")

            st.write("---")
            st.markdown("### 📝 Bước 2: Xác nhận lịch hẹn và tài khoản")

            # Xử lý bắt sự kiện click chuột chọn giờ của Khách
            selected_slot = None
            if state.get("eventClick"):
                clicked_event_id = int(state["eventClick"]["event"]["id"])
                selected_slot = next((s for s in available_slots if s["id"] == clicked_event_id), None)

            # Nếu khách đã chọn một giờ cụ thể trên lịch
            if selected_slot:
                st_obj = datetime.fromisoformat(selected_slot["start_time"])
                en_obj = datetime.fromisoformat(selected_slot["end_time"])
                
                # Hiển thị thông báo khung giờ đang được chọn lên màn hình theo chuẩn Việt Nam
                st.success(f"🎯 Bạn đang chọn: Khung giờ **{st_obj.strftime('%H:%M')} - {en_obj.strftime('%H:%M')}** ngày **{st_obj.strftime('%d/%m/%Y')}**")
                
                # Khối nhập thông tin SĐT để kiểm tra tài khoản khách
                with st.container(border=True):
                    input_phone = st.text_input("Nhập Số điện thoại của bạn (đã được Spa đăng ký):", key="cust_phone_login")
                    btn_booking = st.button("Xác Nhận Đăng Ký Đặt Lịch", type="primary", key="btn_confirm_booking")
                    
                    if btn_booking:
                        if not input_phone.strip():
                            st.error("Vui lòng nhập Số điện thoại để hệ thống xác nhận tài khoản!")
                        else:
                            # Tìm kiếm xem số điện thoại khách điền có trong DB do Admin tạo không
                            check_cust = supabase.table("customers").select("*").eq("phone", input_phone.strip()).execute()
                            
                            if not check_cust.data:
                                st.error("❌ Số điện thoại này chưa được đăng ký tài khoản tại Spa! Vui lòng liên hệ chủ Spa để kích hoạt số tài khoản trước.")
                            else:
                                info_khach = check_cust.data[0]
                                chosen_cust_id = info_khach["id"]
                                ten_khach = info_khach["full_name"]
                                
                                # 1. Thêm bản ghi đặt lịch mới vào bảng bookings
                                booking_data = {
                                    "slot_id": selected_slot["id"],
                                    "customer_id": chosen_cust_id,
                                    "service_name": DUY_NHAT_SERVICE
                                }
                                supabase.table("bookings").insert(booking_data).execute()
                                
                                # 2. Chuyển trạng thái slot giờ vừa book sang 'booked' để ẩn đi
                                supabase.table("slots").update({"status": "booked"}).eq("id", selected_slot["id"]).execute()
                                
                                # Bắn hiệu ứng pháo hoa bóng bay chúc mừng thành công
                                st.balloons()
                                st.success(f"🎉 Xin chúc mừng {ten_khach}! Bạn đã đặt lịch hẹn thành công gói dịch vụ [{DUY_NHAT_SERVICE}].")
                                
                                # 3. Tạo link tích hợp nhanh lịch Google Calendar cho khách hàng
                                s_time = st_obj.strftime("%Y%m%dT%H%M%S")
                                e_time = en_obj.strftime("%Y%m%dT%H%M%S")
                                cal_title = urllib.parse.quote(f"Lịch Hẹn Spa - {DUY_NHAT_SERVICE}")
                                cal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={cal_title}&dates={s_time}/{e_time}&details=Hẹn+gặp+bạn+tại+Private+Spa!"
                                
                                st.markdown(f"[📅 Nhấp vào đây để tự thêm lịch hẹn này vào Google Calendar cá nhân của bạn]({cal_url})")
            else:
                st.warning("👈 Vui lòng dùng chuột/ngón tay bấm chọn trực tiếp vào một ô **Chữ hiển thị Mốc Giờ màu xanh** trên bảng lịch tháng ở trên để tiến hành đặt chỗ.")
    else:
        st.error("Không thể tải thông tin do lỗi kết nối API Supabase.")