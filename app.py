import os
import google.generativeai as genai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

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
    user_msg = event.message.text.strip()
    
    if "今日新聞報" in user_msg:
        mode = "news"
        system_prompt = """你現在是「泊樂」專屬的體育記者。
你的任務是提供一篇【今日最新的真實足球新聞】。
1. 內容必須詳細深入，生動報導最新賽事動態、球員轉會或內幕。
2. 絕對不要用條列式，必須是流暢的長篇新聞報導格式。
3. 不需要任何問候語或結語。"""
    elif "當日賽事推薦" in user_msg:
        mode = "bet"
        system_prompt = """你現在是「泊樂」專屬的獨立代理運彩分析師。
你的任務是提供一場【當日隨機足球賽事推薦】。
1. 極度簡短：總字數嚴格控制在 80 字以內。
2. 格式：
賽事：(哪隊 vs 哪隊)
推薦下注：(例如主勝、大分、讓分)
理由：(一句話帶過)
3. 絕對不要使用 * 或 - 符號。不需要任何問候語或結語。"""
    else:
        return 
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
        
        response = model.generate_content(
            f"{system_prompt}\n\n用戶要求：{user_msg}",
            safety_settings=safety_settings
        )
        
        try:
            if mode == "bet":
                reply_text = response.text.replace('*', '').replace('。', '')
            else:
                reply_text = response.text.replace('*', '')
        except ValueError:
            reply_text = "這個問題裁判吹哨不讓我說！我們來聊聊接下來的賽事預測吧"
            
    except Exception as e:
        # 將真實錯誤紀錄在系統後台，不要讓客人看到
        print(f"系統錯誤: {str(e)}")
        # 覆寫傳給客人的罐頭安撫訊息
        reply_text = "請稍等1~3分鐘再嘗試 目前詢問人數過多"

    # 如果是因為人太多跳出的罐頭訊息，就不硬塞活動廣告；正常回覆才會加上廣告詞
    if "請稍等1~3分鐘再嘗試" not in reply_text:
        final_reply = f"{reply_text.strip()}\n\n點擊選單進入社群!目前還有抽獎活動哦"
    else:
        final_reply = reply_text

    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=final_reply)
        )
    except Exception as e:
        print(f"發送訊息失敗: {e}")

if __name__ == "__main__":
    app.run()
