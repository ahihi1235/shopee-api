import streamlit as st
import requests
import json
import re
import time

# Cấu hình cơ bản nhất, không dùng CSS phức tạp để tránh lỗi trình duyệt
st.set_page_config(page_title="Shopee Tool", layout="centered")

st.markdown("""
    <style>
        /* Ẩn phần Expander (Cấu hình SubID) */
        div[data-testid="stExpander"] {
            display: none !important;
        }

        /* Ẩn Tab thứ 2 (Content) */
        button[id="tabs-bui3-tab-1"] { 
            display: none !important;
        }
        /* Ẩn toàn bộ thanh chứa các Tab */
        div[data-baseweb="tab-list"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# CSS tối giản, chỉ ẩn footer để giảm tải cho Safari
st.markdown("""
    <style>
        footer {visibility: hidden;}
        .stCodeBlock { background-color: #f0f2f6 !important; }
    </style>
""", unsafe_allow_html=True)

# ===== HÀM XỬ LÝ COOKIE =====
def process_cookie_input(raw_input):
    if not raw_input: return ""
    try:
        data = json.loads(raw_input)
        if isinstance(data, dict) and "cookies" in data:
            return "; ".join([f"{c['name']}={c['value']}" for c in data["cookies"] if "name" in c])
        return raw_input
    except:
        return raw_input

# ===== KIỂM TRA SECRETS =====
if "SHOPEE_COOKIE" in st.secrets:
    cookie_str = process_cookie_input(st.secrets["SHOPEE_COOKIE"])
else:
    st.error("Chưa cấu hình SHOPEE_COOKIE trong Settings > Secrets!")
    st.stop()

# ===== GIAO DIỆN =====
st.title("Chuyển Đổi Link")

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

tab1, tab2 = st.tabs(["📋 Link List", "📝 Content"])

with tab1:
    txt = st.text_area("Nhập link (mỗi dòng 1 link):", height=150)
    if st.button("🚀 Chuyển đổi", use_container_width=True):
        links = [l.strip() for l in txt.split('\n') if l.strip()]
        if links:
            res = call_api(links, sub_ids)
            out = [r.get('shortLink') or f"Lỗi {r.get('failCode')}" for r in res]
            st.code("\n".join(out))

with tab2:
    con = st.text_area("Dán bài viết cần thay link:", height=200)
    if st.button("🔄 Thay thế link", use_container_width=True):
        found = list(set(re.findall(r'(https?://s\.shopee\.vn/[a-zA-Z0-9]+)', con)))
        if found:
            res = call_api(found, sub_ids)
            new_con = con
            for old, r in zip(found, res):
                if r.get('shortLink'): new_con = new_con.replace(old, r['shortLink'])
            st.code(new_con)
