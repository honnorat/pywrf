#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    ANSII Color formatting for output in terminal.
"""

from __future__ import print_function
import os

__all__ = ['bolded', 'colored']

ATTRIBUTES = {
    'bold':      1,
    'dark':      2,
    'underline': 4,
    'blink':     5,
    'reverse':   7,
    'concealed': 8
}
HIGHLIGHTS = {
    'on_grey':    40,
    'on_red':     41,
    'on_green':   42,
    'on_yellow':  43,
    'on_blue':    44,
    'on_magenta': 45,
    'on_cyan':    46,
    'on_white':   47
}
COLORS = {
    'grey':    30,
    'red':     31,
    'green':   32,
    'yellow':  33,
    'blue':    34,
    'magenta': 35,
    'cyan':    36,
    'white':   37
}

RESET = '\033[0m'


def colored(text, color=None, on_color=None, attrs=None):
    r""" Colorize text.

    Available text colors:
        `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`.

    Available text highlights:
        `on_red`, `on_green`, `on_yellow`, `on_blue`, `on_magenta`, `on_cyan`, `on_white`.

    Available attributes:
        bold, dark, underline, blink, reverse, concealed.

    >>> colored('Hello, World!', 'red', 'on_white', ['blink'])
    '\\x1b[5m\\x1b[47m\\x1b[31mHello, World!\\x1b[0m'
    >>> colored('Hello, World!', 'green')
    '\\x1b[32mHello, World!\\x1b[0m'
    """
    if os.getenv('ANSI_COLORS_DISABLED') is None:
        fmt_str = '\033[%dm%s'
        if color is not None:
            text = fmt_str % (COLORS[color], text)

        if on_color is not None:
            text = fmt_str % (HIGHLIGHTS[on_color], text)

        if attrs is not None:
            for attr in attrs:
                text = fmt_str % (ATTRIBUTES[attr], text)

        text += RESET
    return text


def bolded(text):
    r"""
    Return a modified version of ``text`` with bold TTY decoration.

    >>> bolded("Hello, bolded")
    '\x1b[1mHello, bolded\x1b[0m'
    """
    return colored(text, attrs=["bold"])


if __name__ == '__main__':

    print('Current terminal type: %s' % os.getenv('TERM'))
    print('Test basic colors:')
    print(colored('Grey color', 'grey'))
    print(colored('Red color', 'red'))
    print(colored('Green color', 'green'))
    print(colored('Yellow color', 'yellow'))
    print(colored('Blue color', 'blue'))
    print(colored('Magenta color', 'magenta'))
    print(colored('Cyan color', 'cyan'))
    print(colored('White color', 'white'))
    print(('-' * 78))

    print('Test highlights:')
    print(colored('On grey color', on_color='on_grey'))
    print(colored('On red color', on_color='on_red'))
    print(colored('On green color', on_color='on_green'))
    print(colored('On yellow color', on_color='on_yellow'))
    print(colored('On blue color', on_color='on_blue'))
    print(colored('On magenta color', on_color='on_magenta'))
    print(colored('On cyan color', on_color='on_cyan'))
    print(colored('On white color', color='grey', on_color='on_white'))
    print('-' * 78)

    print('Test attributes:')
    print(colored('Bold grey color', 'grey', attrs=['bold']))
    print(colored('Dark red color', 'red', attrs=['dark']))
    print(colored('Underline green color', 'green', attrs=['underline']))
    print(colored('Blink yellow color', 'yellow', attrs=['blink']))
    print(colored('Reversed blue color', 'blue', attrs=['reverse']))
    print(colored('Concealed Magenta color', 'magenta', attrs=['concealed']))
    print(colored('Bold underline reverse cyan color', 'cyan', attrs=['bold', 'underline', 'reverse']))
    print(colored('Dark blink concealed white color', 'white', attrs=['dark', 'blink', 'concealed']))
    print(('-' * 78))

    print('Test mixing:')
    print(colored('Underline red on grey color', 'red', 'on_grey',  ['underline']))
    print(colored('Reversed green on red color', 'green', 'on_red', ['reverse']))
