from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import os

app = FastAPI()

class LinkRequest(BaseModel):
    url: str
    subId1: str = None

@app.post("/convert")
async def convert_link(req: LinkRequest):
    # Lấy Cookie và xử lý sơ bộ
    raw_cookie = os.getenv("SHOPEE_COOKIE", "").strip()
    
    # Loại bỏ dấu ngoặc kép nếu lỡ tay điền vào Render
    if raw_cookie.startswith('"') and raw_cookie.endswith('"'):
        raw_cookie = raw_cookie[1:-1]
    
    # Kiểm tra xem Cookie có bị trống không
    if not raw_cookie:
        return {"status": "error", "message": "Loi: Cookie tren Render dang bi trong!"}

    url = "https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink"
    headers = {
        "content-type": "application/json",
        "cookie": raw_cookie, 
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "referer": "https://affiliate.shopee.vn/",
        "origin": "https://affiliate.shopee.vn"
    }

    payload = {
        "operationName": "batchGetCustomLink",
        "query": "query batchGetCustomLink($linkParams: [CustomLinkParam!], $sourceCaller: SourceCaller) { batchCustomLink(linkParams: $linkParams, sourceCaller: $sourceCaller) { shortLink failCode } }",
        "variables": {
            "linkParams": [{"originalLink": req.url, "advancedLinkParams": {"subId1": req.subId1} if req.subId1 else {}}],
            "sourceCaller": "CUSTOM_LINK_CALLER"
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        data = resp.json()
        
        # --- DEBUG QUAN TRỌNG ---
        # Kiểm tra xem Shopee có báo lỗi authentication không
        if 'errors' in data:
            err_msg = data['errors'][0].get('message', 'Unknown Error')
            return {
                "status": "error", 
                "message": f"Shopee tu choi: {err_msg}",
                "debug_cookie_dau": raw_cookie[:20] + "..." # Xem 20 kytu dau cua cookie de check
            }

        # Kiểm tra data
        results = data.get('data')
        if results is None: 
            return {
                "status": "error", 
                "message": "Shopee tra ve NULL. Kha nang cao la Cookie chet hoac IP bi chan.",
                "raw_response": data
            }

        batch_list = results.get('batchCustomLink')
        if not batch_list:
            return {"status": "error", "message": "Danh sach link tra ve bi rong. Check lai Link input."}

        res = batch_list[0]
        if res.get('shortLink'):
            return {"status": "success", "shortLink": res['shortLink']}
        
        return {"status": "error", "message": f"That bai. FailCode: {res.get('failCode')}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
async def home():
    return {"message": "API Online"}
