#!/usr/bin/env python3

from gi.repository import Gtk
from gi.repository import GObject

from src.Constants import UI_FOLDER
from src.Interface.Utils import BasicInterface

import os

class SHandler():
  
  def __init__(self, interface):
    self.interface = interface
  
  def searchMissingSearch(self, *args):
    self.interface.startSearch()
  
  def searchMissingClose(self, *args):
    self.interface.close()
  
  def onAcceptReplace(self, *args):
    self.interface.onAcceptReplace(*args)
  
  def onAcceptRemove(self, *args):
    self.interface.onAcceptRemove(*args)


class SearchMissing(BasicInterface):
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.browser = self.ts.browser
    self._loadInterface()
 
  def _loadInterface(self):
    self.builder = Gtk.Builder()
    ui_file = os.path.join(UI_FOLDER, 'SearchMissing.glade')
    self.builder.add_from_file(ui_file)
    # Connect signals
    self.shandler = SHandler(self)
    self.builder.connect_signals(self.shandler)
    # Setup main window
    self.main_window = self.builder.get_object('SearchMissing')
    if self.browser is not None:
      self.main_window.set_transient_for(self.browser.main_window)
  
  ## Start/Stop
  def start(self):
    self.updateInterface()
    self.main_window.show()
  
  def close(self):
    self.main_window.hide()
    self.ts.closeSecondary(refresh=True)
  
  ## Update interface
  def updateInterface(self):
    # find missing files
    self.missing_files = self.findMissingFiles()
    # hide completion
    self.showCompletion(False)
    if len(self.missing_files) > 0:
      # setup results grid
      self.setupResultsGrid()
    else:
      # show completion
      self.showCompletion()
      
  def findMissingFiles(self):
    # get all files
    all_files = self.db.getAllFiles()
    # search missing files
    missing_files = {}
    for single_file in all_files:
      if not self.ts.fileExists(single_file):
        missing_files[single_file] = None
    return missing_files
  
  def setupResultsGrid(self):
    # cleanup variables
    self.replace_entries = {}
    # clean results grid
    results_grid = self.builder.get_object('SearchMissingResults')
    children = results_grid.get_children()
    for child in children:
      child.destroy()
    # write new grid
    for single_file in self.missing_files:
      # create the file grid
      file_grid = Gtk.Grid()
      file_grid.set_orientation(Gtk.Orientation.VERTICAL)
      file_grid.set_row_spacing(3)
      #file_grid.set_column_spacing(5)
      file_grid.set_hexpand(True)
      name_label = Gtk.Label(self.ts.getFilePath(single_file))
      name_label.set_alignment(0, 0.5)
      name_label.set_hexpand(True)
      #name_label.set_selectable(True)
      replace_entry = Gtk.Entry()
      replace_entry.set_text(self.ts.getFilePath(single_file))
      confirm_button = Gtk.Button('Replace')
      confirm_button.connect('clicked', self.shandler.onAcceptReplace, [single_file, replace_entry, file_grid])
      remove_button = Gtk.Button('Delete')
      remove_button.connect('clicked', self.shandler.onAcceptRemove, [single_file, file_grid])
      hseparator = Gtk.Separator()
      hseparator.set_orientation(Gtk.Orientation.HORIZONTAL)
      # buttons box
      buttons_box = Gtk.Grid()
      buttons_box.set_orientation(Gtk.Orientation.HORIZONTAL)
      buttons_box.set_column_spacing(5)
      buttons_box.add(confirm_button)
      buttons_box.add(remove_button)
      # file grid
      file_grid.add(name_label)
      file_grid.add(replace_entry)
      file_grid.add(buttons_box)
      file_grid.add(hseparator)
      results_grid.add(file_grid)
      # add to replace entries list
      self.replace_entries[single_file] = replace_entry
    results_grid.show_all()
  
  def startSearch(self):
    # show searching message
    sw = Gtk.Window(title="Searching")
    sw.set_transient_for(self.main_window)
    sw.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
    sw.set_modal(True)
    sw.set_border_width(10)
    sw.set_default_size(100, 100)
    label = Gtk.Label('Searching')
    label.set_alignment(0.5, 0.5)
    label.set_hexpand(True)
    label.set_vexpand(True)
    sw.add(label)
    sw.show_all()
    # start timeout
    GObject.timeout_add(100, self.startSearchTimeout, sw)
  
  def startSearchTimeout(self, sw):
    self.searchFileIn(self.browser.root)
    self.updateResultsGrid()
    sw.destroy()
    return False # Stop timeout
  
  def searchFileIn(self, root):
    search_list = {}
    for single_file in self.missing_files:
      search_list[single_file.getName().lower()] = single_file
    for base, dirs, files in os.walk(root): # add a followlinks=True?
      # check file names
      for filename in files:
        # check file
        if filename.lower() in search_list:
          filepath = os.path.join(base, filename)
          single_file = search_list[filename.lower()]
          self.missing_files[single_file] = filepath
      # check folders and ignore folders starting with .
      for single_dir in dirs:
        # check folder
        if single_dir.lower() in search_list:
          filepath = os.path.join(base, single_dir)
          single_file = search_list[single_dir.lower()]
          self.missing_files[single_file] = filepath
        # check if I should ignore
        if single_dir.startswith("."):
          dirs.remove(single_dir)
    
  def updateResultsGrid(self):
    for single_file in self.missing_files:
      replace_path = self.missing_files[single_file]
      if replace_path is not None:
        replace_entry = self.replace_entries[single_file]
        replace_entry.set_text(replace_path)
  
  def onAcceptReplace(self, widget, data):
    # update database
    single_file, replace_entry, grid_widget = data
    replace_path = replace_entry.get_text()
    if os.path.exists(replace_path):
      self.ts.changeFilePath(single_file, replace_path)
      # destroy widgets
      grid_widget.destroy()
      # remove missing element
      self.removeMissing(single_file)
    # show completion
    if len(self.missing_files) == 0:
      self.showCompletion()
  
  def onAcceptRemove(self, widget, data):
    # update database
    single_file, grid_widget = data
    self.db.deleteFile(single_file)
    # destroy widgets
    grid_widget.destroy()
    # remove missing element
    self.removeMissing(single_file)
    # show completion
    if len(self.missing_files) == 0:
      self.showCompletion()
  
  def showCompletion(self, complete=True):
    missing_grid = self.builder.get_object('SearchMissingMainGrid')
    no_missing_label = self.builder.get_object('SearchMissingNoFiles')
    if complete:
      missing_grid.hide()
      no_missing_label.show()
    else:
      missing_grid.show()
      no_missing_label.hide()
  
  def removeMissing(self, single_file):
    del self.missing_files[single_file]
    del self.replace_entries[single_file]


def open(*args, **kwargs):
  sm = SearchMissing(*args, **kwargs)
  return sm
