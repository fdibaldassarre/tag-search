#!/usr/bin/env python3

import os
import re
import shutil

from subprocess import Popen
from gi.repository import Gtk

from src.Constants import UI_FOLDER
from src.Common import createTag
from src.Interface.Utils import BasicInterface
from src.Utils.AddFileLayout import UI_ENTRY
from src.Utils.AddFileLayout import UI_SEPARATOR
from src.Utils.AddFileLayout import UI_TOGGLE
from src.Utils.Magic import guessMime

RE_DEPS = re.compile('#{[_a-z]*}')

class SHandler():
  
  def __init__(self, interface):
    self.interface = interface
  
  def updateDestination(self, *args, **kwargs):
    self.interface.updateDestination()
  
  def add(self, *args, **kwargs):
    self.interface.addFile()
  
  def close(self, *args, **kwargs):
    self.interface.close()


class PropertiesManager():
  
  def __init__(self, interface):
    self.interface = interface
  
  def get(self, name):
    if name in self.interface._custom_entries:
      field = self.interface.layout.fields[name]
      etype = self.interface.layout.getFieldType(name)
      if etype == UI_ENTRY:
        entry = self.interface._custom_entries[name]
        res = entry.get_text().strip()
        if res == '' and not field.getAllowsEmpty():
          res = self.interface._getFieldDefault(field)
        return res
      elif etype == UI_TOGGLE:
        field = self.interface.layout.fields[name]
        if field.getToggle():
          return self._getMultiple(name)
        else:
          # radio
          return self._getSingle(name)
      else:
        return None
    elif name == '_filename_entry':
      return self.interface.filename_entry.get_text().strip()
    elif name == '_filename':
      return self.interface.tfile.getName()
    elif name == '_mime':
      return self.interface.tfile.getMime()
    elif name == '_number_files':
      if self.interface.tfile.getMime() == 'inode/directory':
        # count the elements in the folder
        path = self.interface.tfile.getFilepath()
        return len(os.listdir(path))
      else:
        return 1
    else:
      return None
  
  def _getSingle(self, name):
    lst = self.interface._custom_entries[name]
    for el in lst:
      tag, wid = el
      if wid.get_active():
        return tag.getName()
  
  def _getMultiple(self, name):
    lst = self.interface._custom_entries[name]
    res = []
    for el in lst:
      tag, wid = el
      if wid.get_active():
        res.append(tag.getName())
    return res

class SimpleFile():
  
  def __init__(self, path):
    self.path = os.path.abspath(path)
    self.name = os.path.basename(self.path)
    self.mime = guessMime(self.path)
  
  def getFilepath(self):
    return self.path
  
  def getName(self):
    return self.name
  
  def getMime(self):
    return self.mime
  
class AddFile(BasicInterface):

  def __init__(self, ts, path):
    super().__init__(ts)
    self.tfile = SimpleFile(path)
    self.layout = self.ts.getAddFileLayout()
    self.properties = PropertiesManager(self)
    self._loadInterface()
  
  def _loadInterface(self):
    self.builder = Gtk.Builder.new()
    ui_file = os.path.join(UI_FOLDER, 'AddFile.glade')
    self.builder.add_from_file(ui_file)
    self.main_window = self.builder.get_object('AMMainWindow')
    self.main_window.set_title('Add file to ' + self.ts.getProfileName())
    filename_label = self.builder.get_object('AMLabelBasename')
    filename_label.set_text(self.tfile.getName())
    self.filename_entry = self.builder.get_object('AMEntryName')
    self.filename_entry.set_text(self.tfile.getName())
    self._custom_grid = self.builder.get_object('CustomGrid')
    self._custom_entries = {}
    self._composeInterface()
    self._connectSignals()
    self.updateDestination()
  
  def _composeInterface(self):
    for uel in self.layout.ui:
      self._addElement(uel)
  
  def _addElement(self, uel):
    name = uel.getName()
    if uel.getType() == UI_SEPARATOR:
      self._addSeparator()
    elif uel.getType() == UI_ENTRY:
      self._addEntry(name)
    elif uel.getType() == UI_TOGGLE:
      self._addToggle(name)
  
  def _addSeparator(self):
    sep = Gtk.Separator()
    sep.set_orientation(Gtk.Orientation.HORIZONTAL)
    self._custom_grid.add(sep)
  
  def _addEntry(self, name):
    field = self.layout.fields[name]
    default_value = self._getFieldDefault(field)
    label = field.getLabel()
    if label is None:
      label = name
    nlabel = Gtk.Label(label + ':')
    grid = Gtk.Grid()
    grid.set_column_spacing(5)
    grid.set_orientation(Gtk.Orientation.HORIZONTAL)
    grid.add(nlabel)
    entry = Gtk.Entry()
    entry.set_hexpand(True)
    if default_value is not None:
      entry.set_text(default_value)
    grid.add(entry)
    self._custom_entries[name] = entry
    if field.getAutocomplete():
      self._setupAutocomplete(name)
    self._custom_grid.add(grid)
  
  def _setupAutocomplete(self, name):
    field = self.layout.fields[name]
    tags = field.getTags()
    if tags is None:
      cat = field.getCategory()
      tags = self.db.getAllTagsWithCategory(cat)
    store = Gtk.ListStore(int, str)
    for tag in tags:
      store.append([tag.getCode(), tag.getName()])
    # Setup completion
    cell_area = Gtk.CellAreaBox()
    completion = Gtk.EntryCompletion.new_with_area(cell_area)
    ## Set model
    completion.set_model(store)
    completion.set_text_column(1)
    ## Settings
    completion.set_inline_completion(False)
    completion.set_popup_completion(True)
    completion.set_popup_set_width(True)
    completion.set_popup_single_match(True)
    completion.set_inline_selection(True)
    ## Add to entry
    sentry = self._custom_entries[name]
    sentry.set_completion(completion)
  
  def _addToggle(self, name):
    field = self.layout.fields[name]
    toggle = field.getToggle()
    defaults = self._getFieldDefault(field)
    if defaults is None:
      defaults = []
    tags = field.getTags()
    if tags is None:
      cat = field.getCategory()
      tags = self.db.getAllTagsWithCategory(cat)
    base_radio = None
    grid = Gtk.Grid()
    entries = []
    if field.isHorizontal():
      grid.set_orientation(Gtk.Orientation.HORIZONTAL)
    else:
      grid.set_orientation(Gtk.Orientation.VERTICAL)
    for tag in tags:
      if base_radio is None:
        if toggle:
          wid = Gtk.CheckButton.new_with_label(tag.getName())
        else:
          wid = Gtk.RadioButton.new_with_label(None, tag.getName())
          base_radio = wid
      else:
        wid = Gtk.RadioButton.new_with_label_from_widget(base_radio, tag.getName())
      if tag.getName() in defaults:
        wid.set_active(True)
      entries.append((tag, wid))
      grid.add(wid)
    self._custom_entries[name] = entries
    self._custom_grid.add(grid)
  
  def _getFieldDefault(self, field):
    default = field.getDefault()
    if default is None:
      return None
    else:
      return self.getEvaluation(default)
  
  def _connectSignals(self):
    self.shandler = SHandler(self)
    self.builder.connect_signals(self.shandler)
    self._connectUpdateDestination()
  
  def _connectUpdateDestination(self):
    depends = self._getDestinationDepends()
    for name in depends:
      if name in self._custom_entries:
        etype = self.layout.getFieldType(name)
        if etype == UI_ENTRY:
          entry = self._custom_entries[name]
          entry.connect('changed', self.shandler.updateDestination)
        elif etype == UI_TOGGLE:
          lst = self._custom_entries[name]
          toggle = self.layout.fields[name].getToggle()
          for el in lst:
            tag, wid = el
            wid.connect('toggled', self.shandler.updateDestination)
            if toggle:
              break
      elif name == 'filename':
        entry = self.builder.get_object('AMEntryName')
        entry.connect('changed', self.shandler.updateDestination)
  
  def _getDestinationDepends(self):
    # deps are elements in #{...}
    deps = []
    tmp = RE_DEPS.findall(self.layout.destination)
    for el in tmp:
      clean = el[2:-1]
      if not clean in deps:
        deps.append(clean)
    return deps
    
  def show(self):
    self.main_window.show_all()
  
  def close(self):
    self.main_window.destroy()
    self.ts.close()
  
  def addFile(self):
    self.updateDestination()
    dest = self.getFullDestination()
    if os.path.exists(dest):
      self.showErrorWindow('Destination exists', 'Please select another destination.')
      return True
    # Create dest folder
    dest_folder = os.path.dirname(dest)
    if not os.path.exists(dest_folder):
      os.makedirs(dest_folder)
    # Move file
    shutil.move(self.tfile.getFilepath(), dest)
    # Open dest folder
    if os.path.isdir(dest):
      folder = dest
    else:
      folder = os.path.dirname(dest)
    self._addFileAndTags(dest)
    p = Popen(['xdg-open', folder])
    # Hide add file (do not close or TagSearch shuts down)
    self.main_window.hide()
    # Open TagFile
    self.ts.openTagFile(dest)
  
  def _addFileAndTags(self, dest):
    mfile = self.ts.loadFile(dest)
    self.db.addFile(mfile, commit=False)
    self._addTags(mfile)
    self.db.commit()
  
  def _addTags(self, mfile):
    for name in self._custom_entries:
      field = self.layout.fields[name]
      etype = self.layout.getFieldType(name)
      if etype == UI_ENTRY:
        entry = self._custom_entries[name]
        tag_name = entry.get_text().strip()
        if tag_name == '' and not field.getAllowsEmpty():
          tag_name = self._getFieldDefault(field)
        if tag_name == '':
          tag = None
        else:
          tag = self.db.getTagFromName(tag_name)
        if tag is None:
          cat = self.layout.fields[name].getCategory()
          tag = createTag(tag_name, cat.getCode())
          self.db.addTag(tag)
        self.db.addTagToFile(tag, mfile, commit=False)
      elif etype == UI_TOGGLE:
        lst = self._custom_entries[name]
        for el in lst:
          tag, wd = el
          if wd.get_active():
            self.db.addTagToFile(tag, mfile, commit=False)
  
  def updateDestination(self):
    dest = self.getDestination()
    dest_label = self.builder.get_object('DestinationLabel')
    dest_label.set_text('Destination: ' + dest)
  
  def getDestination(self):
    return self.getEvaluation(self.layout.destination)
  
  def getEvaluation(self, string):
    valuable = string.replace('#', 'self.properties.get').replace('{', '("').replace('}', '")')
    res = eval(valuable)
    return res
  
  def getFullDestination(self):
    dest = self.getDestination()
    return self.ts.getCompletePath(dest)
  
def open(*args, **kwargs):
  af = AddFile(*args, **kwargs)
  return af
