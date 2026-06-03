import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
import urllib.parse

# 1. CẤU HÌNH SUPABASE (Hãy thay bằng thông tin chính xác dự án của bạn)
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

# Khởi tạo các trạng thái bộ nhớ hệ thống (Session State)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_role" not in st.session_state:
    st.session_state.current_role = "Khách Hàng"

# Định nghĩa gói dịch vụ duy nhất của Spa
DUY_NHAT_SERVICE = "Chăm sóc da mặt chuyên sâu"

# --- THANH MENU ĐIỀU HƯỚNG TRÊN CÙNG ---
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
# PHẦN 1: GIAO DIỆN CHỦ SPA (ADMIN)
# -------------------------------------------------------------------------
if st.session_state.current_role == "Chủ Spa (Admin)":
    
    # 1.1 Trường hợp CHƯA ĐĂNG NHẬP
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
                    
    # 1.2 Trường hợp ĐÃ ĐĂNG NHẬP THÀNH CÔNG
    else:
        st.subheader("⚙️ Khu vực quản trị của Chủ Spa")
        if st.button("🚪 Đăng xuất khỏi Admin"):
            st.session_state.logged_in = False
            st.rerun()
            
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

        # ---- TAB 3: XEM LỊCH HẸN & NHẮC ZALO ----
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
                            
                            # Giao diện quản lý của Admin vẫn hiện đủ Khoảng thời gian để tiện theo dõi điều phối giường
                            view_admin_time = f"{start_obj.strftime('%H:%M')} - {end_obj.strftime('%H:%M')} ngày {start_obj.strftime('%d/%m/%Y')}"
                            
                            # CHỈ LẤY GIỜ BẮT ĐẦU cho tin nhắn gửi khách hàng
                            zalo_msg_time = f"{start_obj.strftime('%H:%M')} ngày {start_obj.strftime('%d/%m/%Y')}"
                            
                            with st.container(border=True):
                                c1, c2, c3 = st.columns([2, 2, 1])
                                c1.markdown(f"👤 **Khách hàng:** {cust_info['full_name']} ({cust_info['phone']})")
                                c1.markdown(f"💆‍♂️ **Dịch vụ:** `{b['service_name']}`")
                                c2.markdown(f"🕒 **Thời gian:** {view_admin_time} *(75 phút)*")
                                
                                # Tạo tin nhắn mẫu CHỈ có giờ bắt đầu
                                msg = f"Chào {cust_info['full_name']}, Spa xác nhận lịch hẹn dịch vụ [{b['service_name']}] của bạn vào lúc {zalo_msg_time}. Hẹn gặp bạn nhé!"
                                zalo_url = f"https://zalo.me/{cust_info['phone']}"
                                
                                c3.markdown(f"[💬 Nhắc Zalo]({zalo_url})")
                                c3.caption("Bấm copy text mẫu:")
                                c3.code(msg, language="text")

# -------------------------------------------------------------------------
# PHẦN 2: GIAO DIỆN KHÁCH HÀNG (ĐẶT LỊCH)
# -------------------------------------------------------------------------
else:
    st.subheader("✨ Đặt lịch hẹn Spa trực tuyến")
    
    if supabase:
        slot_res = supabase.table("slots").select("*").eq("status", "available").order("start_time").execute()
        available_slots = slot_res.data if slot_res.data else []
        
        if not available_slots:
            st.warning("Hiện tại Spa đã kín lịch hoặc chưa mở thêm khung giờ trống mới. Bạn vui lòng quay lại sau nhé!")
        else:
            st.info(f"Spa hiện cung cấp dịch vụ độc quyền: **{DUY_NHAT_SERVICE}** (Thời lượng cố định: 75 phút)")
            
            slot_options = {}
            for slot in available_slots:
                start_obj = datetime.fromisoformat(slot["start_time"])
                end_obj = datetime.fromisoformat(slot["end_time"])
                slot_options[slot["id"]] = f"📅 Khung giờ: {start_obj.strftime('%H:%M')} - {end_obj.strftime('%H:%M')} ngày {start_obj.strftime('%d/%m/%Y')}"
                
            chosen_slot_id = st.radio(
                "1. Chọn khung giờ bạn muốn đặt lịch:", 
                list(slot_options.keys()), 
                format_func=lambda x: slot_options[x],
                key="cust_radio_slot"
            )
            
            st.write("---")
            st.markdown("#### 2. Xác thực thông tin tài khoản của bạn")
            
            with st.container(border=True):
                input_phone = st.text_input("Nhập Số điện thoại của bạn (đã được Spa kích hoạt):", key="cust_phone_login")
                btn_booking = st.button("Xác Nhận Đăng Ký Đặt Lịch", type="primary", key="btn_confirm_booking")
                
                if btn_booking:
                    if not input_phone.strip():
                        st.error("Vui lòng nhập Số điện thoại để hệ thống xác nhận tài khoản!")
                    else:
                        check_cust = supabase.table("customers").select("*").eq("phone", input_phone.strip()).execute()
                        
                        if not check_cust.data:
                            st.error("❌ Số điện thoại này chưa được đăng ký tài khoản tại Spa! Vui lòng liên hệ chủ Spa để tạo tài khoản trước khi book lịch.")
                        else:
                            info_khach = check_cust.data[0]
                            chosen_cust_id = info_khach["id"]
                            ten_khach = info_khach["full_name"]
                            
                            booking_data = {
                                "slot_id": chosen_slot_id,
                                "customer_id": chosen_cust_id,
                                "service_name": DUY_NHAT_SERVICE
                            }
                            supabase.table("bookings").insert(booking_data).execute()
                            
                            supabase.table("slots").update({"status": "booked"}).eq("id", chosen_slot_id).execute()
                            
                            st.success(f"🎉 Xin chúc mừng {ten_khach}! Bạn đã đặt lịch hẹn thành công gói [{DUY_NHAT_SERVICE}].")
                            
                            slot_details = next(s for s in available_slots if s["id"] == chosen_slot_id)
                            s_time = datetime.fromisoformat(slot_details["start_time"]).strftime("%Y%m%dT%H%M%S")
                            e_time = datetime.fromisoformat(slot_details["end_time"]).strftime("%Y%m%dT%H%M%S")
                            
                            cal_title = urllib.parse.quote(f"Lịch Hẹn Spa - {DUY_NHAT_SERVICE}")
                            cal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={cal_title}&dates={s_time}/{e_time}&details=Hẹn+gặp+bạn+tại+Private+Spa!"
                            
                            st.markdown(f"[📅 Nhấp vào đây để thêm lịch hẹn này vào Google Calendar cá nhân của bạn]({cal_url})")
    else:
        st.error("Không thể tải thông tin do lỗi kết nối API Supabase.")