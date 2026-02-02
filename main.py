from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import os

app = FastAPI()

class LinkRequest(BaseModel):
    url: str
    subId1: str = None

def process_cookie_input(raw_input):
    if not raw_input: return ""
    try:
        cookie_data = json.loads(raw_input)
        if isinstance(cookie_data, dict) and "cookies" in cookie_data:
            cookies_list = cookie_data["cookies"]
        elif isinstance(cookie_data, list):
            cookies_list = cookie_data
        else: return raw_input
        return "; ".join([f"{c['name']}={c['value']}" for c in cookies_list if "name" in c and "value" in c])
    except: return raw_input

@app.post("/convert")
async def convert_link(req: LinkRequest):
    raw_cookie = os.getenv("SHOPEE_COOKIE", "")
    cookie_str = process_cookie_input(raw_cookie)
    
    if not cookie_str:
        return {"status": "error", "message": "API thieu Cookie. Hay kiem tra Render Env."}

    url = "https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink"
    # Header đầy đủ để đánh lừa Shopee
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "cookie": cookie_str,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
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
        
        # KIỂM TRA LỖI TRƯỚC KHI TRUY CẬP PHẦN TỬ 0
        results = data.get('data', {}).get('batchCustomLink')
        
        if results is None:
            return {"status": "error", "message": "Shopee tu choi yeu cau (JSON empty)", "raw_shopee": data}
            
        if len(results) == 0:
            return {"status": "error", "message": "Shopee tra ve danh sach rong. Cookie co the bi sai hoac thieu quyen.", "raw_shopee": data}

        res = results[0]
        if res.get('shortLink'):
            return {"status": "success", "shortLink": res['shortLink']}
        return {"status": "error", "message": f"Loi tu Shopee. failCode: {res.get('failCode')}"}

    except Exception as e:
        return {"status": "error", "message": f"Loi he thong: {str(e)}"}

@app.get("/")
async def health():
    return {"status": "ok"}
