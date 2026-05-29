import os
import google.generativeai as genai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 強制清除環境變數隱藏空白
gemini_key = os.environ.get('GEMINI_API_KEY', '').strip()
line_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '').strip()
line_secret = os.environ.get('LINE_CHANNEL_SECRET', '').strip()

line_bot_api = LineBotApi(line_token)
handler = WebhookHandler(line_secret)
genai.configure(api_key=gemini_key)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 【大腦改造區：極度簡潔、邏輯條列】
        system_prompt = """你現在是「2026美加墨世界盃」專業足球分析師。
你的回覆必須嚴格遵守以下規則：
1. 極度簡潔：總字數控制在 100 字以內，不說廢話、不講客套話。
2. 邏輯清晰：必須使用「條列式」呈現戰力數據或賽事重點。
3. 專業客觀：提供準確的足球賽事與歷史分析。
4. 引流結語：結尾固定用一句話，自然引導球迷加入我們的「世界盃私密討論社群」。"""
        
        # 關閉安全審查，防止真實體育對話被誤擋
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
        
        response = model.generate_content(
            f"{system_prompt}\n\n用戶說：{user_msg}",
            safety_settings=safety_settings
        )
        
        try:
            reply_text = response.text
        except ValueError:
            reply_text = "這個問題裁判吹哨不讓我說！我們來聊聊接下來的賽事預測吧。"
            
    except Exception as e:
        reply_text = f"【系統錯誤回報】\n{str(e)}"

    # 【純文字無錯發送區】
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        print(f"發送訊息失敗: {e}")

if __name__ == "__main__":
    app.run()
