#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module contains functions that complement the standard library for manipulating files.
"""

import os
import errno

try:
    _link = os.symlink
except AttributeError:
    import shutil
    _link = shutil.copy


def force_symlink(file1, file2):
    """
    Let ``file2`` be a symbolic link to ``file1``. If symbolic links are not available on the platform,
    copy ``file1`` to the location named ``file2``. In both cases, the original ``file2`` is overwritten.

    :param file1: Path to the source file:
    :param file2: Path to the destination file.
    """
    if os.path.lexists(file2):
        os.remove(file2)

    _link(file1, file2)


def expand_path(path):

    rpath = os.path.expanduser(path)
    if not os.path.isabs(rpath):
        rpath = os.path.abspath(rpath)
    return rpath


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise exc
