from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage
import os
from holiday import is_tomorrow_workday

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
USER_ID = os.getenv("USER_ID")

def send_reminder():
    if is_tomorrow_workday():
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)

        msg = f"""
📢 明日回報提醒

📅 日期：{tomorrow}

請準備：
1️⃣ 今日完成事項
2️⃣ 遇到問題
3️⃣ 明日計畫
4️⃣ 是否需要支援

請提前準備 ✅
"""
        line_bot_api.push_message(USER_ID, TextSendMessage(text=msg))
        print("✅ 已發送提醒")
    else:
        print("⛔ 明天是假日，不發送")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Taipei'))

    # 每天下午 15:00 執行
    scheduler.add_job(send_reminder, 'cron', hour=16, minute=0)

    scheduler.start()
