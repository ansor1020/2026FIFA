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
        
        # 【大腦改造區：把結語拔掉，讓 AI 專心處理數據分析】
        system_prompt = """你現在是「2026美加墨世界盃」專業足球分析師。
你的回覆必須嚴格遵守以下規則：
1. 極度簡潔：總字數控制在 80 字以內，不說廢話。
2. 格式限制：必須條列式呈現，請用數字 1. 2. 3. 開頭，絕對不要使用 * 或 - 符號。
3. 內容：只提供客觀的賽事與戰力分析。不需要寫任何問候語或結語。"""
        
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
            # 這裡直接用 Python 物理清除星號跟句號
            reply_text = response.text.replace('*', '').replace('。', '')
        except ValueError:
            reply_text = "這個問題裁判吹哨不讓我說！我們來聊聊接下來的賽事預測吧"
            
    except Exception as e:
        reply_text = f"【系統錯誤回報】\n{str(e)}"

    # 【強制綁定引流結語】(保證 100% 精準，不會被 AI 竄改)
    if "【系統錯誤回報】" not in reply_text:
        final_reply = f"{reply_text.strip()}\n\n點擊選單進入社群!目前還有抽獎活動哦"
    else:
        final_reply = reply_text

    # 【純文字無錯發送區】
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=final_reply)
        )
    except Exception as e:
        print(f"發送訊息失敗: {e}")

if __name__ == "__main__":
    app.run()
