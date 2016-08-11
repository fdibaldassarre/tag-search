#!/usr/bin/env python3

import os
import argparse

from src import TagSearch

parser = argparse.ArgumentParser(description='Browse tagged files')
parser.add_argument('--profile', help='profile to use', default='default')
args = parser.parse_args()

profile = args.profile

config_folder = os.path.join(os.environ['HOME'], ".config/tag-search/" + profile)
ui = TagSearch.start(config_folder)
ui.openBrowser()
ui.start()
