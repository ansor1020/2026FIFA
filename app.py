import os
import google.generativeai as genai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 強制清除 Render 抓取環境變數時，頭尾可能隱藏的空白鍵
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
        # 恢復標準模型寫法
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        system_prompt = """你現在是「2026美加墨世界盃聊天社群」的專屬 AI 助理。
你的任務是：
1. 提供專業、客觀的足球賽事分析、球隊戰力數據與世足歷史。
2. 熱情地與球迷互動，並在對話中自然地引導他們加入我們的「世界盃私密討論社群」"""
        
        response = model.generate_content(f"{system_prompt}\n\n用戶說：{user_msg}")
        reply_text = response.text
        
    except Exception as e:
        # 如果還是失敗，直接把系統真實死因傳到你的 LINE 手機畫面上
        reply_text = f"【系統錯誤回報】\n{str(e)}\n\n(提示：若仍是 404 錯誤，請確認金鑰是否為 Google AI Studio 申請，而非其他服務平台)"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run()
