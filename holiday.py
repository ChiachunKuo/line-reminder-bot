import holidays
import datetime

tw_holidays = holidays.Taiwan()

def is_tomorrow_workday():
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    # 週末
    if tomorrow.weekday() >= 5:
        return False

    # 國定假日
    if tomorrow in tw_holidays:
        return False

    return True
