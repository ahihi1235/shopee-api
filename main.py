import streamlit as st
import requests
import json
import streamlit.components.v1 as components # Cần thêm thư viện này để tạo nút Copy xịn

# ===== 1. CẤU HÌNH GIAO DIỆN =====
st.set_page_config(page_title="Shopee Tool", layout="centered")

# ===== 2. CSS QUAN TRỌNG: FIX LỖI NHỎ XÍU TRÊN IPHONE =====
st.markdown("""
    <style>
        /* --- PHẦN 1: ẨN CÁC THÀNH PHẦN THEO YÊU CẦU CỦA BẠN --- */
        
        /* Ẩn Header/Footer mặc định */
        header, footer { visibility: hidden; height: 0px; }
        
        /* Ẩn Expander (Cấu hình SubID) */
        div[data-testid="stExpander"] { display: none !important; }
        
        /* Ẩn thanh Tab (Người dùng sẽ chỉ thấy nội dung Tab 1) */
        div[data-baseweb="tab-list"] { display: none !important; }

        /* --- PHẦN 2: TỐI ƯU HIỂN THỊ TRÊN MOBILE (FIX LỖI MÀN HÌNH NHỎ) --- */
        
        /* 1. Căn lề lại container chính cho sát viền điện thoại */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            max-width: 100% !important;
        }

        /* 2. Ép cỡ chữ nhập liệu lên 16px (iPhone sẽ không tự zoom khi bấm vào) */
        .stTextInput input, .stTextArea textarea {
            font-size: 16px !important;
            padding: 10px !important;
            border-radius: 10px !important;
        }

        /* 3. Nút bấm to, dễ bấm bằng ngón tay cái */
        .stButton button {
            width: 100% !important;
            height: 50px !important;
            font-size: 16px !important;
            font-weight: bold !important;
            border-radius: 10px !important;
        }
        
        /* 4. Code block hiển thị kết quả dễ nhìn hơn */
        code {
            font-size: 14px !important;
            white-space: pre-wrap !important;
        }
    </style>
""", unsafe_allow_html=True)

# ===== HÀM COPY JAVASCRIPT (ĐỂ NÚT COPY ĐẸP HƠN) =====
def copy_button(text):
    escaped_text = json.dumps(text)
    html_code = f"""
    <div style="margin-top: 5px;">
        <button onclick="copyToClipboard()" style="
            width: 100%;
            background-color: #EE4D2D;
            color: white; border: none; padding: 12px;
            border-radius: 10px; font-weight: bold; font-size: 16px;
            cursor: pointer;
        ">📋 SAO CHÉP NGAY</button>
    </div>
    <script>
    function copyToClipboard() {{
        navigator.clipboard.writeText({escaped_text}).then(function() {{
            alert('Đã copy thành công!');
        }});
    }}
    </script>
    """
    components.html(html_code, height=60)

# ===== XỬ LÝ COOKIE & LOGIC =====
def process_cookie_input(raw_input):
    if not raw_input: return ""
    try:
        data = json.loads(raw_input)
        if isinstance(data, dict) and "cookies" in data:
            return "; ".join([f"{c['name']}={c['value']}" for c in data["cookies"] if "name" in c])
        return raw_input
    except: return raw_input

if "SHOPEE_COOKIE" in st.secrets:
    cookie_str = process_cookie_input(st.secrets["SHOPEE_COOKIE"])
else:
    st.error("Chưa cấu hình SHOPEE_COOKIE!")
    st.stop()

# Cấu hình SubID (Đã bị ẩn hiển thị bởi CSS ở trên, nhưng code vẫn chạy ngầm)
with st.expander("⚙️ Cấu hình SubID"):
    sub_ids = {}
    c1, c2 = st.columns(2)
    for i in range(1, 5):
        target = c1 if i % 2 != 0 else c2
        val = target.text_input(f"SubID {i}", key=f"s{i}")
        if val: sub_ids[f"subId{i}"] = val

def call_api(links, sub_dict):
    url = "https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink"
    headers = {
        "content-type": "application/json",
        "cookie": cookie_str,
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
    }
    payload = {
        "operationName": "batchGetCustomLink",
        "query": "query batchGetCustomLink($linkParams: [CustomLinkParam!], $sourceCaller: SourceCaller) { batchCustomLink(linkParams: $linkParams, sourceCaller: $sourceCaller) { shortLink, failCode } }",
        "variables": {"linkParams": [{"originalLink": l, "advancedLinkParams": sub_dict} for l in links], "sourceCaller": "CUSTOM_LINK_CALLER"}
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        return r.json().get('data', {}).get('batchCustomLink', [])
    except: return []

# ===== GIAO DIỆN CHÍNH =====
st.title("Chuyển Đổi Link")

# Code của bạn dùng st.tabs nhưng CSS đã ẩn thanh tab đi.
# Điều này có nghĩa là NGƯỜI DÙNG CHỈ THẤY TAB 1.
# Tab 2 vẫn tồn tại trong code nhưng không bấm vào được (đúng theo CSS bạn gửi).
tab1, tab2 = st.tabs(["📋 Link List", "📝 Content"])

with tab1:
    txt = st.text_area("Nhập link (mỗi dòng 1 link):", height=150)
    if st.button("🚀 CHUYỂN ĐỔI", use_container_width=True):
        links = [l.strip() for l in txt.split('\n') if l.strip()]
        if links:
            with st.spinner("Đang xử lý..."):
                res = call_api(links, sub_ids)
                out = [r.get('shortLink') or f"Lỗi" for r in res]
                final_text = "\n".join(out)
                st.code(final_text)
                # Thêm nút copy
                copy_button(final_text)

with tab2:
    # Phần này sẽ bị ẩn do CSS ẩn thanh Tab, nhưng tôi vẫn giữ nguyên code cho bạn
    con = st.text_area("Dán bài viết cần thay link:", height=200)
    if st.button("🔄 Thay thế link", use_container_width=True):
        import re # Import lại ở đây cho chắc
        found = list(set(re.findall(r'(https?://s\.shopee\.vn/[a-zA-Z0-9]+)', con)))
        if found:
            res = call_api(found, sub_ids)
            new_con = con
            for old, r in zip(found, res):
                if r.get('shortLink'): new_con = new_con.replace(old, r['shortLink'])
            st.code(new_con)
