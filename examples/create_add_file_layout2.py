#!/usr/bin/env python3

import os
import argparse

from src import TagSearch

parser = argparse.ArgumentParser(description='Create add file layout')
parser.add_argument('--profile', help='profile to use', default='default')
args = parser.parse_args()

profile = args.profile

config_folder = os.path.join(os.environ['HOME'], ".config/tag-search/" + profile)

ui = TagSearch.start(config_folder)
afl = ui.getAddFileLayout()
afl.clean()
# UI
meta_artist = ui.getMetaTagFromName('Content')
afl.addEntryField('content', meta_artist, label='Content', default='"Unknown"', autocomplete=True, allows_empty=False)
afl.addSeparator()
meta_genre = ui.getMetaTagFromName('Type')
afl.addRadioField('type', meta_genre)
afl.addSeparator()
# Destination
afl.setDestination('#{type} + "/" + #{content} + "/" + #{_filename}')
afl.save()
