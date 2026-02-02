import streamlit as st
import requests
import json
import re
import time
import streamlit.components.v1 as components

# ===== CẤU HÌNH TRANG =====
st.set_page_config(page_title="Shopee Tool", layout="centered")

# CSS tối giản - Tuyệt đối không dùng các thuộc tính gây lỗi Safari
st.markdown("""
    <style>
        header, footer { visibility: hidden; height: 0px; }
        .stButton button { border-radius: 10px; height: 3em; font-weight: bold; }
        .stTextArea textarea { border-radius: 10px; }
        /* Làm nổi bật vùng kết quả */
        .result-box {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #dcdfe6;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# ===== HÀM CÔNG CỤ: COPY VÀO BỘ NHỚ TẠM (FRIENDLY) =====
def copy_button(text):
    """Tạo một nút bấm Copy to Clipboard thân thiện bằng JavaScript"""
    escaped_text = json.dumps(text)
    html_code = f"""
    <button onclick="copyToClipboard()" style="
        width: 100%;
        background-color: #EE4D2D;
        color: white;
        border: none;
        padding: 12px;
        border-radius: 10px;
        font-weight: bold;
        cursor: pointer;
        margin-top: 10px;
        font-family: sans-serif;
    ">📋 SAO CHÉP KẾT QUẢ</button>

    <script>
    function copyToClipboard() {{
        const text = {escaped_text};
        navigator.clipboard.writeText(text).then(function() {{
            alert('Đã copy thành công!');
        }}, function(err) {{
            console.error('Lỗi khi copy: ', err);
        }});
    }}
    </script>
    """
    components.html(html_code, height=65)

# ===== HÀM XỬ LÝ COOKIE & API =====
def process_cookie_input(raw_input):
    if not raw_input: return ""
    try:
        data = json.loads(raw_input)
        if isinstance(data, dict) and "cookies" in data:
            return "; ".join([f"{c['name']}={c['value']}" for c in data["cookies"] if "name" in c])
        return raw_input
    except: return raw_input

def call_api(links, sub_dict, cookie_str):
    url = "https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink"
    headers = {
        "content-type": "application/json",
        "cookie": cookie_str,
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
    }
    payload = {
        "operationName": "batchGetCustomLink",
        "query": "query batchGetCustomLink($linkParams: [CustomLinkParam!], $sourceCaller: SourceCaller) { batchCustomLink(linkParams: $linkParams, sourceCaller: $sourceCaller) { shortLink, failCode } }",
        "variables": {
            "linkParams": [{"originalLink": l, "advancedLinkParams": sub_dict} for l in links],
            "sourceCaller": "CUSTOM_LINK_CALLER"
        }
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        return r.json().get('data', {}).get('batchCustomLink', [])
    except: return []

# ===== THANH SIDEBAR (NƠI ẨN CÁC TÙY CHỌN) =====
with st.sidebar:
    st.header("⚙️ Cài đặt")
    show_subid = st.checkbox("Hiện cấu hình SubID", value=False)
    show_content_tab = st.checkbox("Hiện tab Content", value=False)
    st.divider()
    st.info("Cookie được lấy tự động từ Secrets.")

# Xử lý lấy Cookie
if "SHOPEE_COOKIE" in st.secrets:
    cookie_str = process_cookie_input(st.secrets["SHOPEE_COOKIE"])
else:
    st.error("Thiếu SHOPEE_COOKIE trong Secrets!")
    st.stop()

# Xử lý SubID (Nếu không hiện thì để trống)
sub_ids = {}
if show_subid:
    with st.expander("⚙️ Cấu hình SubID", expanded=True):
        c1, c2 = st.columns(2)
        for i in range(1, 6):
            target = c1 if i % 2 != 0 else c2
            val = target.text_input(f"SubID {i}", key=f"s{i}")
            if val: sub_ids[f"subId{i}"] = val

# ===== GIAO DIỆN CHÍNH =====
st.title("Shopee Affiliate Tool")

# Điều hướng Tab dựa trên cài đặt ở Sidebar
if show_content_tab:
    tab1, tab2 = st.tabs(["📋 Danh sách Link", "📝 Chuyển Content"])
else:
    tab1 = st.container()
    tab2 = st.empty()

with tab1:
    st.write("Nhập danh sách link Shopee (mỗi link 1 dòng):")
    txt = st.text_area("Input Links", height=150, label_visibility="collapsed", placeholder="https://shopee.vn/product/...")
    
    if st.button("🚀 CHUYỂN ĐỔI NGAY", use_container_width=True, type="primary"):
        links = [l.strip() for l in txt.split('\n') if l.strip()]
        if not links:
            st.warning("Vui lòng nhập ít nhất 1 link!")
        else:
            with st.spinner("Đang xử lý..."):
                results = call_api(links, sub_ids, cookie_str)
                final_text = "\n".join([r.get('shortLink') or f"Lỗi: {r.get('failCode')}" for r in results])
                
                if final_text:
                    st.success("Đã xử lý xong!")
                    st.code(final_text) # Vẫn hiện code để xem nhanh
                    copy_button(final_text) # Nút copy to, dễ bấm trên iPhone

if show_content_tab:
    with tab2:
        st.write("Dán bài viết chứa link Shopee:")
        con = st.text_area("Input Content", height=200, label_visibility="collapsed", placeholder="Săn sale ngay tại https://s.shopee.vn/abc...")
        
        if st.button("🔄 CHUYỂN ĐỔI CONTENT", use_container_width=True, type="primary"):
            found = list(set(re.findall(r'(https?://s\.shopee\.vn/[a-zA-Z0-9]+)', con)))
            if not found:
                st.warning(" không tìm thấy link s.shopee.vn nào!")
            else:
                with st.spinner(f"Đang chuyển {len(found)} link..."):
                    results = call_api(found, sub_ids, cookie_str)
                    new_con = con
                    for old, r in zip(found, results):
                        if r.get('shortLink'):
                            new_con = new_con.replace(old, r['shortLink'])
                    
                    st.success("Đã chuyển đổi thành công!")
                    st.code(new_con)
                    copy_button(new_con)
