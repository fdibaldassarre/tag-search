#!/usr/bin/env python3

import os

from gi.repository import Gtk

from src.Constants import MAIN_FOLDER
from src.Constants import UI_FOLDER

from src.Common import createTag
from src.Common import createCategory

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
    self.browser = self.ts.browser
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
    self.categories = self.db.getAllCategories()
    self.tags = self.db.getAllTags()
    # category which can be eliminated
    self.deletable_categories = []
    self.updateDeletableCategories()
  
  def updateDeletableCategories(self):
    tags_category = []
    for tag in self.tags:
      if not tag.getCategory() in tags_category:
        tags_category.append(tag.getCategory())
    self.deletable_categories.clear()
    for category in self.categories:
      if not category.getCode() in tags_category:
        self.deletable_categories.append(category)
  
  @ignoreSignals
  def updateAllSelectors(self):
    # -- Add section --
    self.updateCategorySelector('AddTagCategory', set_active=True)
    ## -- Edit section --
    self.updateCategorySelector('EditCategorySelect')
    self.updateTagSelector('EditTagSelect')
    self.updateCategorySelector('EditTagCategory')
    ## -- Delete section --
    self.updateDeletableCategorySelector('DeleteCategorySelect')
    self.updateTagSelector('DeleteTagSelect')
  
  ## Selector updaters
  def updateCategorySelector(self, name, set_active=False):
    category_selector = self.builder.get_object(name)
    category_selector.remove_all()
    for category in self.categories:
      category_selector.append_text(category.getName())
    if set_active:
      category_selector.set_active(0)
    return category_selector
  
  def updateDeletableCategorySelector(self, name):
    category_selector = self.builder.get_object(name)
    category_selector.remove_all()
    for category in self.deletable_categories:
      category_selector.append_text(category.getName())
    return category_selector
  
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
    category_name = name_entry.get_text()
    category_has_magnitude = magnitude_check.get_active()
    new_category = createCategory(category_name, category_has_magnitude)
    res = self.db.addCategory(new_category)
    if res is None:
      self.showErrorWindow("Category already in database")
    else:
      self.showInfoWindow("Category added")
  
  @requireUpdateInterface
  def addTag(self, widget, data=None):
    name_entry = self.builder.get_object('AddTagName')
    cat_selector = self.builder.get_object('AddTagCategory')
    tag_name = name_entry.get_text()
    category_id = cat_selector.get_active()
    category = self.categories[category_id]
    tag_category = category.getCode()
    new_tag = createTag(tag_name, tag_category)
    res = self.db.addTag(new_tag)
    if res is None:
      self.showErrorWindow("Tag already in database")
    else:
      self.showInfoWindow("Tag added")

  # Edit
  @requireUpdateInterface
  def editCategory(self, widget, data = None):
    category_selector = self.builder.get_object('EditCategorySelect')
    name_entry = self.builder.get_object('EditCategoryName')
    category_id = category_selector.get_active()
    if category_id < 0:
      return True
    category = self.categories[category_id]
    new_name = name_entry.get_text()
    res = self.db.renameCategory(category, new_name)
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
    category_id = cat_selector.get_active()
    if category_id < 0:
      return True
    new_category = self.categories[category_id]
    res = self.db.renameTag(tag, new_name)
    if res is None:
      self.showErrorWindow("Duplicate name")
      return None
    else:
      self.db.changeTagCategory(tag, new_category)
      self.showInfoWindow("Tag edited")
  
  def setEditMetaData(self, category_selector):
    category_id = category_selector.get_active()
    if category_id < 0:
      return True
    category = self.categories[category_id]
    name_entry = self.builder.get_object('EditCategoryName')
    name_entry.set_text(category.getName())
    
  def setEditTagData(self, tag_selector):
    tag_id = tag_selector.get_active()
    if tag_id < 0:
      return True
    tag = self.tags[tag_id]
    name_entry = self.builder.get_object('EditTagName')
    name_entry.set_text(tag.getName())
    category = None
    for cat in self.categories:
      if cat.getCode() == tag.getCategory():
        category = cat
        break
    category_index = self.categories.index(category)
    cat_selector = self.builder.get_object('EditTagCategory')
    cat_selector.set_active(category_index)
  
  # Delete
  @requireUpdateInterface
  def deleteCategory(self, widget, data=None):
    # NOTE: to delete a Category there must be no associated Tags
    cat_selector = self.builder.get_object('DeleteCategorySelect')
    category_id = cat_selector.get_active()
    if category_id < 0:
      return True
    category = self.deletable_categories[category_id]
    self.db.deleteCategory(category)
    self.showInfoWindow("Category deleted")
  
  @requireUpdateInterface
  def deleteTag(self, widget, data = None):
    tag_selector = self.builder.get_object('DeleteTagSelect')
    tag_id = tag_selector.get_active()
    if tag_id < 0:
      return True
    tag = self.tags[tag_id]
    self.db.deleteTag(tag)
    self.showInfoWindow("Tag deleted")
    
  ## Start/Stop
  def start(self):
    self.updateInterface()
    self.main_window.show()
  
  def close(self):
    self.main_window.hide()
    self.ts.closeSecondary(refresh=True)


def open(*args, **kwargs):
  editor = TagEditor(*args, **kwargs)
  return editor
