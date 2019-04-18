#!/usr/bin/env python3
# vim: set ts=4 sw=4 expandtab syntax=python:
"""

psvstore.cli
PS Vita package tool
CLI entry-point


"""

import os
if os.name == 'nt':
    import msvcrt
else:
    import sys, select
import sys
import logging
from argparse import ArgumentParser

from psvstore import __version__, __date__
from psvstore import psfree
from psvstore.util import *

logger = logging.getLogger('psvpack')

def kbhit():
    ''' Returns True if a keypress is waiting to be read in stdin, False otherwise.
    '''
    if os.name == 'nt':
        return msvcrt.kbhit()
    else:
        dr,dw,de = select.select([sys.stdin], [], [], 0)
        return dr != []

def setup_logging(clevel=logging.INFO, flevel=logging.DEBUG, logfile=None):
    """configure logging using standard logging module"""
    logger.setLevel(logging.DEBUG)

    con = logging.StreamHandler()
    con.setLevel(clevel)
    con_format = logging.Formatter("%(levelname)s: %(message)s")
    con.setFormatter(con_format)
    logger.addHandler(con)

    if logfile:
        try:
            flog = logging.handlers.WatchedFileHandler(logfile)
            flog.setLevel(flevel)
            flog_format = logging.Formatter("[%(asctime)s] %(name)s: %(levelname)s: %(message)s")
            flog.setFormatter(flog_format)
            logger.addHandler(flog)
        except Exception as e:
            logger.warning("Failed to open logfile %s: %s", logfile, str(e))

def parse_cli(show_help=False):
    """parse CLI options with argparse"""
    aparser = ArgumentParser(description="PSVita pkg downloader", usage="psvpack -g -c -X -V [a|b|s] [tid|file|search term]")

    # use defaults stored in __init__
    aparser.set_defaults(loglevel=logging.INFO, command=None, noverify=False, glist="PSV", config=get_platform_confpath())

    aparser.add_argument("command", action="store", nargs="?", metavar="COMMAND", help="Command [search, install]")
    aparser.add_argument("parameter", action="store", nargs="?", metavar="PARAMETER", help="Title ID | Batch File | Search term")
    aparser.add_argument("--glist", "-g", action="store", metavar="LIST", help="game list [PSV,PSV_DLC,UPD]")
    aparser.add_argument("--config", "-c", action="store", metavar="PATH", help="config file [default: "+get_platform_confpath()+"]")
    aparser.add_argument("--noverify", "-X", action="store_true", help="skip existing PKG checksum verification")
    aparser.add_argument("--debug", "-d", dest="loglevel", action="store_const", const=logging.DEBUG,
                         help="Enable debug logging")
    aparser.add_argument("--version", "-V", action="version", version="%s (%s)" % (__version__, __date__))

    if show_help:
        aparser.print_help()
        sys.exit(1)

    return aparser.parse_args()

def _main():
    """
    Entry point
    """
    opts = parse_cli()
    setup_logging(clevel=opts.loglevel)
    uconfig = load_config(opts.config)

    if not opts.command in ["a","b","s"]:
        parse_cli(show_help=True)

    if opts.command[0] == 's':
        psfree.do_search(opts.parameter, uconfig, glist=opts.glist)
    elif opts.command[0] == 'a':
        if opts.parameter[:3]==("PCS") and opts.parameter[3] in ["A","B","H","E","C","G","I","F","D",] and opts.parameter[4:].isnumeric():
            psfree.archive(opts.parameter, uconfig)
        else:
            logger.error("Error: Invalid Title ID")
    elif opts.command[0] == 'b':
        try:
            with open(opts.parameter, 'r') as batch:
                for line in batch:
                    psfree.archive(line[:-1], uconfig) #delete \n
                    if kbhit(): break
        except OSError:
            logger.error("Error: File %s not found", opts.parameter)

if __name__ == '__main__':
    _main()
