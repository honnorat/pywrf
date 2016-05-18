#!/usr/bin/env python
# -*- coding: utf-8 -*-

from f90nml import read as read_f90nml
from f90nml.namelist import Namelist as NmlDict
from f90nml.parser import merge_dicts

from pywrf.util.config import ConfigStore
from collections import OrderedDict

import pywrf.util.dates as pud


class Namelist(object):

    def __init__(self, config=None, template=None):

        if config is None:
            config = ConfigStore()

        self._config = config
        self._values = OrderedDict()
        self._template = template

    def __contains__(self, index):
        return self._values.__contains__(index)

    def __delitem__(self, key):
        return self._values.__delitem__(key)

    def __getitem__(self, index):
        return self._values.__getitem__(index)

    def __setitem__(self, index, data):
        self._values.__setitem__(index, data)

    def section(self, section_name):

        if section_name not in self._values:
            # If the required section doesn't exist yet, just create it.
            self._values[section_name] = OrderedDict()

        return self._values[section_name]

    def from_config(self, key, default=None):

        value = self._config.get(key, default=default)

        if value is None:
            return default

        return value

    def update_with_extra(self, base_section):

        extra_nml = self.from_config(base_section)
        if extra_nml is None:
            return

        for section_name in extra_nml:
            # Update section values with extra ones
            self.section(section_name).update(extra_nml[section_name])

    def calc_values(self):
        """
        Builds the dictionary for template namelist substitutions.
        Is supposed to be overridden by a subclass.
        """
        self.max_dom = self.from_config("max_dom", 1)
        self.date_s  = pud.read_date(self.from_config("date_s", "2000-01-01 00:00"))
        self.date_e  = pud.read_date(self.from_config("date_e", "2000-01-01 12:00"))

    def write(self, filename):

        self.calc_values()
        nml_config = NmlDict(self._values)

        if self._template is not None:
            nml_template = read_f90nml(self._template)
            nml_config = merge_dicts(nml_template, nml_config)

        nml_config.write(filename, force=True)

if __name__ == "__main__":

    import sys
    config_file = sys.argv[1]

    try:
        config = ConfigStore(config_file)
    except IOError:
        sys.exit("\nERROR: unable to open config file '{}'".format(config_file))

    from pywrf.namelist import WPSNamelist
    wps_nml = WPSNamelist(config)
    wps_nml.write("wps.namelist")
