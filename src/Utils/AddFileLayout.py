#!/usr/bin/env python3

import os

from src.Common import json_loads
from src.Common import json_dumps

UI_ENTRY = 1
UI_SEPARATOR = 2
UI_TOGGLE = 3

HORIZONTAL = 0
VERTICAL = 1

class UIElement():
  
  def __init__(self, utype, name=None):
    self.name = name
    self.utype = utype
  
  def getName(self):
    return self.name
  
  def getType(self):
    return self.utype
  
  def toList(self):
    return (self.getName(), self.getType())


class Field():
  
  def __init__(self, name, category, tags, label, default):
    self.name = name
    self.category = category
    self.tags = tags
    self.label = label
    self.default = default
  
  def getName(self):
    return self.name
  
  def getLabel(self):
    return self.label
  
  def getDefault(self):
    return self.default
  
  def getCategory(self):
    return self.category
  
  def getTags(self):
    return self.tags
  
  def getTagsList(self):
    if self.tags is None:
      return None
    else:
      tlist = []
      for tag in self.tags:
        tlist.append(tag.getCode())
      return tlist
  
  def toList(self):
    tags_list = self.getTagsList()
    return [self.getName(), self.category.getCode(), tags_list, self.getLabel(), self.getDefault()]
  

class EntryField(Field):
  
  def __init__(self, name, category, tags, label, default, autocomplete=False, allows_empty=False):
    super().__init__(name, category, tags, label, default)
    self.autocomplete = autocomplete
    self.allows_empty = allows_empty
  
  def getAutocomplete(self):
    return self.autocomplete
  
  def getAllowsEmpty(self):
    return self.allows_empty
  
  def toList(self):
    flist = super().toList()
    flist.extend((self.getAutocomplete(), self.getAllowsEmpty()))
    return flist


class ToggleField(Field):
  
  def __init__(self, name, category, tags, label, default, toggle=True, orientation=HORIZONTAL):
    super().__init__(name, category, tags, label, default)
    self.toggle = toggle
    self.orientation = orientation
  
  def getToggle(self):
    return self.toggle
  
  def getOrientation(self):
    return self.orientation
  
  def isHorizontal(self):
    return self.orientation == HORIZONTAL
  
  def isVertical(self):
    return self.orientation == VERTICAL
  
  def setOrientationHorizontal(self):
    self.orientation = HORIZONTAL
  
  def setOrientationVertical(self):
    self.orientation = VERTICAL
  
  def toList(self):
    flist = super().toList()
    flist.extend((self.getToggle(), self.getOrientation()))
    return flist


def validFieldName(method):
  def new(self, *args, **kwargs):
    name = args[0]
    if name in self.fields:
      return None
    else:
      return method(self, *args, **kwargs)
  return new


class AddFileLayout():
  
  def __init__(self, tm):
    self.tm = tm
    self.db = self.tm.getDatabase()
    self.config_folder = self.tm.config_folder
    self.layout_file = os.path.join(self.config_folder, 'addFileLayout.json')
    self.clean()
  
  def clean(self):
    self.ui = []
    self.fields = {}
    self.destination = '#{_filename_entry}'
  
  def setDestination(self, dest):
    self.destination = dest
  
  @validFieldName
  def addEntryField(self, name, category, tags=None, label=None, default=None, autocomplete=False, allows_empty=False):
    field = EntryField(name, category, tags, label, default, autocomplete, allows_empty)
    name = field.getName()
    uel = UIElement(UI_ENTRY, name)
    self.fields[name] = field
    self.ui.append(uel)
    return field
  
  def addSeparator(self):
    uel = UIElement(UI_SEPARATOR)
    self.ui.append(uel)
  
  @validFieldName
  def addToggleField(self, name, category, tags=None, label=None, default=None, horizontal=True):
    field = ToggleField(name, category, tags, label, default,toggle=True)
    if horizontal:
      field.setOrientationHorizontal()
    else:
      field.setOrientationVertical()
    self.fields[name] = field
    uel = UIElement(UI_TOGGLE, name)
    self.ui.append(uel)
  
  @validFieldName
  def addRadioField(self, name, category, tags=None, label=None, default=None, horizontal=True):
    field = ToggleField(name, category, tags, label, default, toggle=False)
    if horizontal:
      field.setOrientationHorizontal()
    else:
      field.setOrientationVertical()
    self.fields[name] = field
    uel = UIElement(UI_TOGGLE, name)
    self.ui.append(uel)
  
  def load(self, layout_file=None):
    if layout_file is None:
      layout_file = self.layout_file
    if not os.path.exists(layout_file):  
      return False
    with open(layout_file, 'r') as hand:
      data = hand.read()
    data = data.strip()
    ulist, flist, dest = json_loads(data)
    self.ui = self._listToUI(ulist)
    self.fields = self._listToFields(flist)
    self.destination = dest
  
  def _listToUI(self, ulist):
    ui = []
    for el in ulist:
      name, utype = el
      uel = UIElement(utype, name)
      ui.append(uel)
    return ui
  
  def _listToFields(self, flist):
    fields = {}
    for name in flist:
      ftype = self.getFieldType(name)
      params = flist[name]
      if ftype == UI_ENTRY:
        name, category_code, tags_list, label, default, autocomplete, allows_empty = params
        category = self.getCategoryFromCode(category_code)
        tags = self.getTagsFromList(tags_list)
        fields[name] = EntryField(name, category, tags, label, default, autocomplete, allows_empty)
      elif ftype == UI_TOGGLE:
        name, category_code, tags_list, label, default, toggle, orientation = params
        category = self.getCategoryFromCode(category_code)
        tags = self.getTagsFromList(tags_list)
        fields[name] = ToggleField(name, category, tags, label, default, toggle, orientation)
    return fields
  
  def getFieldType(self, name):
    for el in self.ui:
      if el.getName() == name:
        return el.getType()
    return None
  
  def getCategoryFromCode(self, category_code):
    if category_code is None:
      return None
    else:
      return self.db.getCategoryFromCode(category_code)
  
  def getTagsFromList(self, tlist):
    if tlist is None:
      return None
    tags = []
    for code in tlist:
      tag = self.tm.getTagFromCode(code)
      tags.append(tag)
    return tags
  
  def save(self, layout_file=None):
    if layout_file is None:
      layout_file = self.layout_file
    ulist = []
    for el in self.ui:
      ulist.append(el.toList())
    flist = {}
    for name in self.fields:
      field = self.fields[name]
      flist[name] = field.toList()
    data = (ulist, flist, self.destination)
    json_enc = json_dumps(data)
    with open(layout_file, 'w') as hand:
      hand.write(json_enc)

def start(*args, **kwargs):
  afl = AddFileLayout(*args, **kwargs)
  return afl
