from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError

import os
import datetime
import threading
import holidays
import json
import re

app = Flask(__name__)

# =====================
# LINE BOT 設定
# =====================
line_bot_api = LineBotApi(
    os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
)

handler = WebhookHandler(
    os.getenv("LINE_CHANNEL_SECRET")
)

# =====================
# 檔案名稱
# =====================
FILE = "data.json"

# =====================
# 固定人員名單
# =====================
DEFAULT_MEMBERS = [
    "造賓",
    "佳真",
    "宗旂",
    "培昇",
    "季家",
    "佳峻",
    "彥呈",
    "欣雯"
]

# =====================
# 資料處理
# =====================
def load_data():

    members_data = {}

    for name in DEFAULT_MEMBERS:

        members_data[name] = {
            "text": "",
            "expire": ""
        }

    if not os.path.exists(FILE):

        return {
            "users": [],
            "groups": [],
            "last_sent": "",
            "members": members_data
        }

    with open(FILE, "r", encoding="utf-8") as f:

        data = json.load(f)

    # 新增新成員
    for name in DEFAULT_MEMBERS:

        if name not in data["members"]:

            data["members"][name] = {
                "text": "",
                "expire": ""
            }

    # 移除舊成員
    remove_list = []

    for name in data["members"]:

        if name not in DEFAULT_MEMBERS:

            remove_list.append(name)

    for name in remove_list:

        del data["members"][name]

    save_data(data)

    return data

# =====================
# 儲存資料
# =====================
def save_data(data):

    with open(FILE, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

# =====================
# 記錄好友
# =====================
def add_user(user_id):

    data = load_data()

    if user_id not in data["users"]:

        data["users"].append(user_id)

    save_data(data)

# =====================
# 記錄群組
# =====================
def add_group(group_id):

    data = load_data()

    if group_id not in data["groups"]:

        data["groups"].append(group_id)

    save_data(data)

# =====================
# 台灣假日
# =====================
tw_holidays = holidays.Taiwan()

def is_tomorrow_workday():

    tomorrow = (
        datetime.date.today()
        + datetime.timedelta(days=1)
    )

    if tomorrow.weekday() >= 5:
        return False

    if tomorrow in tw_holidays:
        return False

    return True

# =====================
# 清除過期資料
# =====================
def clear_expired():

    data = load_data()

    today = datetime.date.today()

    for name, info in data["members"].items():

        expire = info.get("expire", "")

        if expire:

            try:

                expire_date = datetime.datetime.strptime(
                    expire,
                    "%Y/%m/%d"
                ).date()

                if today > expire_date:

                    data["members"][name]["text"] = ""
                    data["members"][name]["expire"] = ""

            except:
                pass

    save_data(data)

# =====================
# 發送每日提醒
# =====================
def send_job():

    clear_expired()

    data = load_data()

    today_str = str(datetime.date.today())

    # 防重複
    if data.get("last_sent") == today_str:
        return

    # 工作日判斷
    if not is_tomorrow_workday():
        return

    msg = "明日是否在營及事故回報：\n\n"

    for name, info in data["members"].items():

        text = info.get("text", "")

        msg += f"{name}：{text}\n"

    # 發送好友
    for user in data["users"]:

        try:

            line_bot_api.push_message(
                user,
                TextSendMessage(text=msg)
            )

        except:
            pass

    # 發送群組
    for group in data["groups"]:

        try:

            line_bot_api.push_message(
                group,
                TextSendMessage(text=msg)
            )

        except:
            pass

    data["last_sent"] = today_str

    save_data(data)

# =====================
# Render 喚醒
# =====================
@app.route("/")
def home():

    return "OK", 200

# =====================
# cron-job 觸發
# =====================
@app.route("/trigger")
def trigger():

    try:

        send_job()

        return "success", 200

    except Exception as e:

        return str(e), 500

# =====================
# LINE Webhook
# =====================
@app.route("/callback", methods=['POST'])
def callback():

    signature = request.headers.get(
        'X-Line-Signature'
    )

    body = request.get_data(
        as_text=True
    )

    try:

        handler.handle(
            body,
            signature
        )

    except InvalidSignatureError:

        abort(400)

    return 'OK'

# =====================
# 接收訊息
# =====================
@handler.add(
    MessageEvent,
    message=TextMessage
)
def handle_message(event):

    text = event.message.text.strip()

    # 自動記錄好友/群組
    if event.source.type == "user":

        add_user(event.source.user_id)

    elif event.source.type == "group":

        add_group(event.source.group_id)

    data = load_data()

    # 格式：
    # 王小明：5/25休假至6/1
    match = re.match(
        r"(.+?)：(.+)",
        text
    )

    if match:

        name = match.group(1).strip()

        content = match.group(2).strip()

        if name not in data["members"]:

            return

        # 抓取日期
        date_match = re.search(
            r"至(\d{1,2})/(\d{1,2})",
            content
        )

        expire = ""

        if date_match:

            month = int(date_match.group(1))
            day = int(date_match.group(2))

            year = datetime.date.today().year

            expire = (
                f"{year}/{month:02d}/{day:02d}"
            )

        data["members"][name]["text"] = content

        data["members"][name]["expire"] = expire

        save_data(data)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"✅ 已更新 {name}"
            )
        )

# =====================
# 啟動 Flask
# =====================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
