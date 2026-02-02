from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import os
import re

app = FastAPI()

class LinkRequest(BaseModel):
    url: str
    subId1: str = None

def get_csrf_token(cookie_str):
    # Tìm giá trị csrftoken trong chuỗi cookie
    match = re.search(r'csrftoken=([a-zA-Z0-9]+)', cookie_str)
    if match:
        return match.group(1)
    return None

@app.post("/convert")
async def convert_link(req: LinkRequest):
    # 1. Lấy và làm sạch Cookie
    raw_cookie = os.getenv("SHOPEE_COOKIE", "").strip()
    if raw_cookie.startswith('"') and raw_cookie.endswith('"'):
        raw_cookie = raw_cookie[1:-1]

    if not raw_cookie:
        return {"status": "error", "message": "Chua co Cookie tren Render"}

    # 2. Trích xuất CSRF Token (Chìa khóa quan trọng để fix lỗi 90309999)
    csrf_token = get_csrf_token(raw_cookie)
    
    # 3. Giả lập trình duyệt Chrome 100%
    url = "https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink"
    headers = {
        "authority": "affiliate.shopee.vn",
        "accept": "*/*",
        "accept-language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "cookie": raw_cookie,
        "origin": "https://affiliate.shopee.vn",
        "referer": "https://affiliate.shopee.vn/offer/custom_link",
        "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        # QUAN TRỌNG: Thêm CSRF Token vào Header
        "x-csrftoken": csrf_token if csrf_token else "missing"
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
        
        # --- DEBUG CHI TIẾT ---
        if 'error' in data.get('raw_shopee', {}) or data.get('error'):
             return {
                "status": "error",
                "message": "Shopee van chan IP Render (Error 90309999).",
                "suggestion": "Cookie ok, Token ok, nhung IP Render bi blacklist.",
                "debug_info": data
            }

        # Xử lý kết quả bình thường
        results = data.get('data', {}).get('batchCustomLink')
        if results and len(results) > 0:
            res = results[0]
            if res.get('shortLink'):
                return {"status": "success", "shortLink": res['shortLink']}
            else:
                 return {"status": "error", "message": f"Shopee tu choi link nay. FailCode: {res.get('failCode')}"}
        
        # Nếu vẫn lỗi
        if 'errors' in data:
             return {"status": "error", "message": data['errors'][0].get('message')}

        return {"status": "error", "message": "Unknown Response", "raw": data}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
async def home():
    return "API Ready"
