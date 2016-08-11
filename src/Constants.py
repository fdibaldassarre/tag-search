#!/usr/bin/env python3

import os

DEBUG = True

path = os.path.abspath(__file__)
SRC_FOLDER = os.path.dirname(path)
MAIN_FOLDER = os.path.dirname(SRC_FOLDER)
SQL_FOLDER = os.path.join(MAIN_FOLDER, 'sql/')
UI_FOLDER = os.path.join(MAIN_FOLDER, 'ui/')
ICONS_FOLDER = os.path.join(MAIN_FOLDER, 'icons/')
CSS_FOLDER = os.path.join(MAIN_FOLDER, 'css/')
