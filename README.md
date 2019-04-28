
# psvstore

**psvstore** is a command-line tool written in python for automatically creating archives of PS Vita Titles. It also includes a search function. What does psvstore set apart from other pkg downloaders? First, it's a command-line tool, so it can be used on a headless remote server, for example. Second, it creates something like merged sets. It downloads a title, all available DLCs of the title plus the latest update of that title ans packs it all together in an accordingly named archive. It stores the original, unaltered pks that match the nointro dat file along with the appropriate zrifs, if a source is given. It's only tested on Linux so far but it sould work on other platforms, too.

# License

```
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of
the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

# Setup Instructions

## Prerequisites

* Python 3.4+
* Git

## Installing psvstore

```
git clone https://github.com/Qubits01/psvstore/
cd psvstore
sudo ./setup.py install
```

## First Run & Configuration

After installation, you should now be able to run:
```
psvstore
```

Make sure to run this as your user and NOT root! This will generate the `~/.config/psvstore` directory, create
a default configuration, then launch your default editor (defined by `$EDITOR`; `nano` is used if this is not defined). Once the editor is launched, be sure to update the `tsv_urls` values. Once you have finished making changes, press `Control+X` to save and exit. This file is located at `~/.config/psvstore/config.yaml` if you need to make further updates in the future.

# Usage

Once you have the correct URLs for TSV files added to your config file, you can begin using psvstore. The general usage is as follows:
```
psvstore [OPTIONS] COMMAND PARAMETER
```

`COMMAND` can be one of the following:
* `s` - Search through TSV files for a title name, content ID, or title ID
* `a` - Create a zip archive of the given Title ID with all available DLCs as well as the latest cumulative Update. 
* `b` - Process a batch file containing Title IDs to download 

## Searching for Games

**General usage:**
```
psvstore [-g] s GAME_TITLE_OR_ID
```

* By default, the `PSV` game list is searched. Use the `-g` option to specify a different `GAME_LIST`. The following are available:
    * `PSV` - PS Vita games
    * `PSV_DLC` - PS Vita DLC
    * `UPD` - PS Vita Updates
* The `GAME_TITLE_OR_ID` can either be a text search term (eg. part of a game name or "original name") or a Title ID (such as `PCSG00XXX`)

### Examples

**Finding PSV games by search term:**
```
psvstore s neptun
```
This will return a list of all Neptunia games for PS Vita. If you wish to grab a title, copy the ID for use with the `a` command.

**Finding all related DLC for a Vita game:**
```
psvstore -g PSV_DLC s PCSG00551
```
This will return a list of all DLC packs associated with title `PCSG00551` (*Taiko no Tatsujin V Version*).

**You can also use UTF-8 text when searching for Japanese or Asian titles:**
```
psvstore s 伝説
```
This searches for games with the text 【伝説】(*densetsu*).

Be sure to add quotes when your search term contains spaces:
```
psvstore s "final fanta"
```
This searches for *Final Fantasy* games.

## Archiving Games

**General usage:**
```
psvstore a TITLE_ID
```

* `TITLE_ID` should be the Title ID of the game. This can be acquired by using the `search` command.

### Example

**Create a Game Archive:**
```
psvstore a PCSA00007
```
This will download *Hustle Kings (US)*, all DLCs of that game and the latest update to your default cache directory. It will then create a zip archive named "Hustle Kings [PCSA00007] [US] [1.01] [3xDLC].zip". Inside will be all the downloaded pks with the unaltered name. The corresponding zRIF of a package will also be stored, if available within the tsv file. It will be the same filename as the pkg with a .zRIF extension.
Each DLC will be stored within a subdir named accordingly to the DLC. Updates will be stored in a subfolder named after the version number of the Update. Finally, there will be a comment added to the zipfile, that will tell you the minimum required firmware version of the game - updated and not updated.

## Batch-Archiving Games

**General usage:**
```
psvstore b FILENAME
```
The filename specified contains Title IDs (one per line) in plaintext form. psvstore will then download all Titles found in FILENAME. At the moment the processing can only be interrupted by CTRL+C. 
