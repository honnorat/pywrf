#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pywrf.util.files as puf
import pywrf.util.dates as pud

from collections import OrderedDict
from .namelist import Namelist
from pywrf.util import ConfigStore
from pywrf.util.logger import get_logger

_thisdir = os.path.dirname(__file__)
_namelist_wps_template = os.path.join(_thisdir, "namelist.wps_template")

log = get_logger("pywrf")

class WPSNamelist(Namelist):

    def __init__(self, config=None):

        if config is None:
            config = ConfigStore()

        # Fetch template file for namelist
        try:
            wps_template = puf.expand_path(config["nml_wps_template"])
            log.warning("OK, I use '{}'.".format(config.get("nml_wps_template")))
        except:
            log.warning("could not find configuration file '{}'. I'll use '{}' instead."
                        .format(config.get("nml_wps_template"), _namelist_wps_template))
            wps_template = _namelist_wps_template

        super(WPSNamelist, self).__init__(config, wps_template)

    def calc_values(self):

        super(WPSNamelist, self).calc_values()

        nd = self.max_dom

        # Section '&share'
        share = self.section("share")
        share["wrf_core"]         = "ARW"
        share["max_dom"]          = nd
        share["start_date"]       = nd * [ pud.format_date(self.date_s) ]
        share["end_date"]         = nd * [ pud.format_date(self.date_e) ]
        share["interval_seconds"] = self.from_config("interval_seconds", 10800)

        # Section '&geogrid'
        geogrid = self.section("geogrid")
        geogrid["parent_id"]         = self.from_config("parent_id",         list(range(nd)))
        geogrid["parent_grid_ratio"] = self.from_config("parent_grid_ratio", [1] + (nd-1)*[3])
        geogrid["i_parent_start"]    = self.from_config("i_parent_start",    [1] + (nd-1)*[10])
        geogrid["j_parent_start"]    = self.from_config("j_parent_start",    [1] + (nd-1)*[10])
        geogrid["e_we"]              = self.from_config("e_we",              [70] + (nd-1)*[88])
        geogrid["e_sn"]              = self.from_config("e_sn",              [70] + (nd-1)*[88])
        geogrid["dx"]                = self.from_config("dx",                27000)
        geogrid["dy"]                = self.from_config("dy",                27000)
        geogrid["geog_data_res"]     = self.from_config("geog_data_res",     ["10m", "5m", "2m", "30s"][:nd])
        geogrid["map_proj"]          = self.from_config("map_proj", "mercator")
        geogrid["ref_lat"]           = self.from_config("ref_lat", 0.)
        geogrid["ref_lon"]           = self.from_config("ref_lon", 0.)
        geogrid["truelat1"]          = self.from_config("truelat1", geogrid["ref_lat"])
        geogrid["truelat2"]          = self.from_config("truelat2", geogrid["truelat1"])
        geogrid["stand_lon"]         = self.from_config("stand_lon", geogrid["ref_lon"])
        geogrid["geog_data_path"]       = os.path.expanduser(self.from_config("geog_data_path", "."))
        geogrid["opt_geogrid_tbl_path"] = os.path.expanduser(self.from_config("opt_geogrid_tbl_path", "."))

        # Section '&ungrib'
        ungrib = self.section("ungrib")
        ungrib["out_format"] = "WPS"
        ungrib["prefix"]     = self.from_config("ungrib_prefix", self.from_config("data_type", "GFS"))

        # Section '&metgrid'
        metgrid = self.section("metgrid")
        metgrid["fg_name"]              = self.from_config("list_ungrib_prefixes")
        metgrid["opt_metgrid_tbl_path"] = os.path.expanduser(self.from_config("opt_metgrid_tbl_path", "."))

        # Update namelist with extra keywords
        self.update_with_extra("namelist_wps")
