"""
In this file we are following the date conventions like as follows:
    for ex:  Start Date (YYYY-MM-DD HH:MM:SS): 2016-03-1 00:00:00
             End Date (YYYY-MM-DD HH:MM:SS): 2016-03-15 23:59:59
End date need to follow the convention of 23:59:59 as hours, minutes and seconds convention to it.
"""
from datetime import timedelta, date
import calendar
import numpy as np
import pandas as pd

from dateutil.parser import parse
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta


def now_local(only_date=False):
    """
    In this method takes only date is true or false. If true means return the date with time (2016-03-15 13:09:08).
    If false means return the date (2016-03-15)
    :param only_date: true / false
    :return: date with time (2016-03-15 13:09:08) and date (2016-03-15)
    """
    if only_date:
        return (timezone.localtime(timezone.now())).date()
    else:
        return timezone.localtime(timezone.now())


def get_boundaries_for_tomorrow_and_day_after_tomorrow():
    """
    :return: tomorrow date (2016-03-16) and day_after_tomorrow (2016-03-17)
    """
    today = timezone.now_local(only_date=True)
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = tomorrow + timedelta(days=1)
    return tomorrow, day_after_tomorrow


def localtime(date_obj):
    """
    :return: return local time ..ie indian standard time
    """
    return timezone.localtime(date_obj)


def get_today_start():
    """
    :return: Start Date (YYYY-MM-DD HH:MM:SS): 2016-03-1 00:00:00
    """
    return now_local().replace(hour=0, minute=0, second=0, microsecond=0)


def get_today_end():
    """
    :return: End Date (YYYY-MM-DD HH:MM:SS): 2016-03-15 23:59:59
    """
    tomorrow = get_today_start() + timedelta(days=1)
    return tomorrow - timedelta(microseconds=1)


def get_day_start(date):
    """
    :return: Start Date (YYYY-MM-DD HH:MM:SS): 2016-03-1 00:00:00
    """
    from datetime import datetime
    date_time = datetime.combine(date, datetime.min.time())
    return date_time.replace(hour=0, minute=0, second=0, microsecond=0)


def get_day_end(date):
    """
    :return: End Date (YYYY-MM-DD HH:MM:SS): 2016-03-15 23:59:59
    """
    from datetime import datetime
    date_time = datetime.combine(date, datetime.min.time())
    return date_time.replace(hour=23, minute=59, second=59, microsecond=0)


def get_yesterday_boundaries():
    """
    :return: Start Date (YYYY-MM-DD HH:MM:SS): 2016-03-1 00:00:00 And End Date (YYYY-MM-DD HH:MM:SS): 2016-03-15 23:59:59
    """
    yesterday_start = get_today_start() - timedelta(days=1)
    yesterday_end = get_today_start() - timedelta(microseconds=1)
    return yesterday_start, yesterday_end


def get_current_month_start():
    """
    It will not take any params. It will returns month start date.
    :return: Month Start Date (YYYY-MM-DD HH:MM:SS): 2016-03-1 00:00:00
    """
    return get_today_start().replace(day=1)


def get_prev_month_boundaries():
    """
    Will return the previous month start date (2016-02-1 00:00:00) and previous month end date (2016-02-29 23:59:59).
    :return: (prev_month_start_date, prev_month_end_date)
    """
    prev_month_end_date = get_current_month_start() - timedelta(microseconds=1)
    if prev_month_end_date:
        prev_month_start_date = prev_month_end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return prev_month_start_date, prev_month_end_date


def get_prev_month_till_today():
    """
    Will return the previous month start date (2016-02-1 00:00:00) and the continuing date of current month as previous month end date
    2016-02-15 23:59:59).
    :return: previous month start date and today date of previous month end date
    """

    prev_month_start_date, prev_month_end_date = get_prev_month_boundaries()
    try:
        #  + datetime.timedelta(days=3) need to remove in next month....
        # import datetime
        prev_month_end_till_date = prev_month_end_date.replace(
            day=get_today_start().day)  # + datetime.timedelta(days=3)
    except ValueError:
        prev_month_end_till_date = prev_month_end_date
    return prev_month_start_date, prev_month_end_till_date


def get_next_60_days_date():
    """
    will return next 60 days date starting form today date
    :return next dates due date from today onwards
    """
    return now_local(only_date=True) + timedelta(days=59)


def get_dates(start_date, end_date=None):
    """
    Will take the start and end date and caluculate the dates and return the dates
    :param start_date, end_date
    :return dict(start_date, end_date)
    """
    try:
        startdate = start_date.date()
        enddate = end_date.date() if end_date else end_date
        date_dict = {
            # Date display
            "start_date": startdate,
            "end_date": enddate,
        }
    except AttributeError:
        date_dict = {
            "start_date": start_date,
            "end_date": end_date
        }
    return date_dict


def get_contest_date(start_date=None, end_date=None):
    from datetime import datetime
    from pytz import timezone
    date_str = "2017-10-01 00:00:01"
    datetime_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    datetime_obj_utc = datetime_obj.replace(tzinfo=timezone('Asia/Kolkata'))
    return datetime_obj_utc


def get_date_format_for_reports_string(date_str):
    """
    It will retunr the Propoer Format Of dates from String
    """
    from datetime import datetime
    from pytz import timezone
    datetime_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    datetime_obj_utc = datetime_obj.replace(tzinfo=timezone('Asia/Kolkata'))
    return datetime_obj_utc


def get_next_prev_year_month_start_end_date():
    """
    will return Prev Year Same Month Start and End date
    :return prev year same month start date , end date
    """
    from calendar import monthrange
    from dateutil.relativedelta import relativedelta
    # monthrange(2011, 2) #  (1, 31)  # (weeks, days)
    prev_year_month_start_date = get_current_month_start() - timedelta(microseconds=-1)
    pre_policy_start_date = prev_year_month_start_date - relativedelta(years=1)
    first_day = pre_policy_start_date.replace(hour=0, minute=0, second=0, microsecond=1)
    get_month_days = monthrange(prev_year_month_start_date.year, prev_year_month_start_date.month)
    days_in_month = get_month_days[1]
    last_day = pre_policy_start_date.replace(day=days_in_month, hour=23, minute=59, second=59, microsecond=1)
    return first_day, last_day


def to_str(dt):
    if not dt:
        return dt
    return dt.isoformat()


def from_str(dt_str):
    if not dt_str:
        return dt_str
    return parse(dt_str)


def get_the_last_date_of_month(date):
    """
    It will take date as a input and return the last day of a month in date format
    Basically Month End
    """
    last_day = calendar.monthrange(date.year, date.month)[1]
    return date.replace(day=last_day)


def subtract_years(date=None, years=1):
    """Return a date that's `years` years ago the date (or datetime)
    object `d`. Return the same calendar date (month and day) in the
    destination year, if it exists, otherwise use the current date to calculate a date an year ago.
    """
    import datetime
    if isinstance(date, datetime.date):
        return date.replace(year=date.year - years)
    else:
        current_datetime = now_local()
        return current_datetime.replace(year=current_datetime.year - years)


def get_current_month_no_of_days():
    import datetime
    now = datetime.datetime.now()
    return calendar.monthrange(now.year, now.month)[1]


def get_date_difference(start_date, end_date=None):
    from dateutil.relativedelta import relativedelta
    from datetime import datetime
    if not end_date:
        end_date = datetime.now()
    else:
        end_date = datetime.combine(end_date, datetime.min.time())
    start_date = datetime.combine(start_date, datetime.min.time())
    difference = relativedelta(end_date, start_date)
    return {'years': difference.years, 'months': difference.months, 'days': difference.days}


def get_month_end_date_and_start_date(month, year=now_local().year):
    start_date = now_local().replace(day=1, year=year, month=month, hour=0, minute=0, second=0, microsecond=0)
    if month == 12:
        end_date = start_date.replace(month=1, year=year + 1) - timedelta(microseconds=1)
    elif month == 1:
        end_date = start_date.replace(day=31, month=month, year=year)
    else:
        end_date = start_date.replace(month=month + 1) - timedelta(microseconds=1)
    return start_date, end_date


def get_back_months_ago(no_of_month):
    return date.today() + relativedelta(months=-no_of_month)


def time_elapsed(end_time, start_time):
    from datetime import datetime
    end_date = datetime.combine(now_local(), end_time)
    start_date = datetime.combine(now_local(), start_time)
    difference = end_date - start_date
    return difference


def all_date_in_daterange(date1, date2):
    x = []
    for n in range(0, int((date2 - date1).days) + 1):
        x.append(date1 + timedelta(n))
    return x


def days_in_date_range(date1, date2, weekdays):
    # Weekdays must be array of weekday's numbers
    all_date = all_date_in_daterange(date1, date2)
    req_date = []
    for dt in all_date:
        if dt.isoweekday() in weekdays:
            req_date.append(dt.strftime("%Y-%m-%d"))
    return req_date


def get_weekday_number_of_a_date_in_month(year, month, day):
    x = np.array(calendar.monthcalendar(year, month))
    weekday_no = np.where(x == day)[0][0] + 1
    return (weekday_no)


def odd_days_in_date_range(date1, date2, weekdays, even=False):
    req_date = []
    all_date = days_in_date_range(date1, date2, weekdays)
    # calender starting from sunday
    calendar.setfirstweekday(6)
    if even:
        for one in all_date:
            one_date = pd.to_datetime(one)
            week_no = get_weekday_number_of_a_date_in_month(one_date.year, one_date.month, one_date.day)
            if week_no % 2 == 0:
                req_date.append(one_date.strftime("%Y-%m-%d"))
    else:
        for one in all_date:
            one_date = pd.to_datetime(one)
            week_no = get_weekday_number_of_a_date_in_month(one_date.year, one_date.month, one_date.day)
            if week_no % 2 == 1:
                req_date.append(one_date.strftime("%Y-%m-%d"))
    return req_date


def get_first_date_of_given_date_range(date1, date2):
    date1 = pd.to_datetime(date1)
    date2 = pd.to_datetime(date2)
    loop = (date2.year - date1.year)*12 + (date2.month - date1.month) + 1
    req_date = []
    from datetime import datetime
    date1 = datetime.combine(date1, datetime.min.time())
    first_date = date1.replace(day=1, month=date1.month, year=date1.year)
    for one in range(loop):
        next_date = first_date + relativedelta(months=one)
        req_date.append(next_date)
    return req_date





