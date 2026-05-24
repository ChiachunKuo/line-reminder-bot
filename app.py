from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError

import os
import datetime
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
# 資料檔案
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

    # 若 members 不存在
    if "members" not in data:

        data["members"] = default_members

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
# 台灣假日判斷
# =====================
tw_holidays = holidays.Taiwan()

def is_tomorrow_workday():

    tomorrow = (
        datetime.date.today()
        + datetime.timedelta(days=1)
    )

    # 六日
    if tomorrow.weekday() >= 5:
        return False

    # 國定假日
    if tomorrow in tw_holidays:
        return False

    return True

# =====================
# 每日清空非排程資料
# 並判斷排程是否到期
# =====================
def refresh_daily_status():

    data = load_data()

    tomorrow = (
        datetime.date.today()
        + datetime.timedelta(days=1)
    )

    for name, info in data["members"].items():

        expire = info.get("expire", "")

        # =====================
        # 沒有排程 → 每天清空
        # =====================
        if expire == "":

            data["members"][name]["text"] = ""

            continue

        try:

            expire_date = datetime.datetime.strptime(
                expire,
                "%Y/%m/%d"
            ).date()

            # =====================
            # 重點修正
            # 前一天回報要清空
            #
            # 例如：
            # 休假至5/25
            # 5/24回報明日(5/25)時
            # 就不能再顯示
            # =====================
            if tomorrow >= expire_date:

                data["members"][name]["text"] = ""
                data["members"][name]["expire"] = ""

        except:

            data["members"][name]["text"] = ""
            data["members"][name]["expire"] = ""

    save_data(data)

# =====================
# 發送每日提醒
# =====================
def send_job():

    # 判斷明日是否工作日
    if not is_tomorrow_workday():

        print("⛔ 明日是假日，不發送")

        return

    # 每日刷新狀態
    refresh_daily_status()

    data = load_data()

    # =====================
    # 組合訊息
    # =====================
    msg = "明日是否在營及事故回報：\n"

    for name, info in data["members"].items():

        text = info.get("text", "")

        msg += f"\n{name}：{text}"

    # =====================
    # 發送好友
    # =====================
    for user in data["users"]:

        try:

            line_bot_api.push_message(
                user,
                TextSendMessage(text=msg)
            )

        except Exception as e:

            print("User Error:", e)

    # =====================
    # 發送群組
    # =====================
    for group in data["groups"]:

        try:

            line_bot_api.push_message(
                group,
                TextSendMessage(text=msg)
            )

        except Exception as e:

            print("Group Error:", e)

    print("✅ 發送成功")

# =====================
# 首頁
# =====================
@app.route("/")
def home():

    return "OK", 200

# =====================
# 外部喚醒
# =====================
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
# 接收 LINE 訊息
# =====================
@handler.add(
    MessageEvent,
    message=TextMessage
)
def handle_message(event):

    text = event.message.text.strip()

    # =====================
    # 自動記錄好友/群組
    # =====================
    if event.source.type == "user":

        add_user(event.source.user_id)

    elif event.source.type == "group":

        add_group(event.source.group_id)

    data = load_data()

    # =====================
    # 格式：
    # 佳峻：5/20休假至5/25
    # =====================
    match = re.match(
        r"(.+?)：(.+)",
        text
    )

    if match:

        name = match.group(1).strip()

        content = match.group(2).strip()

        # 不在名單內
        if name not in data["members"]:

            return

        # =====================
        # 抓取日期
        # 至5/25
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

        # 更新資料
        data["members"][name]["text"] = content

        data["members"][name]["expire"] = expire

        save_data(data)

        # 回覆
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
