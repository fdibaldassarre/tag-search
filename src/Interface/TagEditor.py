#!/usr/bin/env python3

import os

from gi.repository import Gtk

from src.Constants import MAIN_FOLDER
from src.Constants import UI_FOLDER

from src.Common import createTag
from src.Common import createMetaTag

from src.Interface.Utils import BasicInterface
from src.Interface.Utils import acceptInterfaceSignals
from src.Interface.Utils import ignoreSignals

class SHandler():

  def __init__(self, interface):
    self.interface = interface

  def editorAddCategory(self, *args):
    self.interface.addCategory(*args)
  
  def editorAddTag(self, *args):
    self.interface.addTag(*args)
  
  def editorEditCategory(self, *args):
    self.interface.editCategory(*args)
  
  def editorEditTag(self, *args):
    self.interface.editTag(*args)
  
  def editorDeleteCategory(self, *args):
    self.interface.deleteCategory(*args)
  
  def editorDeleteTag(self, *args):
    self.interface.deleteTag(*args)
  
  def editorClose(self, *args):
    self.interface.close()
  
  @acceptInterfaceSignals
  def editorEditCategoryName(self, *args):
    self.interface.setEditMetaData(*args)
  
  @acceptInterfaceSignals
  def editorEditTagName(self, *args):
    self.interface.setEditTagData(*args)

################
## Tag Editor ##
################

def requireUpdateInterface(method):
  def new(self, *args, **kwargs):
    res = method(self, *args, **kwargs)
    self.updateInterface()
    return res
  return new


class TagEditor(BasicInterface):
  
  def __init__(self, tm):
    super().__init__(tm)
    self.browser = self.tm.browser
    self._loadInterface()
  
  def _loadInterface(self):
    # Create builder
    self.builder = Gtk.Builder()
    ui_file = os.path.join(UI_FOLDER, 'TagEditor.glade')
    self.builder.add_from_file(ui_file)
    # Connect signals
    self.shandler = SHandler(self)
    self.builder.connect_signals(self.shandler)
    # Setup main window
    self.main_window = self.builder.get_object('TagEditor')
    if self.browser is not None:
      self.main_window.set_transient_for(self.browser.main_window)
  
  def updateInterface(self):
    self.initializeVariables()
    self.updateAllSelectors()
  
  def initializeVariables(self):
    self.meta_tags = self.tm.getAllMetaTags()
    self.tags = self.tm.getAllTags()
    # meta which can be eliminated
    self.deletable_meta_tags = []
    self.updateDeletableMetaTags()
  
  def updateDeletableMetaTags(self):
    tags_meta = []
    for tag in self.tags:
      if not tag.getMetaCode() in tags_meta:
        tags_meta.append(tag.getMetaCode())
    self.deletable_meta_tags.clear()
    for meta in self.meta_tags:
      if not meta.getCode() in tags_meta:
        self.deletable_meta_tags.append(meta)
  
  @ignoreSignals
  def updateAllSelectors(self):
    # -- Add section --
    self.updateMetaTagSelector('AddTagCategory', set_active=True)
    ## -- Edit section --
    self.updateMetaTagSelector('EditCategorySelect')
    self.updateTagSelector('EditTagSelect')
    self.updateMetaTagSelector('EditTagCategory')
    ## -- Delete section --
    self.updateDeletableMetaTagSelector('DeleteCategorySelect')
    self.updateTagSelector('DeleteTagSelect')
  
  ## Selector updaters
  def updateMetaTagSelector(self, name, set_active=False):
    meta_selector = self.builder.get_object(name)
    meta_selector.remove_all()
    for meta_tag in self.meta_tags:
      meta_selector.append_text(meta_tag.getName())
    if set_active:
      meta_selector.set_active(0)
    return meta_selector
  
  def updateDeletableMetaTagSelector(self, name):
    meta_selector = self.builder.get_object(name)
    meta_selector.remove_all()
    for meta_tag in self.deletable_meta_tags:
      meta_selector.append_text(meta_tag.getName())
    return meta_selector
  
  def updateTagSelector(self, name):
    tag_selector = self.builder.get_object(name)
    tag_selector.remove_all()
    for tag in self.tags:
      tag_selector.append_text(tag.getName())
    return tag_selector
  
  ## -- Database operations --
  # Add
  @requireUpdateInterface
  def addCategory(self, widget, data=None):
    name_entry = self.builder.get_object('AddCategoryName')
    magnitude_check = self.builder.get_object('AddCategoryMagnitude')
    meta_tag_name = name_entry.get_text()
    meta_has_magnitude = magnitude_check.get_active()
    new_meta = createMetaTag(meta_tag_name, meta_has_magnitude)
    res = self.tm.addMetaTag(new_meta)
    if res is None:
      self.showErrorWindow("Category already in database")
    else:
      self.showInfoWindow("Category added")
  
  @requireUpdateInterface
  def addTag(self, widget, data=None):
    name_entry = self.builder.get_object('AddTagName')
    cat_selector = self.builder.get_object('AddTagCategory')
    tag_name = name_entry.get_text()
    meta_id = cat_selector.get_active()
    meta = self.meta_tags[meta_id]
    tag_meta = meta.getCode()
    new_tag = createTag(tag_name, tag_meta)
    res = self.tm.addTag(new_tag)
    if res is None:
      self.showErrorWindow("Tag already in database")
    else:
      self.showInfoWindow("Tag added")

  # Edit
  @requireUpdateInterface
  def editCategory(self, widget, data = None):
    category_selector = self.builder.get_object('EditCategorySelect')
    name_entry = self.builder.get_object('EditCategoryName')
    meta_id = category_selector.get_active()
    if meta_id < 0:
      return True
    meta = self.meta_tags[meta_id]
    new_name = name_entry.get_text()
    res = self.tm.renameMetaTag(meta, new_name)
    if res is None:
      self.showErrorWindow("Duplicate name")
    else:
      self.showInfoWindow("Category edited")
  
  @requireUpdateInterface
  def editTag(self, widget, data = None):
    tag_selector = self.builder.get_object('EditTagSelect')
    name_entry = self.builder.get_object('EditTagName')
    cat_selector = self.builder.get_object('EditTagCategory')
    tag_id = tag_selector.get_active()
    if tag_id < 0:
      return True
    tag = self.tags[tag_id]
    new_name = name_entry.get_text()
    meta_id = cat_selector.get_active()
    if meta_id < 0:
      return True
    new_meta = self.meta_tags[meta_id]
    res = self.tm.renameTag(tag, new_name)
    if res is None:
      self.showErrorWindow("Duplicate name")
      return None
    else:
      self.tm.changeTagMeta(tag, new_meta)
      self.showInfoWindow("Tag edited")
  
  def setEditMetaData(self, meta_selector):
    meta_id = meta_selector.get_active()
    if meta_id < 0:
      return True
    meta = self.meta_tags[meta_id]
    name_entry = self.builder.get_object('EditCategoryName')
    name_entry.set_text(meta.getName())
    
  def setEditTagData(self, tag_selector):
    tag_id = tag_selector.get_active()
    if tag_id < 0:
      return True
    tag = self.tags[tag_id]
    name_entry = self.builder.get_object('EditTagName')
    name_entry.set_text(tag.getName())
    meta_tag = None
    for meta in self.meta_tags:
      if meta.getCode() == tag.getMetaCode():
        meta_tag = meta
        break
    meta_tag_index = self.meta_tags.index(meta_tag)
    cat_selector = self.builder.get_object('EditTagCategory')
    cat_selector.set_active(meta_tag_index)
  
  # Delete
  @requireUpdateInterface
  def deleteCategory(self, widget, data=None):
    # NOTE: to delete a MetaTag there must be no associated Tags
    cat_selector = self.builder.get_object('DeleteCategorySelect')
    meta_id = cat_selector.get_active()
    if meta_id < 0:
      return True
    meta = self.deletable_meta_tags[meta_id]
    self.tm.deleteMetaTag(meta)
    self.showInfoWindow("Category deleted")
  
  @requireUpdateInterface
  def deleteTag(self, widget, data = None):
    tag_selector = self.builder.get_object('DeleteTagSelect')
    tag_id = tag_selector.get_active()
    if tag_id < 0:
      return True
    tag = self.tags[tag_id]
    self.tm.deleteTag(tag)
    self.showInfoWindow("Tag deleted")
    
  ## Start/Stop
  def start(self):
    self.updateInterface()
    self.main_window.show()
  
  def close(self):
    self.main_window.hide()
    self.tm.closeSecondary(refresh=True)


def open(*args, **kwargs):
  editor = TagEditor(*args, **kwargs)
  return editor
