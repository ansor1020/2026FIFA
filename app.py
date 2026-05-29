import os
import google.generativeai as genai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 系統會自動從雲端後台讀取你剛剛存下來的三把鑰匙
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

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
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 【核心人設與大腦洗腦區】
    system_prompt = f"""
    你現在是「2026美加墨世界盃聊天社群」的專屬 AI 助理。
    你的任務是：
    1. 提供專業、客觀的足球賽事分析、球隊戰力數據與世足歷史。
    2. 熱情地與球迷互動，並在對話中自然地引導他們加入我們的「世界盃私密討論社群」。
    3. 最高禁令：絕對不可以提到「泊樂」、「娛樂城」、「博奕」、「下注」、「盤口」等任何與賭博相關的字眼。
    4. 語氣要像一個熱愛足球的專業球評兼社群管理員，親切且專業。

    球迷的訊息是：{user_msg}

    請根據以上設定，用自然、繁體中文回答這位球迷：
    """
    
    # 把問題丟給 Gemini
    response = model.generate_content(system_prompt)
    
    # 將 Gemini 的回答傳回給 LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response.text)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
