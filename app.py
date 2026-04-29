from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import os
import datetime
import threading
import holidays
import json

app = Flask(__name__)

# =====================
# LINE 設定
# =====================
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# =====================
# 資料儲存
# =====================
FILE = "data.json"

def load_data():
    if not os.path.exists(FILE):
        return {"users": [], "groups": []}
    with open(FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(FILE, "w") as f:
        json.dump(data, f)

def add_user(user_id):
    data = load_data()
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)

def add_group(group_id):
    data = load_data()
    if group_id not in data["groups"]:
        data["groups"].append(group_id)
        save_data(data)

# =====================
# 台灣假日判斷
# =====================
tw_holidays = holidays.Taiwan()

def is_tomorrow_workday():
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    if tomorrow.weekday() >= 5:
        return False

    if tomorrow in tw_holidays:
        return False

    return True

# =====================
# 發送任務（背景執行）
# =====================
def send_job():
    if not is_tomorrow_workday():
        print("⛔ 明天是假日，不發送")
        return

    data = load_data()
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

    print("✅ 發送完成")

# =====================
# 基本喚醒（超輕量）
# =====================
@app.route("/")
def home():
    return "OK", 200

@app.route("/wake")
def wake():
    return "awake", 200

# =====================
# 🔥 cron-job 觸發點
# =====================
@app.route("/trigger")
def trigger():
    # 👉 背景執行（避免 timeout / 503）
    threading.Thread(target=send_job).start()
    return "triggered", 200

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

# =====================
# 啟動
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
