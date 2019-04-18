#!/usr/bin/env python3
# vim: set ts=4 sw=4 expandtab syntax=python:
"""

psvpack.util
Utility functions and configuration loader

@author   Jacob Hipps <jacob@ycnrg.org>

Copyright (c) 2018 J. Hipps / Neo-Retro Group, Inc.
https://ycnrg.org/

"""

import os
import re
import platform
import logging
import subprocess

import yaml

from psvpack import default_config, conf_header


logger = logging.getLogger('psvpack')


def load_config(fpath=None, interactive=True):
    fpath = get_platform_confpath('config.yaml')
    rpath = os.path.realpath(os.path.expanduser(fpath))
    fdir = os.path.dirname(rpath)

    logger.debug("Using config path: %s", fpath)

    if not os.path.exists(fdir):
        try:
            os.makedirs(fdir, mode=0o755, exist_ok=True)
            logger.info("Created new config directory: %s", fdir)
        except Exception as e:
            logger.error("Failed to create config directory: %s", str(e))
            return None

    # create default config if doesn't exist
    if not os.path.exists(rpath):
        save_config(get_default_config())

    # load config
    try:
        with open(rpath) as f:
            tconfig = yaml.load(f, Loader=yaml.SafeLoader)
        logger.debug("Loaded configuration from %s", rpath)
    except Exception as e:
        logger.error("Failed to load config from %s: %s", rpath, str(e))
        logger.warning("Using default configuration")
        tconfig = default_config

    logger.debug("Loaded config:\n%s", tconfig)
    return tconfig

def save_config(config, fpath=None):
    """
    Save user configuration to YAML file
    If @fpath is not specified, the default platform-specific path is used
    """
    if fpath is None:
        fpath = get_platform_confpath('config.yaml')
    rpath = os.path.realpath(os.path.expanduser(fpath))
    fdir = os.path.dirname(rpath)

    try:
        with open(rpath, 'w') as f:
            f.write(conf_header)
            yaml.dump(config, stream=f, Dumper=yaml.SafeDumper, default_flow_style=False)
        logger.info("Wrote config to: %s", rpath)
    except Exception as e:
        logger.error("Failed to write configuration: %s", str(e))
        return str(e)
    return True

def get_default_config():
    """
    Generate default config
    """
    dconf = default_config
    for tkey in dconf.keys():
        if isinstance(dconf[tkey], str):
            dconf[tkey] = re.sub(r'{{platform_confpath}}', get_platform_confpath(), dconf[tkey])
    return dconf

def launch_editor(confpath):
    """
    Launch default editor with chosen text file @confpath
    Used when a default config is generated
    """
    edpath = os.environ.get('EDITOR', '/bin/nano')
    xopts = ['-t'] if 'nano' in edpath else []

    logger.warning("Launching default editor (%s)...", edpath)
    os.execve(edpath, [edpath, confpath] + xopts, os.environ)

def fmtsize(insize, rate=False, bits=False):
    """
    format human-readable file size and xfer rates
    """
    try:
        onx = float(abs(int(insize)))
    except:
        return '?'

    for u in ['B', 'K', 'M', 'G', 'T', 'P']:
        if onx < 1024.0:
            tunit = u
            break
        onx /= 1024.0
    suffix = ""
    if u != 'B': suffix = "iB"
    if rate:
        if bits:
            suffix = "bps"
            onx *= 8.0
        else:
            suffix += "/sec"
    if tunit == 'B':
        ostr = "%3d %s%s" % (onx, tunit, suffix)
    else:
        ostr = "%3.01f %s%s" % (onx, tunit, suffix)
    return ostr

def sha256sum(fpath):
    """
    Run sha256sum on @fpath
    """
    ss = subprocess.Popen(['sha256sum', fpath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    so, se = ss.communicate()
    if ss.returncode != 0:
        return None
    else:
        return so.split()[0].strip().decode('utf-8', errors='ignore')

def get_platform_confpath(fname=None):
    """
    Determine the default config path for
    the current platform
    """
    pathlist = {
        'Linux': "~/.config/psvpack",
        'Darwin': "~/.config/psvpack",
        'Windows': "%APPDATA%/psvpack",
    }
    ppath = os.path.realpath(os.path.expandvars(os.path.expanduser(pathlist[platform.system()])))
    if fname:
        ppath = os.path.join(ppath, fname)
    return ppath
