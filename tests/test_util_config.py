#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import pytest
import shutil
import sys
import tempfile

sys.path.insert(1, '..')

from pywrf.util.config import ConfigStore, SmartOrderedDict


CONF_FILE = """
### COMMENT ###
string : /home/data/
int : 10
list : 1, 2, 3
list2 : 2*3
mixed : 2*3, 4
mixed2 : 2*3, text
home : ${HOME}
rank1:
    rank2.1 : 1
    rank2.2 : 2
"""

CONF_EVAL = """
sum : eval( 3 + 4 )
div : eval( 8. / 2 )
prod : eval( 3 * 4 )
sub : eval(1-2)
noeval : 1-2
"""

CONF_EVAL_BUG = """
sum : eval( '3 + 4 )
"""

CONF_INC_1 = """
include : ${CALLED}
existing : 1
new : 4
imp : "%(imported)"
map : {1: "a"}
"""

CONF_INC_2 = """
existing : 2
imported : 3
map : {2: "b"}
"""


def create_conf_file(f_name, f_content):
    dir = tempfile.mkdtemp()
    with open(os.path.join(dir, f_name), "w") as f:
        f.write(f_content)
    return dir


class TestConfig:

    def test_none(self):
        config = ConfigStore()
        assert list(iter(config)) == []
        assert str(config) == "ConfigStore('None')"

    def test_values(self):
        config = ConfigStore(io.StringIO(CONF_FILE))
        assert config["string"] == "/home/data/"
        assert config["int"] == 10
        assert config["list"] == [1, 2, 3]
        assert config["list2"] == [3, 3]
        assert config["mixed"] == [3, 3, 4]
        assert config["mixed2"] == [3, 3, "text"]

    def test_file(self):
        dir = create_conf_file("conf.yaml", CONF_FILE)
        try:
            config = ConfigStore(os.path.join(dir, "conf.yaml"))
            assert config["string"] == "/home/data/"
        finally:
            shutil.rmtree(dir)

    def test_type(self):
        config = ConfigStore(io.StringIO(CONF_FILE))
        assert isinstance(config.get("string"), str)
        assert isinstance(config.get("int"), int)
        assert isinstance(config.get("list"), list)

    def test_environ(self):
        config = ConfigStore(io.StringIO(CONF_FILE))
        assert config.get("home") == os.environ["HOME"]

    def test_nested(self):
        config = ConfigStore(io.StringIO(CONF_FILE))
        assert config.get("rank1", "rank2.1") == 1
        assert config.get("rank1/rank2.2") == 2

    def test_set(self):
        config = ConfigStore(io.StringIO(CONF_FILE))
        with pytest.raises(KeyError):
            n = config["new"]
        assert config.get("new") is None
        assert config.get("new", default=0) == 0
        assert ("new" in config) == False
        config["new"] = 1
        assert ("new" in config) == True
        assert config.get("new") == 1
        assert config.get("new", default=0) == 1
        assert config.get("new", default="") == '1'

    def test_update(self):
        config = ConfigStore(io.StringIO(CONF_FILE))
        config.update_default("int", 20)
        config.update_default("new", "new")
        assert config["int"] == 10
        assert config["new"] == "new"

    def test_include(self):
        dir1 = create_conf_file("conf1.yaml", CONF_INC_1)
        dir2 = create_conf_file("conf2.yaml", CONF_INC_2)
        os.environ["CALLED"] = os.path.join(dir2, "conf2.yaml")
        try:
            config = ConfigStore(os.path.join(dir1, "conf1.yaml"))
            assert config["existing"] == 1
            assert config["imported"] == 3
            assert config["new"] == 4
            assert config["imp"] == 3
            sod = SmartOrderedDict()
            sod[2] = "b"
            sod[1] = "a"
            assert config["map"] == sod
        finally:
            shutil.rmtree(dir1)
            shutil.rmtree(dir2)

    def test_eval(self):
        config = ConfigStore(io.StringIO(CONF_EVAL))
        assert config["sum"] == 7
        assert config["div"] == 4
        assert config["prod"] == 12
        assert config["sub"] == -1
        assert config["noeval"] == "1-2"
        with pytest.raises(Exception):
            config = ConfigStore(io.StringIO(CONF_EVAL_BUG))
