import streamlit as st
import requests
import json
import re
import time

# ===== CẤU HÌNH GIAO DIỆN =====
st.set_page_config(page_title="Shopee Tool", layout="wide")

# CSS TỐI ƯU CHO MOBILE (KHÔNG GÂY TRẮNG MÀN HÌNH)
st.markdown("""
    <style>
        /* Ẩn header và footer của Streamlit */
        header, footer {
            visibility: hidden;
            height: 0px;
        }
        
        /* Tối ưu khoảng cách nội dung cho Mobile */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* Ẩn nút View Fullscreen trên ảnh/code block */
        button[title="View fullscreen"] {
            display: none !important;
        }

        /* Làm gọn giao diện Tab */
        div[data-testid="stTabList"] {
            gap: 10px;
        }
        
        /* Tùy chỉnh hiển thị Code Block để dễ nhìn trên điện thoại */
        code {
            white-space: pre-wrap !important;
            word-break: break-all !important;
        }
    </style>
""", unsafe_allow_html=True)

# ===== HÀM XỬ LÝ COOKIE THÔNG MINH =====
def process_cookie_input(raw_input):
    if not raw_input:
        return ""
    try:
        cookie_data = json.loads(raw_input)
        if isinstance(cookie_data, dict) and "cookies" in cookie_data:
            cookies_list = cookie_data["cookies"]
        elif isinstance(cookie_data, list):
            cookies_list = cookie_data
        else:
            return raw_input

        formatted_cookies = []
        for c in cookies_list:
            if "name" in c and "value" in c:
                formatted_cookies.append(f"{c['name']}={c['value']}")
        return "; ".join(formatted_cookies)
    except json.JSONDecodeError:
        return raw_input

# ===== LOAD VÀ XỬ LÝ COOKIE =====
cookie_str = ""
if "SHOPEE_COOKIE" in st.secrets:
    cookie_str = process_cookie_input(st.secrets["SHOPEE_COOKIE"])
else:
    st.error("❌ Lỗi: Chưa cấu hình 'SHOPEE_COOKIE' trong mục Secrets của Streamlit!")
    st.stop()

# ===== KHU VỰC CẤU HÌNH SUB_ID =====
with st.expander("⚙️ Cấu hình SubID (Tùy chọn)"):
    cols = st.columns(2) # Chia 2 cột cho mobile dễ nhìn
    sub_ids = {}
    for i in range(5):
        val = st.text_input(f"SubID {i+1}", key=f"sub_{i+1}")
        if val.strip():
            sub_ids[f"subId{i+1}"] = val.strip()

# ===== HÀM GỌI API =====
def call_shopee_api(links_batch, sub_ids_dict):
    URL = "https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "cookie": cookie_str,
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    }

    link_params = []
    for link in links_batch:
        item = {"originalLink": link}
        if sub_ids_dict:
            item["advancedLinkParams"] = sub_ids_dict
        link_params.append(item)

    payload = {
        "operationName": "batchGetCustomLink",
        "query": """
        query batchGetCustomLink($linkParams: [CustomLinkParam!], $sourceCaller: SourceCaller) {
          batchCustomLink(linkParams: $linkParams, sourceCaller: $sourceCaller) {
            shortLink
            failCode
          }
        }
        """,
        "variables": {
            "linkParams": link_params,
            "sourceCaller": "CUSTOM_LINK_CALLER"
        }
    }

    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            return resp.json().get('data', {}).get('batchCustomLink', [])
    except:
        return []
    return []

# ===== GIAO DIỆN CHÍNH =====
st.title("Shopee Link Tool")
tab1, tab2 = st.tabs(["📋 Danh sách Link", "📝 Chuyển Content"])

with tab1:
    raw_input = st.text_area("Dán link Shopee vào đây (mỗi link 1 dòng):", height=150)
    if st.button("🚀 Chuyển Đổi Ngay", key="btn_tab1", use_container_width=True):
        if not raw_input.strip():
            st.warning("Vui lòng nhập link!")
        else:
            input_links = [l.strip() for l in raw_input.split('\n') if l.strip()]
            final_results = []
            progress = st.progress(0)
            
            batch_size = 50
            for i in range(0, len(input_links), batch_size):
                chunk = input_links[i : i + batch_size]
                results = call_shopee_api(chunk, sub_ids)
                if results:
                    for res in results:
                        final_results.append(res.get('shortLink') or f"Lỗi: {res.get('failCode')}")
                else:
                    final_results.extend(["Lỗi API"] * len(chunk))
                progress.progress(min((i + batch_size) / len(input_links), 1.0))
            
            st.success("Xong! Copy kết quả bên dưới:")
            st.code("\n".join(final_results))

with tab2:
    content_input = st.text_area("Dán bài viết chứa link s.shopee.vn:", height=200)
    if st.button("🔄 Chuyển Đổi Bài Viết", key="btn_tab2", use_container_width=True):
        if not content_input.strip():
            st.warning("Vui lòng nhập nội dung!")
        else:
            found_links = list(set(re.findall(r'(https?://s\.shopee\.vn/[a-zA-Z0-9]+)', content_input)))
            if not found_links:
                st.warning("Không tìm thấy link s.shopee.vn nào!")
            else:
                with st.spinner(f"Đang xử lý {len(found_links)} link..."):
                    mapping = {}
                    results = call_shopee_api(found_links, sub_ids)
                    if results:
                        for old, res in zip(found_links, results):
                            if res.get('shortLink'):
                                mapping[old] = res['shortLink']
                    
                    new_content = content_input
                    for old, new in mapping.items():
                        new_content = new_content.replace(old, new)
                    
                    st.success("Đã chuyển đổi thành công!")
                    st.code(new_content)
