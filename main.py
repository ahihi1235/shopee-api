import streamlit as st
import requests
import json
import re

# --- CẤU HÌNH GIAO DIỆN ĐỂ NHÚNG VÀO PHP ---
st.set_page_config(layout="wide")

# Ẩn Menu và Footer của Streamlit để nhìn cho giống API
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {
                padding-top: 0rem;
                padding-bottom: 0rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- LOGIC XỬ LÝ (Giữ nguyên logic cũ của bạn) ---
def get_shopee_link(original_url):
    # Lấy cookie từ Secrets của Streamlit
    if "SHOPEE_COOKIE" in st.secrets:
        cookie_str = st.secrets["SHOPEE_COOKIE"]
    else:
        return "Lỗi: Chưa cấu hình Secrets"

    headers = {
        "content-type": "application/json",
        "cookie": cookie_str,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "referer": "https://affiliate.shopee.vn/"
    }
    
    # Logic gọi API Shopee
    try:
        payload = {
            "operationName": "batchGetCustomLink",
            "query": "query batchGetCustomLink($linkParams: [CustomLinkParam!], $sourceCaller: SourceCaller) { batchCustomLink(linkParams: $linkParams, sourceCaller: $sourceCaller) { shortLink failCode } }",
            "variables": {
                "linkParams": [{"originalLink": original_url}],
                "sourceCaller": "CUSTOM_LINK_CALLER"
            }
        }
        resp = requests.post("https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink", headers=headers, json=payload, timeout=10)
        data = resp.json()
        results = data.get('data', {}).get('batchCustomLink', [])
        
        if results:
            return results[0].get('shortLink', f"Lỗi failCode: {results[0].get('failCode')}")
        return "Lỗi: Không có kết quả trả về"
    except Exception as e:
        return f"Lỗi hệ thống: {str(e)}"

# --- PHẦN QUAN TRỌNG: NHẬN LINK TỪ PHP ---
# Lấy tham số ?url=... từ trên thanh địa chỉ
query_params = st.query_params
url_input = query_params.get("url", None)

# Giao diện hiển thị kết quả
st.markdown("### Kết quả chuyển đổi:")

if url_input:
    # Nếu có link trên thanh địa chỉ thì tự động chạy
    with st.spinner(f'Đang xử lý: {url_input} ...'):
        short_link = get_shopee_link(url_input)
        
    if "http" in short_link:
        st.success("Thành công!")
        st.code(short_link, language="text")
        st.markdown(f"[Bấm để mở link]({short_link})")
    else:
        st.error(short_link)
else:
    st.info("Vui lòng nhập link từ giao diện bên ngoài.")
