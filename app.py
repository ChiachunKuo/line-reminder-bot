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
# LINE 設定
# =====================
line_bot_api = LineBotApi(
    os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
)

handler = WebhookHandler(
    os.getenv("LINE_CHANNEL_SECRET")
)

# =====================
# 資料儲存
# =====================
FILE = "data.json"

# =====================
# 固定名單
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
# 讀取資料
# =====================
def load_data():

    default_members = {}

    for name in DEFAULT_MEMBERS:

        default_members[name] = {
            "text": "",
            "expire": ""
        }

    # 第一次建立
    if not os.path.exists(FILE):

        return {
            "users": [],
            "groups": [],
            "members": default_members
        }

    with open(FILE, "r", encoding="utf-8") as f:

        data = json.load(f)

    # 新增不存在成員
    if "members" not in data:

        data["members"] = default_members

    for name in DEFAULT_MEMBERS:

        if name not in data["members"]:

            data["members"][name] = {
                "text": "",
                "expire": ""
            }

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
# 台灣假日判斷
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

                # 日期已過
                if today > expire_date:

                    data["members"][name]["text"] = ""
                    data["members"][name]["expire"] = ""

            except:
                pass

    save_data(data)

# =====================
# 發送任務
# =====================
def send_job():

    if not is_tomorrow_workday():

        print("⛔ 明天是假日，不發送")

        return

    # 清除過期
    clear_expired()

    data = load_data()

    msg = "明日是否在營及事故回報：\n"

    for name, info in data["members"].items():

        text = info.get("text", "")

        msg += f"\n{name}：{text}"

    # 發送好友
    for user in data["users"]:

        try:

            line_bot_api.push_message(
                user,
                TextSendMessage(text=msg)
            )

        except Exception as e:

            print("User error:", e)

    # 發送群組
    for group in data["groups"]:

        try:

            line_bot_api.push_message(
                group,
                TextSendMessage(text=msg)
            )

        except Exception as e:

            print("Group error:", e)

    print("✅ 發送完成")

# =====================
# 基本喚醒
# =====================
@app.route("/")
def home():

    return "OK", 200

@app.route("/wake")
def wake():

    return "awake", 200

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

    # 自動記錄 ID
    if event.source.type == "user":

        add_user(event.source.user_id)

    elif event.source.type == "group":

        add_group(event.source.group_id)

    data = load_data()

    # =====================
    # 格式：
    # 佳峻：5/25休假至6/1
    # =====================
    match = re.match(
        r"(.+?)：(.+)",
        text
    )

    if match:

        name = match.group(1).strip()

        content = match.group(2).strip()

        # 非固定名單不更新
        if name not in data["members"]:

            return

        # =====================
        # 抓取日期
        # 至6/1
        # =====================
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

        # 更新
        data["members"][name]["text"] = content

        data["members"][name]["expire"] = expire

        save_data(data)

        # 回覆成功
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"✅ 已更新 {name}"
            )
        )

# =====================
# 啟動
# =====================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
