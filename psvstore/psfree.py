#!/usr/bin/env python3
# vim: set ts=4 sw=4 expandtab syntax=python:
"""

psvpack.psfree
PSFree search tool, TSV parser & pkg downloader

"""

import os
import sys
import codecs
import errno
import re
import logging
import csv
import subprocess
from time import time
import zlib
from zipfile import ZipFile
import shutil

import arrow
import requests
import progressbar

from psvstore.util import *


logger = logging.getLogger('psvpack')


class TSVManager(object):
    """
    Handles downloading, updating, parsing, and searching of TSV files
    """
    filename = None
    url = None
    last_update = None
    ttl = None
    glist = []
    loaded = False
    pd = None

    def __init__(self, tsvname, config, pd=None):
        try:
            self.ttl = int(config['cache_ttl'])
        except:
            logger.error("Invalid `cache_ttl` specified in config file. Using default.")
            self.ttl = 86400
        self.tsvname = tsvname
        self.pd = pd
        self.url = config['tsv_urls'][tsvname.upper()]
        self.filename = os.path.join(os.path.expanduser(config['cache_dir']), 'tsv', self.url.split('/')[-1])
        logger.debug("Using TSV for %s: URL=%s / Local=%s", tsvname, self.url, self.filename)
        self.check_for_update()
        self.load_tsv()

    def set_progress(self, msg=None, value=None):
        """
        Update progress dialog, if one is specified (self.pd)
        """
        if self.pd:
            if msg is not None:
                self.pd.setLabelText(msg)
            if value is not None:
                self.pd.setValue(value)

    def check_for_update(self, force=False):
        """
        Check mtime of cache TSV file to see if we should update
        If @force is True, then force an update
        """
        do_update = True if force else False
        nowtime = time()

        try:
            last_update = os.stat(self.filename).st_mtime
            logger.debug("Cached TSV file last updated %s", arrow.get(last_update).format())
            if nowtime - last_update >= self.ttl:
                do_update = True
            else:
                self.last_update = arrow.get(last_update)
        except OSError as e:
            if e.errno == errno.EACCES:
                logger.error("Permission denied when attempting to access cached TSV file: %s", self.filename)
                return None
            elif e.errno != errno.ENOENT:
                logger.error("Error accessing cached TSV file [%s]: %s", self.filename, str(e))
                return None
            else:
                do_update = True

        if do_update:
            try:
                logger.info("Updating cached TSV file from %s", self.url)
                self.set_progress("Downloading updated game list (%s)..." % (self.tsvname))
                r = requests.get(self.url)
                r.raise_for_status()
            except Exception as e:
                logger.error("Failed to fetch TSV file: %s", str(e))
                return None

            try:
                self.last_update = arrow.get(r.headers['Last-Modified'], "ddd, DD MMM YYYY HH:mm:ss ZZZ")
                logger.debug("Remote TSV modification time: %s", self.last_update.format())
            except Exception as e:
                logger.warning("Failed to parse modification time of TSV file. Using current time. Error: %s", str(e))
                self.last_update = arrow.now()

            cache_dir = os.path.dirname(self.filename)
            if not os.path.exists(cache_dir):
                try:
                    os.makedirs(cache_dir, 0o775, exist_ok=True)
                except:
                    logger.error("Failed to create TSV cache directory %s: %s", cache_dir, str(e))

            try:
                with codecs.open(self.filename, 'w', 'utf8') as f:
                    f.write(r.content.decode('utf8'))
                logger.info("Wrote TSV file successfully: %s", self.filename)
                # TODO: need to figure out a better way to track last update
                #os.utime(self.filename, (nowtime.timestamp, self.last_update.timestamp))
            except Exception as e:
                logger.error("Failed to write updated TSV cache file [%s]: %s", self.filename, str(e))
                return None

        return self.last_update

    def load_tsv(self):
        """
        Parse TSV file
        """
        self.set_progress("Parsing game list...", 50)
        try:
            with codecs.open(self.filename, 'r', 'utf8') as f:
                self.glist = [x for x in csv.DictReader(f, dialect='excel-tab')]
            self.loaded = True
            return True
        except Exception as e:
            logger.error("Failed to parse TSV file: %s", str(e))
            return False

    def search(self, gtitle, reglist=['US', 'JP', 'EU', 'ASIA']):
        """
        Search for game title in TSV
        """
        return [x for x in self.glist if (re.search(gtitle, x['Name'], re.I) or re.search(gtitle, x.get('Original Name', ''), re.I) or gtitle == x['Title ID']) and x['Region'] in reglist]

    def get_title(self, tid):
        """
        Return game info by Title ID
        """
        if '-' in tid:
            rez = [x for x in self.glist if tid.upper() == x['Content ID']]
        else:
            rez = [x for x in self.glist if tid.upper() == x['Title ID']]

        if len(rez) == 0:
            return None
        else:
            return rez

def download_pkg(url, dest, cs=1024, filesize=0):
    """
    Download package from @url to @dest path via Requests stream
    @cs = chunk size
    """
    logger.info("Downloading pkg from %s --> %s", url, dest)

    pg = progressbar.ProgressBar(min_value=0, max_value=filesize).start()
    try:
        r = requests.get(url, stream=True)
        with open(dest, 'wb') as f:
            curbyte = 0
            for chunk in r.iter_content(chunk_size=cs):
                if chunk:
                    f.write(chunk)
                    curbyte += len(chunk)
                    pg.update(curbyte)

        fsize = os.stat(dest).st_size
        pg.finish()
        logger.info("Successfully fetched package (%s total size)", fmtsize(fsize))
        return fsize
    except Exception as e:
        logger.error("Failed to download file %s -> %s: %s", url, dest, str(e))
        return False

def check_cached(pkgpath, chksum, noverify=False):
    """
    Check to see if pkg exists locally and matches sha256 hash
    """
    if os.path.exists(pkgpath):
        if noverify:
            logger.warning("PKG file exists. SHA256 verification skipped.")
            return True
        else:
            logger.info("Checking integrity of existing pkg file...")
            if sha256sum(pkgpath) == chksum:
                logger.info("Existing file matches checksum -> %s", pkgpath)
                return True
            else:
                logger.warning("Existing file does NOT match checksum. Overwriting.")
    return False

def slugify(dirname):
    if "(3." in dirname:
        dirname = dirname[:dirname.find("(3.")-1]
    if "(DEMO" in dirname:
        dirname = dirname[:dirname.find("(DEMO")-1]
    dirname = dirname.replace(":", " -")
    invalid_chars = '/?<>\\*|\"'
    return ''.join(c for c in dirname if not(c in invalid_chars))

def fetch_pkg(tgame, config, glist="PSV", noverify=False):
    """
    Perform game download & optional installation
    """
    if not(glist == "UPD"):
        logger.info(">>> Downloading %s: %s", glist, tgame['Content ID'])
    else:
        logger.info(">>> Downloading %s: %s", glist, tgame["Title ID"])

    # Preflight checks
    if not(glist == "UPD"):
        if not(tgame['PKG direct link'][:4] == "http"):
            logger.error("Game does not include PKG download link!")
            return None
        elif tgame['zRIF'] == "MISSING":
            logger.warning("Game does not include zRIF! Downloading without zRIF!")

    # Check cache dir
    if glist == "PSV_DLC":
        cache_dir = os.path.realpath(os.path.join(os.path.expanduser(config['cache_dir']), 'pkg', slugify(tgame['Name'])))
    elif glist == "PSV":
        cache_dir = os.path.realpath(os.path.join(os.path.expanduser(config['cache_dir']), 'pkg'))
    elif glist == "UPD":
        ustring = "Update v"+tgame['Update Version']
        cache_dir = os.path.realpath(os.path.join(os.path.expanduser(config['cache_dir']), 'pkg', ustring))
    if not os.path.exists(cache_dir):
        try:
            os.makedirs(cache_dir, 0o775, exist_ok=True)
            logger.info("Created local pkg cache: %s", cache_dir)
        except Exception as e:
            logger.error("Failed to create pkg cache path [%s]: %s", cache_dir, str(e))
            return None

    # Fetch package if not exit
    local_path = os.path.realpath(os.path.join(cache_dir, tgame['PKG direct link'][tgame['PKG direct link'].rfind("/")+1:])) #save pkg in cachedir with original pkg name
    if not check_cached(local_path, tgame['SHA256'], noverify):
        try:
            rp_size = int(tgame['File Size'])
        except Exception as e:
            logger.error("Failed to parse expected filesize: %s", str(e))
            rp_size = -1

        dl_size = download_pkg(tgame['PKG direct link'], local_path, filesize=rp_size)
        if not dl_size:
            logger.error("Failed to retrieve package from remote repository :(")
            return None
        elif dl_size != rp_size:
            logger.warning("Downloaded package does not match reported size (%s != %s bytes)", dl_size, rp_size)

    # Write zrif if exist
    if not(glist == "UPD"):
        if not(tgame['zRIF'] == "MISSING"):
            zrifname = local_path[:-3]+"zrif"
            with open(zrifname, 'w') as f:
                f.write(tgame['zRIF'])
                logger.info("Successfully written zRIF for %s", tgame['Name'])
        else:
          logger.warning("No zRIF exists for %s", tgame['Name'])
    return local_path

def do_search(gtitle, config, glist="PSV"):
    """
    Perform a search, then display the results
    """
    tsv = TSVManager(glist, config)
    results = tsv.search(gtitle)

    if len(results):
        print('{:16} {:4} {:8} {}'.format("ID", "Reg", "Size", "Name/Version"))
        print('=' * 60)
        for tgame in results:
            warn = ""
            if 'PSV' in glist:
                if tgame['zRIF'] == "MISSING":
                    warn += "<NO zRIF!> "
            if tgame['PKG direct link'] == "MISSING":
                warn += "<NO PKG LINK!> "

            if 'DLC' in glist:
                print('{Content ID:42} {Region:4} {fsize:8} {Name} {warn}'.format(fsize=fmtsize(tgame['File Size']), warn=warn, **tgame))
            elif tgame.get('App Version'):
                print('{Title ID:16} {Region:4} {fsize:8} {Name} [{App Version}] {warn}'.format(fsize=fmtsize(tgame['File Size']), warn=warn, **tgame))
            elif 'UPD' in glist:
                print('{Title ID:16} {Region:4} {fsize:8} {Name} {Update Version} {warn}'.format(fsize=fmtsize(tgame['File Size']), warn=warn, **tgame))
            else:
                print('{Title ID:16} {Region:4} {fsize:8} {Name} {warn}'.format(fsize=fmtsize(tgame['File Size']), warn=warn, **tgame))
    else:
        print("!! No results.")
        return False

def archive(tid, config):
    """
    Download all pkgs of an associated tid (basegame, all DLC, latest update) and create a names archive TODO: with install script
    """
    tsv_g = TSVManager("PSV", config)
    tsv_d = TSVManager("PSV_DLC", config)
    tsv_u = TSVManager("UPD", config)
    #download
    game_count = get_game(tid, config, "PSV")
    dlc_count = get_game(tid, config, "PSV_DLC", False, True)
    get_game(tid, config, "UPD")
    #
    gresult = tsv_g.get_title(tid)
    print('success value: ',game_count)
    if game_count == 0:
        logger.error("Error. No PKG for Title ID %s found. Aborting.", tid)
        sys.exit()
    elif gresult is None:
        logger.error("Error. Title ID %s not found in Database. Aborting.", tid)
        sys.exit()
    dresult = tsv_d.get_title(tid)
    uresult = tsv_u.get_title(tid)
    uresult = getMaxVersion(uresult)
    title = gresult[0]['Title ID']
    region = gresult[0]['Region']
    name = slugify(gresult[0]['Name'])
    minv_o = gresult[0]['Required FW']
    if dlc_count is None:
        dlc_count = 0
    version = "1.00"  #Game Version
    minv_u = minv_o   #Firmware Version(s)
    if not(uresult is None):
        version = uresult[0]['Update Version']
        minv_u = uresult[0]['Required FW VERSION']
    archive_name = name + " [" + title + "] [" + region + "] [" + version + "]"
    if dlc_count == 0:
        archive_name = archive_name + ".zip"
    else:
        archive_name = archive_name + " [" + str(dlc_count) + "xDLC].zip"
    zip_path = os.path.realpath(os.path.join(os.path.expanduser(config['zip_out'])))
    zip_out = os.path.realpath(os.path.join(os.path.expanduser(config['zip_out']), archive_name))
    zip_in = os.path.realpath(os.path.join(os.path.expanduser(config['cache_dir']), 'pkg'))
    #print(archive_name)
    if not os.path.exists(zip_path):
        try:
            os.makedirs(zip_path, 0o775, exist_ok=True)
        except:
            logger.error("Failed to create zip output directory %s: %s", cache_dir, str(e))
    with ZipFile(zip_out, 'w') as zf:
        cpath = zip_in
        for dirpath,dirs,files in os.walk(cpath):
            for f in files:
                fabs = os.path.join(dirpath, f)
                frel = os.path.join(os.path.relpath(dirpath, cpath), f)      
                zf.write(fabs, frel)
        if uresult is None or minv_o == minv_u:
            cstr = "Minimum Firmware Version: "+minv_o
        else:
            cstr = "Minimum Firmware Version without Update: "+minv_o+"\nMinimum Firmware Version with Update: "+minv_u
        zf.comment = cstr.encode()
    logger.info("Successfully written \"%s\"", archive_name)
    shutil.rmtree(zip_in)
    os.mkdir(zip_in)
    logger.info("Downloaded pkgs deleted!")

def getMaxVersion(rlist):
    max = 0
    pos = 0
    if not(rlist is None):
        for entry in range(len(rlist)):
            if float(rlist[entry]['Update Version']) > max:
                max = float(rlist[entry]['Update Version'])
                pos = entry
        return [rlist[pos]]
    else:
        return rlist


def get_game(tid, config, glist="PSV", noverify=False, getall=False):
    """
    Fetch game by Title ID or Content ID
    Can install multiple titles/items (such as all matching DLC) when @getall is True
    """
    tsv = TSVManager(glist, config)
    gresults = tsv.get_title(tid)
    if gresults is None:
        logger.error("No %s match found for %s", glist, tid)
        return None

    if not(glist=="UPD"):
        if len(gresults) > 1 and not getall:
            logger.error("Error: Title ID not found.")
            return None
        else:
            logger.info("%d results found. Installing all related items...", len(gresults))
    elif len(gresults) > 1:
        gresults = getMaxVersion(gresults)

    ires = {'success': 0, 'failed': 0}
    for tgame in gresults:
        if fetch_pkg(tgame, config, glist, noverify) is None:
            ires['failed'] += 1
        else:
            ires['success'] += 1

    logger.info("*** Installation report: %d success / %d failed", ires['success'], ires['failed'])
    if ires['failed'] == 0:
        logger.info("All titles/items installed successfully!")
    else:
        logger.warning("Some titles/items failed")
    print("returning Value:", ires['success'])
    return ires['success']
