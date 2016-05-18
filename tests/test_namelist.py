#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import pytest
import shutil
import sys
import tempfile
sys.path.insert(1, '..')

import pywrf
from pywrf.namelist import WPSNamelist
from pywrf.util import ConfigStore


def create_conf(ndom=1):
    conf = ConfigStore()
    conf["date_s"] = "2015-01-01"
    conf["date_e"] = "20150101_12"
    conf["interval_seconds"] = 3600
    conf["max_dom"] = ndom
    return conf


class TestWPSNamelist:

    def test_default(self):
        nml = WPSNamelist()
        nml.calc_values()
        assert nml["share"] is not None
        assert nml["geogrid"] is not None
        assert nml["ungrib"] is not None
        assert nml["metgrid"] is not None

    def test_fail(self):
        nml = WPSNamelist()
        nml.calc_values()
        assert "share" in nml
        assert "not_here" not in nml
        assert len(nml.section("iam_here")) == 0    # Actually creates the section
        assert "iam_here" in nml
        with pytest.raises(KeyError):
            assert nml["still_not_here"] is None

    def test_share(self):
        nml = WPSNamelist(create_conf())
        nml.calc_values()
        share = nml["share"]
        assert share["wrf_core"] == "ARW"
        assert share["start_date"] == ["2015-01-01_00:00:00"]
        assert share["end_date"] == ["2015-01-01_12:00:00"]
        assert share["interval_seconds"] == 3600

    def test_share_2doms(self):
        nml = WPSNamelist(create_conf(2))
        nml.calc_values()
        share = nml["share"]
        assert share["wrf_core"] == "ARW"
        assert share["start_date"] == 2*["2015-01-01_00:00:00"]
        assert share["end_date"] == 2*["2015-01-01_12:00:00"]
        assert share["interval_seconds"] == 3600

    def test_geogrid(self):
        conf = create_conf(3)
        conf["dx"] = 25000
        nml = WPSNamelist(conf)
        nml.calc_values()
        geogrid = nml["geogrid"]
        assert geogrid["parent_id"] == list(range(3))
        assert geogrid["dx"] == 25000

    def test_wps_extras(self):
        conf = ConfigStore(io.StringIO("""
        namelist_wps:
            geogrid:
                extra : unused """))
        nml = WPSNamelist(conf)
        nml.calc_values()
        geogrid = nml["geogrid"]
        assert geogrid["extra"] == "unused"

    def test_write(self):
        nml = WPSNamelist()
        nml.calc_values()
        try:
            dir = tempfile.mkdtemp()
            nml.write(os.path.join(dir, "tmp.nml.txt"))
        finally:
            shutil.rmtree(dir)

