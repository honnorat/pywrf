#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module defines a CustomLogger class. Any class that need to implement a logging
facility can be derived from CustomLogger.
The method CustomLogger.setup_logging() can be overridden in the subclass to customize the log output.
"""

import sys
import re
import logging

from pywrf.util.termcolor import colored

__all__ = ['create_logger', 'get_logger']


class _RewritableHandler:
    """
    Interface that rewrite logging messages according to their actual level.
    """
    @property
    def istty(self):
        """
        Returns True if the current object is of console type.
        """
        # Beware, there is some magic in the following lines.
        isatty = getattr(self.stream, 'isatty', None)
        return isatty and isatty()

    def rewrite_msg(self, record):
        """
        Rewrite the record with a colored label according to the message level.
        """
        if record.levelno in (logging.ERROR, logging.CRITICAL):
            record.msg = colored('[{}]: '.format(record.levelname), 'red') + record.msg
        elif record.levelno in (logging.WARNING, logging.DEBUG):
            record.msg = colored('[{}]: '.format(record.levelname), 'yellow') + record.msg

        if not self.istty:  # Remove all colors
            record.msg = re.sub(r"\033\[[0-9;]*m", "", str(record.msg))


class ColoredStreamHandler(logging.StreamHandler, _RewritableHandler):
    """
    A handler class which writes formatted logging records to data stream.
    """
    def format(self, record):
        self.rewrite_msg(record)
        return logging.StreamHandler.format(self, record)


class ColoredFileHandler(logging.FileHandler, _RewritableHandler):
    """
    A handler class which writes formatted logging records to disk files.
    """
    def format(self, record):
        self.rewrite_msg(record)
        return logging.FileHandler.format(self, record)


class LogWrapper(object):
    """
    Wrapper class for logging.Logger.
    Make it possible to call the instance directly ; in this case, the message is passed
    at level INFO.
    """
    def __init__(self, log):
        self.log = log

    def __getattr__(self, name):
        # If the user calls LogWrapper.info(), it is deferred to LogWrapper.log.info()
        try:
            return self.__getattribute__(name)
        except:
            return getattr(self.log, name)

    def __call__(self, message):
        self.log.info(message)


def create_logger(name, log_level=logging.INFO, log_fmt=None, log_file=None,
                  color=True, stderr=False):
    """
    Creates a logging instance.
    If log_file is specified, handler is a FileHandler, otherwise StreamHandler
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if log_fmt is None:
        log_fmt = '%(asctime)s: %(message)s'

    formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d_%H:%M:%S')

    if stderr:
        sout = sys.stderr
    else:
        sout = sys.stdout

    if color:
        csh = ColoredStreamHandler(sout)
    else:
        csh = logging.StreamHandler(sout)
    csh.setFormatter(formatter)
    logger.addHandler(csh)

    if log_file is not None:
        fh = logging.FileHandler(log_file, mode='w')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return LogWrapper(logger)


def get_logger(name):

    return LogWrapper(logging.getLogger(name))


if __name__ == "__main__":

    def _logit(log, level=None):

        if level is not None:
            log.setLevel(level)

        log.critical("*" * 50)
        log.critical("*  LEVEL = %s" % logging.getLevelName(log.level))
        log.critical("*" * 50)
        log.debug("Ceci est un message de niveau 'debug'.")
        log.info("Ceci est un message de niveau 'info'.")
        log.warn("Ceci est un message de niveau 'warn'.")
        log.error("Ceci est un message de niveau 'error'.")
        log.fatal("Ceci est un message de niveau 'fatal'.")
        try:
            a = 1 / 0.
        except:
            log.exception("Ceci est un message lancé lors d'une exception.")
            print("")

    log = create_logger("test", log_fmt="", log_file="toto.out")

    _logit(log)
    _logit(log, logging.NOTSET)
    _logit(log, logging.ERROR)
    _logit(log, logging.INFO)
    _logit(log, logging.DEBUG)
    _logit(log, logging.CRITICAL)
