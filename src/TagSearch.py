#!/usr/bin/env python3

import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src.Constants import DEBUG
from src.Utils import PyLog
from src.Utils import AddFileLayout
from src.Database import Database

from src.Interface import Browser
from src.Interface import TagFile
from src.Interface import AddFile
from src.Interface import TagEditor
from src.Interface import SearchMissing

class TagSearch(Database):
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._setupLogger(DEBUG)
    self._initializeVariables()
  
  def _initializeVariables(self):
    self.browser = None
    self.tag_file = None
    # Secondary windows
    self.tag_editor = None
  
  def loadDefaultConfig(self):
    config = {}
    config['root'] = os.path.join(os.environ['HOME'], 'TagSearch/')
    config['use_magnitude'] = False
    return config
  
  def _setupLogger(self, debug=False):
    log_folder = os.path.join(self.config_folder, 'logs/')
    self.logger = PyLog.new(log_folder)
    if debug:
      self.log = self.logger.createDebugLogger('main.log')
    else:
      self.log = self.logger.createInfoLogger('main.log')
  
  def openBrowser(self):
    self.browser = Browser.open(self)
    self.browser.start()
  
  def openBrowserTagFile(self, paths):
    tag_file = TagFile.openFromBrowser(self, paths)
    tag_file.start()
  
  def openTagFile(self, path):
    tag_file = TagFile.open(self, [path])
    tag_file.start()
  
  def openTagEditor(self):
    if self.tag_editor is None:
      self.tag_editor = TagEditor.open(self)
    self.tag_editor.start()
  
  def openAddFile(self, filepath):
    add_file = AddFile.open(self, filepath)
    add_file.show()
  
  def openSearchMissing(self):
    search_missing = SearchMissing.open(self)
    search_missing.start()
  
  def getAddFileLayout(self):
    adf = AddFileLayout.start(self)
    adf.load()
    return adf
  
  def start(self):
    Gtk.main()
  
  def close(self):
    Gtk.main_quit()
  
  def closeSecondary(self, refresh=False):
    if self.browser is None and self.tag_file is None:
      self.close()
    elif refresh:
      self.browser.reloadMainWindow()

def start(*args, **kwargs):
  ui = TagSearch(*args, **kwargs)
  return ui
