#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import pytest
import sys

sys.path.insert(1, '../')

import pywrf.util.dates as pud


class TestReadDate:

    def test_read_datetime(self):
        d = datetime.datetime(2000, 1, 1)
        assert pud.read_date(d) == d

    def test_read_simple(self):
        d = pud.read_date("2015-01-01")
        assert d.date() == datetime.date(2015, 1, 1)
        assert d.time() == datetime.time(0, 0)

    def test_read_wrf(self):
        d = pud.read_date("2015-01-01_12:13:14")
        assert d.date() == datetime.date(2015, 1, 1)
        assert d.time() == datetime.time(12, 13, 14)

    def test_read_leap_year(self):
        pud.read_date("2012-02-29")
        with pytest.raises(ValueError):
            pud.read_date("2013-02-29")

    def test_read_date_time_1(self):
        d = pud.read_date("200001", "12")
        assert d.date() == datetime.date(2000, 1, 1)
        assert d.time() == datetime.time(12, 0)

    def test_read_date_time_2(self):
        d = pud.read_date("2000-01-01T00:00:00", "12:13:14")
        assert d.date() == datetime.date(2000, 1, 1)
        assert d.time() == datetime.time(12, 13, 14)

    def test_read_date_time_3(self):
        d = pud.read_date("2000-01-01_12:13")
        assert d.date() == datetime.date(2000, 1, 1)
        assert d.time() == datetime.time(12, 13, 0)

    def test_read_bad_date(self):
        with pytest.raises(ValueError) as e:
            pud.read_date("201001-01")
        assert str(e.value).startswith("Unknown date format")

    def test_read_bad_time(self):
        with pytest.raises(ValueError) as e:
            pud.read_date("20100101_100100")
        assert str(e.value).startswith("Unknown hour format")


class TestFormatDate:

    def test_format_default(self):
        assert pud.format_date("201501") == "2015-01-01_00:00:00"

    def test_format_short(self):
        assert pud.format_date("1999-01-01", "short") == "1999010100"

    def test_format_long(self):
        assert pud.format_date("1999-01-01", "long") == "1999-01-01_00:00:00"

    def test_format_wrf(self):
        assert pud.format_date("1999-01-01", "wrf") == "1999-01-01_00:00:00"

    def test_format_iso(self):
        assert pud.format_date("1999-01-01", "ISO") == "1999-01-01T00:00:00Z"

    def test_format_cfsr(self):
        assert pud.format_date("1999-01-01", "cfsr") == "1999-01-01 00:00"

    def test_format_fnl(self):
        assert pud.format_date("1999-01-01", "fnl") == "fnl_19990101_00_00"

    def test_format_fnl_dir(self):
        assert pud.format_date("1999-01-01", "fnl_dir") == "grib2/1999/1999.01/fnl_19990101_00_00"

    def test_format_gfs(self):
        assert pud.format_date("1999-01-01", "GFS") == "GFS:1999-01-01_00"
        assert pud.format_date("19990101 12:13:14", "GFS") == "GFS:1999-01-01_12"


class TestAdvanceDate:

    def test_advance_dummy(self):
        d = datetime.datetime(1999, 1, 1)
        assert pud.advance_date(d) == d

    def test_advance_hour(self):
        assert pud.advance_date(datetime.datetime(1999, 1, 1), 0, 1) == pud.read_date("1999-01-01T01:00:00")

    def test_advance_day(self):
        assert pud.advance_date(datetime.datetime(1999, 12, 31, 18), 0, 6) == pud.read_date("20000101")

    def test_advance_back_one_day(self):
        assert pud.advance_date("2000-01-01", -1) == pud.read_date("1999-12-31")
        assert pud.advance_date("2004-03-01", -1) == pud.read_date("2004-02-29")
        assert pud.advance_date("2000-03-01", -1) == pud.read_date("2000-02-29")
        assert pud.advance_date("2100-03-01", -1) == pud.read_date("2100-02-28")


class TestRangeDates:

    def test_range_day(self):
        l = pud.range_dates("1999-12-30", "2000-01-02", increment_d=1)
        assert next(l).date() == datetime.date(1999, 12, 30)
        assert next(l).date() == datetime.date(1999, 12, 31)
        assert next(l).date() == datetime.date(2000, 1, 1)

    def test_range_hour(self):
        l = pud.range_dates("1999123122", "2000-01-01 01:00", increment_h=1)
        d = next(l)
        assert d.date() == datetime.date(1999, 12, 31)
        assert d.time() == datetime.time(22)
        d = next(l)
        assert d.date() == datetime.date(1999, 12, 31)
        assert d.time() == datetime.time(23)
        d = next(l)
        assert d.date() == datetime.date(2000, 1, 1)
        assert d.time() == datetime.time(0)
        d = next(l)
        assert d.date() == datetime.date(2000, 1, 1)
        assert d.time() == datetime.time(1)
        with pytest.raises(StopIteration):
            next(l)
