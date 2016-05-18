#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module contains miscellanious functions that complement the standard library.
"""

def to_list(item, nb=1):
    """ Transform item into a list of size nb """

    # Transform string representing a list into an actual list
    if isinstance(item, str) and item[0] == "[" and item[-1] == "]":
        item = eval(item)

    # Transform any non-list item into a list
    if not isinstance(item, list):
        item = nb*[item]

    return item

