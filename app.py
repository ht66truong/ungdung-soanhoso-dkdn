import streamlit as st
from docxtpl import DocxTemplate
import os
import datetime
import json

def remove_accents(text):
    if not text: return text
    accents = {
        'a': 'àáạảãâầấậẩẫăằắặẳẵ', 'A': 'ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ',
        'e': 'èéẹẻẽêềếệểễ', 'E': 'ÈÉẸẺẼÊỀẾỆỂỄ',
        'i': 'ìíịỉĩ', 'I': 'ÌÍỊỈĨ',
        'o': 'òóọỏõôồốộổỗơờớợởỡ', 'O': 'ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ',
        'u': 'ùúụủũưừứựửữ', 'U': 'ÙÚỤỦŨƯỪỨỰỬỮ',
        'y': 'ỳýỵỷỹ', 'Y': 'ỲÝỴỶỸ',
        'd': 'đ', 'D': 'Đ'
    }
    for char, accented_chars in accents.items():
        for acc in accented_chars:
            text = text.replace(acc, char)
    return text

# --- HÀM XỬ LÝ SỐ VỚI DẤU CHẤM NGHÌN ---
def parse_number_with_dots(s):
    """Chuyển đổi chuỗi số có dấu chấm nghìn thành float"""
    if not s or str(s).strip() == "": return 0.0
    s = str(s).replace('.', '')  # Loại bỏ dấu chấm nghìn
    try:
        return float(s)
    except ValueError:
        return 0.0

def format_number_with_dots(n):
    """Định dạng số thành chuỗi có dấu chấm nghìn"""
    if not n or n == 0: return ""
    try:
        # Định dạng với dấu phẩy, sau đó thay bằng dấu chấm
        return f"{float(n):,.0f}".replace(',', '.')
    except:
        return str(n)

def format_percent(value):
    """Định dạng phần trăm với 3 chữ số thập phân và dấu phẩy"""
    try:
        return f"{float(value):.3f}".replace('.', ',')
    except:
        return str(value)

# --- HÀM LƯU & TẢI DỮ LIỆU ---
CACHE_FILE = "cache_data.json"

def save_cache(data):
    """Lưu dữ liệu vào file JSON"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def load_cache():
    """Tải dữ liệu từ file JSON"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return None

def clear_cache():
    """Xóa cache"""
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
    except:
        pass

# --- HÀM QUẢN LÝ HỒ SƠ KHÁCH HÀNG ---
PROFILES_DIR = "customer_profiles"

def ensure_profiles_dir():
    """Tạo thư mục profiles nếu chưa tồn tại"""
    if not os.path.exists(PROFILES_DIR):
        os.makedirs(PROFILES_DIR)

def save_customer_profile(company_name, data):
    """Lưu profile khách hàng vào file JSON - deep merge với dữ liệu hiện có"""
    try:
        ensure_profiles_dir()
        clean_name = remove_accents(company_name.strip())
        file_path = os.path.join(PROFILES_DIR, f"{clean_name}.json")
        
        # Load profile hiện có nếu có
        existing_profile = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_profile = json.load(f)
            except:
                existing_profile = {}
        
        # Deep merge dữ liệu: giữ dữ liệu cũ, update với dữ liệu mới
        merged_profile = existing_profile.copy()
        
        # Merge context_cache (giữ các field cũ không có trong dữ liệu mới)
        if 'context_cache' in data:
            if 'context_cache' not in merged_profile:
                merged_profile['context_cache'] = {}
            existing_context = merged_profile['context_cache'].copy()
            existing_context.update(data['context_cache'])  # Update với dữ liệu mới
            merged_profile['context_cache'] = existing_context
        
        # Merge ds_thanhvien và ds_huongloi (nếu có dữ liệu mới, sử dụng dữ liệu mới; nếu không, giữ dữ liệu cũ)
        if 'ds_thanhvien' in data and data['ds_thanhvien']:
            merged_profile['ds_thanhvien'] = data['ds_thanhvien']
        elif 'ds_thanhvien' not in merged_profile:
            merged_profile['ds_thanhvien'] = data.get('ds_thanhvien', [])
        
        if 'ds_huongloi' in data and data['ds_huongloi']:
            merged_profile['ds_huongloi'] = data['ds_huongloi']
        elif 'ds_huongloi' not in merged_profile:
            merged_profile['ds_huongloi'] = data.get('ds_huongloi', [])

        if 'is_same' in data:
            merged_profile['is_same'] = data['is_same']
        elif 'is_same' not in merged_profile:
            merged_profile['is_same'] = False
        
        # Ghi file với dữ liệu đã merge
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(merged_profile, f, ensure_ascii=False, indent=2)
        return True, f"✅ Đã lưu profile: {clean_name}"
    except Exception as e:
        return False, f"❌ Lỗi lưu profile: {str(e)}"

def load_customer_profile(company_name):
    """Tải profile khách hàng từ file JSON"""
    try:
        clean_name = remove_accents(company_name.strip())
        file_path = os.path.join(PROFILES_DIR, f"{clean_name}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return None

def get_customer_list():
    """Lấy danh sách khách hàng đã lưu"""
    try:
        ensure_profiles_dir()
        files = [f.replace('.json', '') for f in os.listdir(PROFILES_DIR) if f.endswith('.json')]
        return sorted(files)
    except:
        return []

def delete_customer_profile(company_name):
    """Xóa profile khách hàng"""
    try:
        clean_name = remove_accents(company_name.strip())
        file_path = os.path.join(PROFILES_DIR, f"{clean_name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True, f"✅ Đã xóa profile: {clean_name}"
    except Exception as e:
        return False, f"❌ Lỗi xóa profile: {str(e)}"

st.set_page_config(page_title="SME - Hệ thống Soạn Hồ sơ ĐKDN", layout="wide")

TEMPLATE_DIR = "templates"
OUTPUT_DIR = "output_nas"

# --- 1. KHỞI TẠO STATE (KHÔI PHỤC ĐẦY ĐỦ TRƯỜNG THÀNH VIÊN) ---
cache_data = load_cache()

if 'ds_thanhvien' not in st.session_state:
    if cache_data and 'ds_thanhvien' in cache_data:
        st.session_state.ds_thanhvien = cache_data['ds_thanhvien']
        # Chuyển đổi vongop từ string sang float nếu cần
        for m in st.session_state.ds_thanhvien:
            if 'vongop' in m and isinstance(m['vongop'], str):
                m['vongop'] = parse_number_with_dots(m['vongop'])
    else:
        st.session_state.ds_thanhvien = [{
            'hoten': '', 'ngaysinh': '', 'gioitinh': '', 'cccd': '', 
            'quoctich': '', 'dantoc': '', 'diachi': '', 
            'vongop': 0.0, 'thoihan': '90 ngày kể từ ngày cấp GCNĐKDN', 'taisan': 'Đồng Việt Nam', 'tyle': ''
        }]

if 'ds_huongloi' not in st.session_state:
    if cache_data and 'ds_huongloi' in cache_data:
        st.session_state.ds_huongloi = cache_data['ds_huongloi']
    else:
        st.session_state.ds_huongloi = [{
            'hoten': '', 'ngaysinh': '', 'gioitinh': '', 'cccd': '', 
            'quoctich': '', 'dantoc': '', 'diachi': '', 
            'tyle_vdl': '', 'tyle_bieuquyet': '', 
            'quyen_chiphoi': '- Bổ nhiệm, miễn nhiệm hoặc bãi nhiệm đa số hoặc tất cả thành viên hội đồng quản trị, giám đốc hoặc tổng giám đốc của doanh nghiệp\n- Sửa đổi, bổ sung điều lệ của doanh nghiệp\n- Thay đổi cơ cấu tổ chức quản lý công ty\n- Tổ chức lại, giải thể công ty'
        }]

if 'context_cache' not in st.session_state:
    if cache_data and 'context_cache' in cache_data:
        st.session_state.context_cache = cache_data['context_cache']
    else:
        st.session_state.context_cache = {}

# --- 2. THỨ TỰ ƯU TIÊN (ĐDPL TRƯỚC CSH) ---
ORDER_LIST = [
    "dn_tencongty", "dn_tencongty_tienganh", "dn_tencongty_viettat", "dn_masodoanhnghiep",
    "dn_truso_sonha", "dn_truso_phuong", "dn_truso_tinh",
    "dn_vondieule_so", "dn_vondieule_bangchu", "dn_sdt", "dn_email",
    "ddpl_hoten", "ddpl_ngaysinh", "ddpl_gioitinh", "ddpl_sodinhdanh", "ddpl_diachi", "ddpl_chucdanh",
    "csh_hoten", "csh_ngaysinh", "csh_gioitinh", "csh_sodinhdanh", "csh_diachi"
]

# 2. VIỆT HÓA NHÃN HIỂN THỊ
MAP_LABELS = {
    "dn_tencongty": "Tên công ty (Tiếng Việt)",
    "dn_tencongty_tienganh": "Tên công ty (Tiếng Anh)",
    "dn_tencongty_viettat": "Tên công ty (Viết tắt)",
    "dn_masodoanhnghiep": "Mã số doanh nghiệp",
    "dn_truso_sonha": "Địa chỉ trụ sở (Số nhà, tên đường)",
    "dn_truso_phuong": "Địa chỉ trụ sở (Phường/Xã)",
    "dn_truso_tinh": "Địa chỉ trụ sở (Tỉnh/Thành phố)",
    "dn_vondieule_so": "Vốn điều lệ (Số)",
    "dn_vondieule_bangchu": "Vốn điều lệ (Bằng chữ)",
    "dn_sdt": "Số điện thoại công ty",
    "dn_email": "Email công ty",
    "ddpl_hoten": "Họ tên - ĐDPL",
    "ddpl_ngaysinh": "Ngày sinh - ĐDPL",
    "ddpl_sodinhdanh": "Số định danh/CCCD - ĐDPL",
    "ddpl_diachi": "Địa chỉ liên lạc - ĐDPL",
    "ddpl_chucdanh": "Chức danh - ĐDPL (Giám đốc, Tổng giám đốc)",
    "csh_hoten": "Họ tên - CSH",
    "csh_ngaysinh": "Ngày sinh - CSH",
    "csh_sodinhdanh": "Số định danh/CCCD - CSH",
    "csh_diachi": "Địa chỉ liên lạc - CSH"
}

st.title("⚖️ HỆ THỐNG SOẠN HỒ SƠ ĐĂNG KÝ DOANH NGHIỆP")

def get_clean_vars(selected_path, files):
    all_v = set()
    for f in files:
        try:
            doc = DocxTemplate(os.path.join(selected_path, f))
            all_v.update(doc.get_undeclared_template_variables())
        except: pass
    return sorted(list(all_v), key=lambda x: ORDER_LIST.index(x) if x in ORDER_LIST else 999)

# --- 3. SIDEBAR ---
if not os.path.exists(TEMPLATE_DIR): os.makedirs(TEMPLATE_DIR)
subfolders = [f for f in os.listdir(TEMPLATE_DIR) if os.path.isdir(os.path.join(TEMPLATE_DIR, f))]
folder_choice = st.sidebar.selectbox("Chọn loại hồ sơ:", ["Mặc định"] + subfolders)
selected_path = TEMPLATE_DIR if folder_choice == "Mặc định" else os.path.join(TEMPLATE_DIR, folder_choice)
templates = [f for f in os.listdir(selected_path) if f.endswith('.docx')]

# Khi thay đổi loại hồ sơ, mặc định chọn tất cả file mẫu
if 'previous_folder' not in st.session_state:
    st.session_state.previous_folder = folder_choice

if folder_choice != st.session_state.previous_folder:
    st.session_state.selected_files = templates
    st.session_state.previous_folder = folder_choice

# Reset widgets nếu cần
if st.session_state.get('reset_all', False):
    if 'selected_files' in st.session_state:
        del st.session_state.selected_files
    st.session_state.input_company_name = ""
    st.session_state.customer_select = ""
    st.session_state.is_same = False
    st.session_state.reset_all = False
elif st.session_state.get('reset_customer', False):
    st.session_state.customer_select = ""
    st.session_state.input_company_name = ""
    st.session_state.is_same = False
    st.session_state.reset_customer = False

selected_files = st.sidebar.multiselect("Chọn file mẫu:", templates, default=st.session_state.get('selected_files', templates), key="selected_files")

# --- QUẢN LÝ PROFILE KHÁCH HÀNG ---
st.sidebar.divider()
st.sidebar.subheader("📋 Quản lý hồ sơ khách hàng")

customer_list = get_customer_list()
if customer_list:
    col_select, col_delete = st.sidebar.columns([3, 1])
    with col_select:
        selected_customer = st.selectbox("Chọn khách hàng:", [""] + customer_list, key="customer_select")
    with col_delete:
        if st.button("🗑️ Xóa", key="btn_delete_profile"):
            if selected_customer:
                success, msg = delete_customer_profile(selected_customer)
                st.sidebar.success(msg) if success else st.sidebar.error(msg)
                st.rerun()
            else:
                st.sidebar.warning("Chọn khách hàng để xóa")
    
    # Tự động load profile khi chọn khách hàng
    if 'previous_customer' not in st.session_state:
        st.session_state.previous_customer = ""
    
    if selected_customer and selected_customer != st.session_state.previous_customer:
        profile = load_customer_profile(selected_customer)
        if profile:
            # Cập nhật state TRƯỚC st.rerun()
            st.session_state.context_cache = profile.get('context_cache', {})
            st.session_state.ds_thanhvien = profile.get('ds_thanhvien', st.session_state.ds_thanhvien)
            st.session_state.ds_huongloi = profile.get('ds_huongloi', st.session_state.ds_huongloi)
            st.session_state.is_same = profile.get('is_same', False)
            # Chuyển đổi vongop từ string sang float nếu cần
            for m in st.session_state.ds_thanhvien:
                if 'vongop' in m and isinstance(m['vongop'], str):
                    m['vongop'] = parse_number_with_dots(m['vongop'])
            st.session_state.refresh_key = st.session_state.get('refresh_key', 0) + 1  # Force refresh input fields
            st.session_state.profile_loaded = True  # Flag để tracking
            st.session_state.previous_customer = selected_customer  # SET TRƯỚC st.rerun()
            st.rerun()
        else:
            st.session_state.previous_customer = selected_customer
    elif not selected_customer:
        st.session_state.previous_customer = ""
    
    # Hiển thị thông báo nếu profile vừa được load
    if st.session_state.get('profile_loaded', False):
        st.toast(f"✅ Đã tải tự động: {selected_customer}", icon="✅")
        st.session_state.profile_loaded = False
    
    # --- LƯU PROFILE KHÁCH HÀNG ---
    st.sidebar.divider()
    with st.sidebar.expander("💼 Lưu Profile Khách Hàng", expanded=False):
        # Tự động lấy tên công ty làm tên profile từ context_cache
        auto_name = st.session_state.context_cache.get('dn_tencongty', '').strip()
        
        # Nếu profile name chưa có, dùng tên công ty để tự động điền
        if auto_name and not st.session_state.get('input_company_name'):
            st.session_state.input_company_name = auto_name
        
        col_company, col_save_profile = st.columns([2, 1])
        with col_company:
            company_name = st.text_input(
                "Tên profile (mặc định lấy từ Tên công ty):",
                value=st.session_state.get('input_company_name', auto_name),
                help="Chỉnh sửa nếu cần; nếu chưa có tên công ty thì nhập tên profile để lưu",
                key="input_company_name"
            )
        with col_save_profile:
            if st.button("💾 Lưu", use_container_width=True):
                if company_name:
                    profile_data = {
                        'context_cache': st.session_state.context_cache,
                        'ds_thanhvien': st.session_state.ds_thanhvien,
                        'ds_huongloi': st.session_state.ds_huongloi,
                        'is_same': st.session_state.get('is_same', False)
                    }
                    success, msg = save_customer_profile(company_name, profile_data)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("⚠️ Vui lòng nhập tên công ty trước (tab: Thông tin doanh nghiệp) hoặc đặt tên profile để lưu")
else:
    st.sidebar.info("📌 Chưa có profile khách hàng nào. Hãy lưu profile mới.")

# --- 4. GIAO DIỆN NHẬP LIỆU ---
if selected_files:
    vars_found = get_clean_vars(selected_path, selected_files)
    context = {}

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏢 THÔNG TIN DOANH NGHIỆP", "👤 ĐẠI DIỆN PHÁP LUẬT/CSH", "👥 THÔNG TIN THÀNH VIÊN", "🌟 CSH HƯỞNG LỢI", "📑 KHÁC"])

    with tab1:
        biz_vars = [v for v in vars_found if v.startswith('dn_')]
        for i in range(0, len(biz_vars), 2):
            row = biz_vars[i:i+2]
            col1, col2 = st.columns(2)
    
            with col1:
                v = row[0]
                label = MAP_LABELS.get(v, v.replace('dn_', '').replace('_', ' ').upper())
                context[v] = st.text_input(label, value=st.session_state.context_cache.get(v, ''), key=f"in_{v}_{st.session_state.get('refresh_key', 0)}")
    
            if len(row) > 1:
                with col2:
                    v = row[1]
                    label = MAP_LABELS.get(v, v.replace('dn_', '').replace('_', ' ').upper())
                    context[v] = st.text_input(label, value=st.session_state.context_cache.get(v, ''), key=f"in_{v}_{st.session_state.get('refresh_key', 0)}")
    with tab2:
        ddpl_vars = [v for v in vars_found if v.startswith('ddpl_')]
        csh_vars = [v for v in vars_found if v.startswith('csh_')]
    
        st.subheader("I. Người đại diện pháp luật (ĐDPL)")
        for i in range(0, len(ddpl_vars), 2):
            row = ddpl_vars[i:i+2]
            d1, d2 = st.columns(2)
            with d1:
                v = row[0]
                if 'gioitinh' in v:
                    cached_val = st.session_state.context_cache.get(v, "")
                    options = ["", "Nam", "Nữ"]
                    idx = 0
                    if cached_val == "Nam":
                        idx = 1
                    elif cached_val == "Nữ":
                        idx = 2
                    context[v] = st.selectbox("Giới tính - ĐDPL", options, index=idx,
                                              format_func=lambda x: "Chọn..." if x == "" else x,
                                              key=f"in_{v}_{st.session_state.get('refresh_key', 0)}")
                else:
                    label = MAP_LABELS.get(v, f"ĐDPL - {v.replace('ddpl_', '').replace('_', ' ').upper()}")
                    context[v] = st.text_input(label, value=st.session_state.context_cache.get(v, ''),
                                              key=f"in_{v}_{st.session_state.get('refresh_key', 0)}")
            if len(row) > 1:
                with d2:
                    v = row[1]
                    if 'gioitinh' in v:
                        cached_val = st.session_state.context_cache.get(v, "")
                        options = ["", "Nam", "Nữ"]
                        idx = 0
                        if cached_val == "Nam":
                            idx = 1
                        elif cached_val == "Nữ":
                            idx = 2
                        context[v] = st.selectbox("Giới tính - ĐDPL", options, index=idx,
                                                  format_func=lambda x: "Chọn..." if x == "" else x,
                                                  key=f"in_{v}_{st.session_state.get('refresh_key', 0)}")
                    else:
                        label = MAP_LABELS.get(v, f"ĐDPL - {v.replace('ddpl_', '').replace('_', ' ').upper()}")
                        context[v] = st.text_input(label, value=st.session_state.context_cache.get(v, ''),
                                                  key=f"in_{v}_{st.session_state.get('refresh_key', 0)}")
    
        if csh_vars:
            st.divider()
            st.subheader("II. Chủ sở hữu (CSH)")
            is_same = st.checkbox("🔄 Người đại diện pháp luật là Chủ Sở Hữu (Đồng bộ dữ liệu)", value=st.session_state.get('is_same', False), key="is_same")
            if not is_same:
                for i in range(0, len(csh_vars), 2):
                    row = csh_vars[i:i+2]
                    c1, c2 = st.columns(2)
                    with c1:
                        v = row[0]
                        if 'gioitinh' in v:
                            cached_val = st.session_state.context_cache.get(v, "")
                            options = ["", "Nam", "Nữ"]
                            idx = 0
                            if cached_val == "Nam":
                                idx = 1
                            elif cached_val == "Nữ":
                                idx = 2
                            context[v] = st.selectbox("Giới tính - CSH", options, index=idx,
                                                      format_func=lambda x: "Chọn..." if x == "" else x,
                                                      key=f"in_{v}_{st.session_state.get('refresh_key', 0)}")
                        else:
                            label = MAP_LABELS.get(v, f"CSH - {v.replace('csh_', '').replace('_', ' ').upper()}")
                            context[v] = st.text_input(label, value=st.session_state.context_cache.get(v, ''),
                                                      key=f"in_{v}_{st.session_state.get('refresh_key', 0)}")
                    if len(row) > 1:
                        with c2:
                            v = row[1]
                            if 'gioitinh' in v:
                                cached_val = st.session_state.context_cache.get(v, "")
                                options = ["", "Nam", "Nữ"]
                                idx = 0
                                if cached_val == "Nam":
                                    idx = 1
                                elif cached_val == "Nữ":
                                    idx = 2
                                context[v] = st.selectbox("Giới tính - CSH", options, index=idx,
                                                          format_func=lambda x: "Chọn..." if x == "" else x,
                                                          key=f"in_{v}_{st.session_state.get('refresh_key', 0)}")
                            else:
                                label = MAP_LABELS.get(v, f"CSH - {v.replace('csh_', '').replace('_', ' ').upper()}")
                                context[v] = st.text_input(label, value=st.session_state.context_cache.get(v, ''),
                                                          key=f"in_{v}_{st.session_state.get('refresh_key', 0)}")
            else:
                for v in csh_vars:
                    source = v.replace('csh_', 'ddpl_')
                    context[v] = context.get(source, st.session_state.context_cache.get(v, ""))
    with tab3:
        st.subheader("Danh sách Thành viên (Mẫu số 6)")
        for i, m in enumerate(st.session_state.ds_thanhvien):
            with st.expander(f"Thành viên {i+1}: {m['hoten']}", expanded=True):
                r1, r2, r3 = st.columns(3)
                m['hoten'] = r1.text_input("Họ tên", value=m['hoten'], key=f"tv_h_{i}_{st.session_state.get('refresh_key', 0)}")
                m['ngaysinh'] = r2.text_input("Ngày sinh", value=m['ngaysinh'], key=f"tv_n_{i}_{st.session_state.get('refresh_key', 0)}")
                options_gt = ["", "Nam", "Nữ"]
                idx_gt = 0
                if m['gioitinh'] == "Nam":
                    idx_gt = 1
                elif m['gioitinh'] == "Nữ":
                    idx_gt = 2
                m['gioitinh'] = r3.selectbox("Giới tính", options_gt, index=idx_gt, format_func=lambda x: "Chọn..." if x == "" else x, key=f"tv_g_{i}_{st.session_state.get('refresh_key', 0)}")
                
                r4, r5, r6 = st.columns(3)
                m['cccd'] = r4.text_input("Số định danh/CCCD", value=m['cccd'], key=f"tv_c_{i}_{st.session_state.get('refresh_key', 0)}")
                m['quoctich'] = r5.text_input("Quốc tịch", value=m['quoctich'], key=f"tv_q_{i}_{st.session_state.get('refresh_key', 0)}")
                m['dantoc'] = r6.text_input("Dân tộc", value=m['dantoc'], key=f"tv_d_{i}_{st.session_state.get('refresh_key', 0)}")
                
                m['diachi'] = st.text_input("Địa chỉ liên lạc", value=m['diachi'], key=f"tv_a_{i}_{st.session_state.get('refresh_key', 0)}")
                
                r7, r8, r9 = st.columns(3)
                # Dùng text_input để tránh số 0 mặc định
                m['vongop'] = parse_number_with_dots(r7.text_input("Vốn góp (VNĐ)", value=format_number_with_dots(m['vongop']), key=f"tv_v_{i}_{st.session_state.get('refresh_key', 0)}"))
                m['thoihan'] = r8.text_input("Thời hạn góp", value=m['thoihan'], key=f"tv_t_{i}_{st.session_state.get('refresh_key', 0)}")
                m['taisan'] = r9.text_input("Tài sản góp", value=m['taisan'], key=f"tv_ts_{i}_{st.session_state.get('refresh_key', 0)}")
                
                if st.button("🗑️ Xóa thành viên", key=f"tv_del_{i}_{st.session_state.get('refresh_key', 0)}"):
                    st.session_state.ds_thanhvien.pop(i)
                    st.rerun()
        if st.button("➕ Thêm Thành viên", key=f"tv_add_{st.session_state.get('refresh_key', 0)}"):
            st.session_state.ds_thanhvien.append({'hoten': '', 'ngaysinh': '', 'gioitinh': '', 'cccd': '', 'quoctich': '', 'dantoc': '', 'diachi': '', 'vongop': 0.0, 'thoihan': '90 ngày kể từ ngày cấp GCNĐKDN', 'taisan': 'Đồng Việt Nam', 'tyle': ''})
            st.rerun()

    with tab4:
        st.subheader("Danh sách CSH Hưởng lợi (Mẫu số 10)")
        for i, h in enumerate(st.session_state.ds_huongloi):
            with st.expander(f"CSHHL {i+1}: {h['hoten']}", expanded=True):
                h1, h2, h3 = st.columns(3)
                h['hoten'] = h1.text_input("Họ tên", value=h['hoten'], key=f"hl_h_{i}_{st.session_state.get('refresh_key', 0)}")
                h['ngaysinh'] = h2.text_input("Ngày sinh", value=h['ngaysinh'], key=f"hl_n_{i}_{st.session_state.get('refresh_key', 0)}")
                options_gt = ["", "Nam", "Nữ"]
                idx_gt = 0
                if h['gioitinh'] == "Nam":
                    idx_gt = 1
                elif h['gioitinh'] == "Nữ":
                    idx_gt = 2
                h['gioitinh'] = h3.selectbox("Giới tính ", options_gt, index=idx_gt, format_func=lambda x: "Chọn..." if x == "" else x, key=f"hl_g_{i}_{st.session_state.get('refresh_key', 0)}")
                
                h4, h5, h6 = st.columns(3)
                h['cccd'] = h4.text_input("Số định danh/CCCD ", value=h['cccd'], key=f"hl_c_{i}_{st.session_state.get('refresh_key', 0)}")
                h['quoctich'] = h5.text_input("Quốc tịch ", value=h['quoctich'], key=f"hl_q_{i}_{st.session_state.get('refresh_key', 0)}")
                h['dantoc'] = h6.text_input("Dân tộc ", value=h['dantoc'], key=f"hl_d_{i}_{st.session_state.get('refresh_key', 0)}")
                
                h['diachi'] = st.text_input("Địa chỉ liên lạc ", value=h['diachi'], key=f"hl_a_{i}_{st.session_state.get('refresh_key', 0)}")
                
                ha, hb = st.columns(2)
                # FIX LỖI SỐ 0: Chuyển sang text_input
                h['tyle_vdl'] = ha.text_input("Tỷ lệ sở hữu VDL (%)", value=str(h['tyle_vdl']), key=f"hl_v_{i}_{st.session_state.get('refresh_key', 0)}")
                h['tyle_bieuquyet'] = hb.text_input("Tỷ lệ biểu quyết (%)", value=str(h['tyle_bieuquyet']), key=f"hl_b_{i}_{st.session_state.get('refresh_key', 0)}")
                
                h['quyen_chiphoi'] = st.text_area("Quyền chi phối chi tiết ", value=h['quyen_chiphoi'], key=f"hl_qc_{i}_{st.session_state.get('refresh_key', 0)}")
                
                if st.button("🗑️ Xóa CSHHL", key=f"hl_del_{i}_{st.session_state.get('refresh_key', 0)}"):
                    st.session_state.ds_huongloi.pop(i)
                    st.rerun()
        if st.button("➕ Thêm CSHHL", key=f"hl_add_{st.session_state.get('refresh_key', 0)}"):
            st.session_state.ds_huongloi.append({'hoten': '', 'ngaysinh': '', 'gioitinh': '', 'cccd': '', 'quoctich': '', 'dantoc': '', 'diachi': '', 'tyle_vdl': '', 'tyle_bieuquyet': '', 'quyen_chiphoi': ''})
            st.rerun()

    with tab5:
        other_vars = [v for v in vars_found if not v.startswith(('dn_', 'csh_', 'ddpl_'))]
        for i in range(0, len(other_vars), 2):
            row = other_vars[i:i+2]
            o1, o2 = st.columns(2)
            with o1:
                v = row[0]
                label = MAP_LABELS.get(v, v.replace('_', ' ').upper())
                context[v] = st.text_input(label, value=st.session_state.context_cache.get(v, ''),
                                          key=f"in_{v}_{st.session_state.get('refresh_key', 0)}")
            if len(row) > 1:
                with o2:
                    v = row[1]
                    label = MAP_LABELS.get(v, v.replace('_', ' ').upper())
                    context[v] = st.text_input(label, value=st.session_state.context_cache.get(v, ''),
                                              key=f"in_{v}_{st.session_state.get('refresh_key', 0)}")
    # --- TỰ ĐỘNG LƯU DỮ LIỆU ---
    st.session_state.context_cache = context
    save_cache({
        'context_cache': context,
        'ds_thanhvien': st.session_state.ds_thanhvien,
        'ds_huongloi': st.session_state.ds_huongloi
    })

    # --- 5. XUẤT FILE ---
    col_export, col_clear = st.columns([2, 1])
    
    with col_export:
        if st.button("🚀 XUẤT HỒ SƠ", use_container_width=True):
            if 'is_same' in locals() and is_same:
                for v in csh_vars:
                    source = v.replace('csh_', 'ddpl_')
                    if source in context: context[v] = context[source]

            # Tính tỷ lệ tự động nếu có nhập số vốn
            try:
                valid_vons = [m['vongop'] for m in st.session_state.ds_thanhvien if m['vongop'] and m['vongop'] > 0]
                total_v = sum(valid_vons)
                for m in st.session_state.ds_thanhvien:
                    if m['vongop'] and m['vongop'] > 0 and total_v > 0:
                        m['tyle'] = round((m['vongop'] / total_v * 100), 3)
                    else:
                        m['tyle'] = ""
            except:
                pass

            # Chuyển dữ liệu export sang định dạng văn bản đẹp
            export_members = []
            for m in st.session_state.ds_thanhvien:
                export_item = m.copy()
                if export_item.get('vongop') and isinstance(export_item['vongop'], (int, float)) and export_item['vongop'] > 0:
                    export_item['vongop'] = format_number_with_dots(export_item['vongop'])
                else:
                    export_item['vongop'] = ""

                if export_item.get('tyle') != "" and export_item.get('tyle') is not None:
                    export_item['tyle'] = format_percent(export_item['tyle']) if isinstance(export_item['tyle'], (int, float)) else str(export_item['tyle'])
                else:
                    export_item['tyle'] = ""

                export_members.append(export_item)

            context['ds_thanhvien'] = export_members
            context['ds_huongloi'] = st.session_state.ds_huongloi

            try:
                # 1. Lấy thông tin thời gian hiện tại
                now = datetime.datetime.now()
                curr_year = str(now.year)
                curr_month = now.strftime('%m')

                # 2. Xử lý tên công ty: Bỏ dấu nhưng giữ nguyên HOA và khoảng trắng
                raw_company = context.get('dn_tencongty', 'Ho So Moi').strip()
                clean_company = remove_accents(raw_company)
                company_code = context.get('dn_masodoanhnghiep', '').strip()

                # 3. Tên thư mục: nếu có mã số doanh nghiệp thì sử dụng "MÃ SỐ - TÊN CÔNG TY"
                if company_code:
                    folder_name = f"{company_code} - {clean_company}"
                else:
                    folder_name = clean_company

                # 4. Tạo cấu trúc thư mục: Năm / Tên Công Ty / Tháng
                save_path = os.path.join(OUTPUT_DIR, curr_year, folder_name, curr_month)
                os.makedirs(save_path, exist_ok=True)
                for f in selected_files:
                    doc = DocxTemplate(os.path.join(selected_path, f))
                    doc.render(context)
                    doc.save(os.path.join(save_path, f))
                
                # LƯU CACHE SAU KHI XUẤT THÀNH CÔNG
                cache_to_save = {
                    'context_cache': context,
                    'ds_thanhvien': st.session_state.ds_thanhvien,
                    'ds_huongloi': st.session_state.ds_huongloi
                }
                save_cache(cache_to_save)
                st.session_state.context_cache = context
                
                st.success(f"✅ Đã xuất tại: {save_path}")
                st.balloons()
            except Exception as e:
                st.error(f"Lỗi: {e}")
    
    with col_clear:
        if st.button("🗑️ XOÁ THÔNG TIN", use_container_width=True, help="Làm sạch dữ liệu hiện tại và huỷ chọn khách hàng"):
            clear_cache()
            st.session_state.context_cache = {}
            st.session_state.ds_thanhvien = [{
                'hoten': '', 'ngaysinh': '', 'gioitinh': '', 'cccd': '', 
                'quoctich': '', 'dantoc': '', 'diachi': '', 
                'vongop': 0.0, 'thoihan': '90 ngày kể từ ngày cấp GCNĐKDN', 'taisan': 'Đồng Việt Nam', 'tyle': ''
            }]
            st.session_state.ds_huongloi = [{
                'hoten': '', 'ngaysinh': '', 'gioitinh': '', 'cccd': '', 
                'quoctich': '', 'dantoc': '', 'diachi': '', 
                'tyle_vdl': '', 'tyle_bieuquyet': '', 
                'quyen_chiphoi': '- Bổ nhiệm, miễn nhiệm hoặc bãi nhiệm đa số hoặc tất cả thành viên hội đồng quản trị, giám đốc hoặc tổng giám đốc của doanh nghiệp\n- Sửa đổi, bổ sung điều lệ của doanh nghiệp\n- Thay đổi cơ cấu tổ chức quản lý công ty\n- Tổ chức lại, giải thể công ty'
            }]
            st.session_state.previous_customer = ""
            st.session_state.profile_loaded = False
            st.session_state.refresh_key = st.session_state.get('refresh_key', 0) + 1
            st.session_state.reset_all = True  # Trigger widget reset
            st.success("✅ Đã xoá thông tin hiện tại")
            st.rerun()
else:
    st.warning("Vui lòng chọn các file mẫu ở cột bên trái để bắt đầu nhập liệu.")