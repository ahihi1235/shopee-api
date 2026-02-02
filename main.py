from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import uvicorn
import os

app = FastAPI()

# Lấy Cookie từ môi trường (Environment Variables)
SHOPEE_COOKIE = os.getenv("SHOPEE_COOKIE", "")

def process_cookie(raw_cookie):
    try:
        data = json.loads(raw_cookie)
        if isinstance(data, dict) and "cookies" in data:
            return "; ".join([f"{c['name']}={c['value']}" for c in data["cookies"]])
        return raw_cookie
    except:
        return raw_cookie

COOKIE_STR = process_cookie(SHOPEE_COOKIE)

class LinkRequest(BaseModel):
    url: str
    subId1: str = None

@app.post("/convert")
async def convert_link(req: LinkRequest):
    if not COOKIE_STR:
        raise HTTPException(status_code=500, detail="Chưa cấu hình Cookie")

    api_url = "https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink"
    headers = {
        "content-type": "application/json",
        "cookie": COOKIE_STR,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
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
        resp = requests.post(api_url, headers=headers, json=payload)
        data = resp.json()
        result = data.get('data', {}).get('batchCustomLink', [])[0]
        if result.get('shortLink'):
            return {"status": "success", "shortLink": result['shortLink']}
        return {"status": "error", "failCode": result.get('failCode')}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
