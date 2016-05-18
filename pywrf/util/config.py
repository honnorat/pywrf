#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a class ConfigStore to easily read configuration files in YAML format.

Configuration files substitute environment variables or existing variables defined somewhere else
in the configuration store, they also can import other configuration files.

For example, if the following file is named ``'example.yaml'``: ::

    # Example configuration file
    my_path : /home/data/
    nbiter : 10

then we can use ConfigStore as follows: ::

>>> conf = ConfigStore('example.yaml')
>>> print conf["nbiter"]
10
"""

import os
import re
import string
import sys
import yaml
from builtins import str
from collections import OrderedDict, Mapping

from pywrf.util.logger import get_logger

RE_OP_STRING   = re.compile(r"[\+\-\*/%]+")
RE_EVAL_STRING = re.compile(r"eval\((?P<bracket>[\"\'])?(?P<eval_str>.*?)(?P=bracket)?\)")


class LocalTemplate(string.Template):

    delimiter = '%'
    pattern = r"""
    %(delim)s(?:
      (?P<escaped>%(delim)s) |   # Escape sequence of two delimiters
      (?P<named>%(id)s)      |   # delimiter and a Python identifier
    \((?P<braced>%(id)s)\)   |   # delimiter and a braced identifier
      (?P<invalid>)              # Other ill-formed delimiter exprs
    )
    """ % {'delim': re.escape(delimiter), 'id': string.Template.idpattern}


def tryto_eval(value):

    # Look for 'eval' keyword
    results = RE_EVAL_STRING.findall(value)

    if not results:
        # No 'eval' found, we return and evaluated version of 'value' only if it
        # does not contain any operator. This will prevent a unwanted evaluation
        # of a date string for example "2015-01-01".
        if RE_OP_STRING.search(value) is None:
            try:
                value = eval(value)
                if isinstance(value, tuple):
                    value = list(value)
            except:
                pass
        return value

    for result in results:
        # For each occurrence of 'eval(...)', we try to replace it with the evaluation
        # of its content.
        try:
            # result[0] is an optional quote character (" or ')
            # result[1] is the actual string to evaluate
            strlook = r"eval({}{}{})".format(result[0], result[1], result[0])
            value = eval(value.replace(strlook, str(eval(result[1]))))
        except Exception as e:
            raise Exception("Error while parsing '{}'".format(result[1]))

    return value


def transform_value(value, default=None):

    if isinstance(value, str):
        value = tryto_eval(value)

    if isinstance(value, str):
        if (',' in value or '*' in value):
            # Transform text to list
            str_list = list(map(str.strip, (e for e in value.split(",") if e)))

            # Transform string "3*4" into a list ['4', '4', '4']
            for i, list_item in enumerate(str_list):
                list_item = tryto_eval(list_item)
                if isinstance(list_item, str) and '*' in list_item:
                    nb, val = list_item.split("*")
                    str_list[i] = int(nb) * [val]

            # Flatten and evaluate str_list : [['2', '3'], [' 4']] -> [2, 3, 4]
            value = []
            for item in str_list:
                try:
                    if isinstance(item, list):
                        item = list(map(tryto_eval, item))
                    else:
                        item = [tryto_eval(item)]
                except:
                    # Maybe it's a string we cannot evaluate...
                    pass
                if not isinstance(item, list):
                    item = [item]
                value.extend(item)
        else:
            value = tryto_eval(value)

    if value is None:
        return default

    if (default is not None) and (type(value) != type(default)):
        # Force 'value' to be of same type as 'default'.
        return type(default)(value)

    return value


class SmartOrderedDict(OrderedDict):

    def __missing__(self, key):
        return None

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, transform_value(value))

    def __str__(self):
        return yaml.dump(self)

    def update(self, other):
        """
        Update the present dictionary with the other one. If a key is found in both dicts
        and the corresponding values are themselves dicts, we update instead of overwriting.
        """
        for key in other:
            o_val = other[key]
            if key in self:
                s_val = self[key]
                if isinstance(s_val, Mapping) and isinstance(o_val, Mapping):
                    s_val.update(o_val)
                else:
                    self[key] = o_val
            else:
                self[key] = o_val


# Customize YAML library in order to use SmartOrderedDict instead of
# regular dicts for mapping.

def sod_representer(dumper, data):
    return dumper.represent_dict(iter(data.items()))


def construct_mapping(loader, node):
    return SmartOrderedDict(loader.construct_pairs(node))

yaml.add_representer(SmartOrderedDict, sod_representer)
yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)


class ConfigStore:
    """
    Dictionary built from a configuration file. See util.config for an example.
    """
    log = get_logger("pywrf")

    def __init__(self, path=None):
        """
        :param path: Path to the configuration file.
        """
        self.read_config_file(path)

    def __iter__(self):
        return iter(self._values)

    def __setitem__(self, key, value):

        if (key in self._values) and (value != self._values[key]):
            ConfigStore.log.debug("WARNING: %s: redefining directive '%s': ('%s' -> '%s')"
                      % (self._path, key, self._values[key], value))

        self._values[key] = value

    def __getitem__(self, key):
        return self.get(key, raise_keyerror=True)

    def __contains__(self, key):
        try:
            self.get(key, raise_keyerror=True)
        except KeyError:
            return False
        else:
            return True

    def __str__(self):
        return "ConfigStore('{}')".format(self._path)

    @property
    def values(self):
        return yaml.dump(self._values)

    def update_default(self, key, value):
        """
        Add (key, value) only if key is not already present.
        """
        if key not in self._values:
            ConfigStore.log.warning("Set default config value for {}: {}".format(key, value))
            self._values[key] = value

    def get(self, *args, **kwargs):
        """
        Returns the value of potentially nested keys.

        >>> config.get("namelist_wps/share")
        SmartOrderedDict([('debug_level', 10)])
        >>> config.get("namelist_wps/share", "debug_level")
        10
        >>> config.get("namelist_wps", "share", "debug_level")
        10

        Raises a KeyError if the value is not found.
        """
        raise_keyerror = ("raise_keyerror" in kwargs) and (kwargs["raise_keyerror"])
        default = None if ("default" not in kwargs) else kwargs["default"]
        args = "/".join(args).split("/")    # Flatten list of arguments : ["1/2", "3"] -> ["1", "2", "3"]
        value = self._values
        for arg in args:
            value = value[arg]
            if value is None:
                if raise_keyerror:
                    raise KeyError(arg)
                else:
                    return transform_value(value, default)

        return transform_value(value, default)

    def read_config_file(self, path):
        """
        Parse a configuration file in YAML format and store the contents as an ordered dictionary.
        """
        self._path = path
        self._values = SmartOrderedDict()

        if path is None:
            return

        if isinstance(path, str):

            format = os.path.splitext(path)[1]

            if format not in ('.yaml', '.yml'):
                raise NotImplementedError("Only YAML configuration files are supported.")

            # Read data from file
            with open(path, "rt") as f:
                conf_str = f.read()

        elif hasattr(path, "read"):
            conf_str = path.read()

        else:
            NotImplementedError("Unrecognized type.")

        # First incorporate environment variables
        conf_str = string.Template(conf_str).safe_substitute(os.environ)

        # Convert text into a SmartOrderedDict instance
        config_dict = yaml.load(conf_str)

        # Include nested configuration files
        include_files = config_dict.get("include")
        if include_files is not None:
            if isinstance(include_files, str):
                include_files = [include_files]
            for i_file in include_files:
                ConfigStore.log("Including config file '{}'...".format(i_file))
                i_store = ConfigStore(i_file)
                self._values.update(i_store._values)
            del config_dict["include"]

        self._values.update(config_dict)

        # Then recursively convert local variables until no more changes occur.
        while True:
            conf_str_old = yaml.dump(self._values)
            conf_str_new = LocalTemplate(conf_str_old).safe_substitute(self._values)
            if conf_str_new == conf_str_old:
                break
            self._values = yaml.load(conf_str_new)


if __name__ == "__main__":

    if len(sys.argv) == 1:
        import io
        cfile = io.StringIO("""
            string : /home/data/
            int : 10
            list : 1, 2, 3
        """)
        args = [cfile]

    else:
        args = sys.argv[1:]

    for config_file in args:

        print("=" * 150)
        c = ConfigStore(config_file)
        print(c)
        print(c.values)
        print("my_path :", c.get("my_path", default="/dev/null"))
