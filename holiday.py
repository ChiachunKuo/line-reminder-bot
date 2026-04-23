import holidays
import datetime

tw_holidays = holidays.Taiwan()

def is_tomorrow_workday():
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    if tomorrow.weekday() >= 5:
        return False

    if tomorrow in tw_holidays:
        return False

    return True
