#!/usr/bin/env python3

import os
import argparse

from src import TagSearch
from src.Common import getConfigFolder

parser = argparse.ArgumentParser( description = 'Add file to database' )
parser.add_argument('file', help='file to tag', nargs=1)
parser.add_argument('--profile', dest='profile', help='profile to use', default='default')
args = parser.parse_args()

filepaths = args.file
filepath = filepaths[0]
profile = args.profile

config_folder = getConfigFolder(profile)
ui = TagSearch.start(config_folder)
ui.openAddFile(filepath)
ui.start()

