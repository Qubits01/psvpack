#!/usr/bin/env python3
# vim: set ts=4 sw=4 expandtab syntax=python:
"""

psvstore.__init__
Config file data

"""

__version__ = '0.190418'
__date__ = '04 Apr 2019'

default_config = {
    'cache_dir': "{{platform_confpath}}",
    'cache_ttl': 86400,
    'zip_out' : "{{platform_confpath}}",
    'tsv_urls': {
        'PSV': "",
        'PSV_DLC': "",
        'UPD': "",
    },
}

conf_header = """\
# psvpack - user configuration file
#
# To revert back to defaults, simply delete this file, and it will be recreated
# the next time psvpack is run.
#
# Be sure to set the following values correctly:
# * pkg2zip  - Path to the pkg2zip binary (if you're unsure, run `which pkg2zip`)
#
# Optional:
# * cache_dir    - Path to where pkg files are downloaded (cache_dir/pkg)
# * cache_ttl    - Max age (in seconds) of TSV files before they are refreshed
#
---
"""
