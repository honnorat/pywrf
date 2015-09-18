#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import datetime, timedelta

DATE_FORMATS = {
    "short":   "%Y%m%d%H",
    "long":    "%Y-%m-%d_%H:%M:%S",
    "wrf":     "%Y-%m-%d_%H:%M:%S",
    "ISO":     "%Y-%m-%dT%H:%M:%SZ",
    "cfsr":    "%Y-%m-%d %H:00",
    "fnl":     "fnl_%Y%m%d_%H_00",
    "fnl_dir": "grib2/%Y/%Y.%m/fnl_%Y%m%d_%H_00",
    "GFS":     "GFS:%Y-%m-%d_%H"
}


def _to_int(strlist):
    return [int(x) for x in strlist]


def read_date(date_str, hour_str=None):
    """
    Accepted formats
    - for date_str :
    1. YYYY-MM-DD_HH:MM:SS where '_' can also be ' ' or 'T'
    2. YYYY-MM-DD          where '-' can also be '/'
    3. YYYYMMDD
    4. YYYYMMDDHH
    - for  hour_str :
    1. HH:MM:SS
    2. HH:MM
    3. HH
    """
    if isinstance(date_str, datetime):
        return date_str

    date_str = date_str.strip()

    if len(date_str) > 10:          # date_str = YYYY-MM-DD_HH:MM:SS
        date_str, _hour_str = re.split("[ _T]", date_str)
        if hour_str is None:
            hour_str = _hour_str

    datelen = len(date_str)

    if hour_str is None:
        hour, minute, second = 0, 0, 0
    elif len(hour_str) == 8:        # hour_str = HH:MM:SS
        hour, minute, second = _to_int(hour_str.split(":"))
    elif len(hour_str) == 5:        # hour_str = HH:MM
        (hour, minute), second = _to_int(hour_str.split(":")), 0
    elif len(hour_str) == 2:        # hour_str = HH
        hour, minute, second = int(hour_str), 0, 0
    else:
        raise ValueError("Unknown hour format : {}".format(date_str))

    if datelen == 6:                # date_str = YYYYMM
        year  = int(date_str[0:4])
        month = int(date_str[4:6])
        day   = 1
    elif datelen == 8:              # date_str = YYYYMMDD
        year  = int(date_str[0:4])
        month = int(date_str[4:6])
        day   = int(date_str[6:8])
    elif datelen == 10:             # date_str = YYYY-MM-DD or YYYYMMDDHH
        try:
            year, month, day = _to_int(re.split("[- /]", date_str))
        except ValueError:
            year  = int(date_str[0:4])
            month = int(date_str[4:6])
            day   = int(date_str[6:8])
            hour  = int(date_str[8:10])
    else:
        raise ValueError("Unknown date format : {}".format(date_str))

    return datetime(year, month, day, hour, minute, second)


def format_date(date, type="long"):

    date = read_date(date)
    return date.strftime(DATE_FORMATS[type])


def advance_date(date, increment_d=0, increment_h=0, increment_m=0, increment_s=0):

    date = read_date(date)

    if isinstance(increment_d, str):
        increment_d = float(increment_d)
    if isinstance(increment_h, str):
        increment_h = float(increment_h)
    if isinstance(increment_m, str):
        increment_m = float(increment_m)
    if isinstance(increment_s, str):
        increment_s = float(increment_s)

    date += timedelta(days=increment_d, hours=increment_h, minutes=increment_m, seconds=increment_s)

    return date


def range_dates(date_s, date_e, increment_d=0, increment_h=0, increment_m=0, increment_s=0):

    while format_date(date_s) <= format_date(date_e):
        yield read_date(date_s)
        date_s = advance_date(date_s, increment_d, increment_h, increment_m, increment_s)


def test_dates():

    import sys

    args = sys.argv[1:]
    if len(args) == 2:
        date_i, hour_i = args
    elif len(args) == 1:
        date_i, hour_i = args[0], None
    else:
        print("usage: {} DATE_STR".format(sys.argv[0]) + """\n
    where DATE_STR can have the following format:
     . YYYY-MM-DD_HH:MM:SS
     . YYYY-MM-DD
     . YYYYMMDD
     . YYYYMMDDHH """)
        return

    print("date_input = |{}|".format(date_i))
    print("hour_input = |{}|".format(hour_i))

    date_r = read_date(date_i, hour_i)
    print("date read  = ", date_r)
    print("date wrf   = ", format_date(date_r, "wrf"))
    print("date long  = ", format_date(date_r, "long"))
    print("date short = ", format_date(date_r, "short"))
    print("date fnl   = ", format_date(date_r, "fnl"))
    print("---")

    print("date_i incr 0 = ", format_date(advance_date(date_i)))
    print("date_r incr 0 = ", format_date(advance_date(date_r)))
    print("date_r -1d    = ", format_date(advance_date(date_r, increment_d="-1")))
    print("date_r +1.5d  = ", format_date(advance_date(date_r, increment_d=1.5)))
    print("date_r +10s   = ", format_date(advance_date(date_r, increment_s=-10)))
    print("date_r +10s   = ", format_date(advance_date(date_r, increment_s=10)))
    print("---")

    print("date_r + 3610s = ", format_date(advance_date(date_r, increment_s=3610)))
    print("date_r - 3610s = ", format_date(advance_date(date_r, increment_s=-3610)))

if __name__ == "__main__":

    test_dates()
