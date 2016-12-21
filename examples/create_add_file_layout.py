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
db = ui.getDatabase()
afl = ui.getAddFileLayout()
afl.clean()
# UI
meta_artist = db.getCategoryFromName('Artist')
afl.addEntryField('artist', meta_artist, label='Artist', default='"Unknown"', autocomplete=True, allow_empty=False)
afl.addSeparator()
meta_genre = db.getCategoryFromName('Genre')
afl.addRadioField('genre', meta_genre)
afl.addSeparator()
meta_instr = db.getCategoryFromName('Instruments')
afl.addToggleField('instruments', meta_instr, horizontal=False)
# Destination
afl.setDestination('#{genre} + "/" + #{artist} + "/" + #{_filename}')
# More complex destination (example)
# afl.setDestination('("Classical/" if #{genre} == "Classical" else ("Modern/" if #{genre}.lower() in ["metal", "rock"] else "Misc/")) + #{artist} + "/" + #{_filename}')
afl.save()
