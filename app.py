from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage
from linebot.exceptions import InvalidSignatureError
import os
from scheduler import start_scheduler
from storage import add_user, add_group

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/")
def home():
    return "Bot is running"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 🔥 自動記錄 ID
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.source.type == "user":
        add_user(event.source.user_id)

    elif event.source.type == "group":
        add_group(event.source.group_id)

# 啟動排程
start_scheduler()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
