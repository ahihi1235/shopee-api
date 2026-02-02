from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import os

app = FastAPI()

# --- MODEL DỮ LIỆU (Bắt buộc phải có để nhận từ PHP) ---
class LinkRequest(BaseModel):
    url: str
    subId1: str = None

# --- HÀM XỬ LÝ COOKIE (Giữ nguyên từ code gốc của bạn) ---
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

# --- API ENDPOINT ---
@app.post("/convert")
async def convert_link(req: LinkRequest):
    # Lấy cookie từ biến môi trường của Render
    raw_cookie = os.getenv("SHOPEE_COOKIE", "")
    cookie_str = process_cookie_input(raw_cookie)
    
    if not cookie_str:
        return {"status": "error", "message": "Chua cau hinh SHOPEE_COOKIE tren Render"}

    url = "https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "cookie": cookie_str,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "origin": "https://shopee.vn",
        "referer": "https://shopee.vn/",
    }

    # Cấu hình Params y hệt bản gốc
    link_params = [{"originalLink": req.url}]
    if req.subId1:
        link_params[0]["advancedLinkParams"] = {"subId1": req.subId1}

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
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        data = resp.json()
        results = data.get('data', {}).get('batchCustomLink', [])
        
        # Sửa lỗi 'list index out of range' bằng cách kiểm tra danh sách
        if results and len(results) > 0:
            res = results[0]
            if res.get('shortLink'):
                return {"status": "success", "shortLink": res['shortLink']}
            else:
                return {"status": "error", "message": f"Shopee failCode: {res.get('failCode')}"}
        
        return {"status": "error", "message": "Shopee khong tra ve ket qua. Kiem tra lai link hoac Cookie."}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# Thêm trang chủ để tránh lỗi 404 khi vào link Render trực tiếp
@app.get("/")
async def home():
    return {"status": "online", "message": "API Shopee dang chay binh thuong"}
