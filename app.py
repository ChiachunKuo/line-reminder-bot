from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import os
import datetime

from storage import add_user, add_group, get_all
from holiday import is_tomorrow_workday

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# =====================
# 基本路由（喚醒用）
# =====================
@app.route("/")
def home():
    return "OK", 200

# =====================
# 🔥 cron-job 觸發點
# =====================
@app.route("/trigger")
def trigger():
    if not is_tomorrow_workday():
        return "Tomorrow is holiday", 200

    data = get_all()
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    msg = f"""明日是否在營及事故回報：
造賓：
佳真：受訓
宗旂：
培昇：
季家：
佳峻：
彥呈：
欣雯："""

    # 發送給好友
    for user in data["users"]:
        try:
            line_bot_api.push_message(user, TextSendMessage(text=msg))
        except Exception as e:
            print("User error:", e)

    # 發送給群組
    for group in data["groups"]:
        try:
            line_bot_api.push_message(group, TextSendMessage(text=msg))
        except Exception as e:
            print("Group error:", e)

    return "Sent", 200

# =====================
# LINE Webhook
# =====================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# =====================
# 自動記錄 ID
# =====================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.source.type == "user":
        add_user(event.source.user_id)

    elif event.source.type == "group":
        add_group(event.source.group_id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
