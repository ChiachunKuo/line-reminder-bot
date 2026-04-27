from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage
import os
from holiday import is_tomorrow_workday
from storage import get_all

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))

def send_reminder():
    if not is_tomorrow_workday():
        print("⛔ 明天是假日，不發送")
        return

    data = get_all()
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    msg = f""" 明日是否在營及事故回報：
造賓：
佳真：受訓
宗旂：
培昇：
季家：
佳峻：
彥呈：
欣雯："""

    # 發送給所有好友
    for user in data["users"]:
        try:
            line_bot_api.push_message(user, TextSendMessage(text=msg))
        except:
            pass

    # 發送給所有群組
    for group in data["groups"]:
        try:
            line_bot_api.push_message(group, TextSendMessage(text=msg))
        except:
            pass

    print("✅ 已發送全部")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Taipei'))
    scheduler.add_job(send_reminder, 'cron', hour=21, minute=00)
    scheduler.start()
