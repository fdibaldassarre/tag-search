#!/usr/bin/env python3

import os
import argparse

from src import TagSearch
from src.Common import getConfigFolder

parser = argparse.ArgumentParser(description='Tag file')
parser.add_argument('path', help='file to tag')
parser.add_argument('--profile', help='profile to use', default='default')
args = parser.parse_args()

path = args.path
profile = args.profile

config_folder = getConfigFolder(profile)

ui = TagSearch.start(config_folder)
ui.openTagFile(path)
ui.start()
