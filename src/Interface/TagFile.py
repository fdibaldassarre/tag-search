#!/usr/bin/env python3

import os

from gi.repository import Gtk
from gi.repository import Gdk

from src.Common import loadFile
from src.Common import createTag
from src.Common import createMetaTag

from src.Constants import MAIN_FOLDER
from src.Constants import CSS_FOLDER
from src.Constants import ICONS_FOLDER
from src.Constants import UI_FOLDER

from src.Interface.Utils import BasicInterface
from src.Interface.Utils import acceptInterfaceSignals
from src.Interface.Utils import ignoreSignals

MAGNITUDE_MAX = 5

####################
## SignalsHandler ##
####################

class SHandler():
  
  def __init__(self, interface):
    self.interface = interface
  
  ## Main
  @acceptInterfaceSignals
  def tfCloseMain(self, *args):
    self.interface.close()
  
  ## Meta selector
  @acceptInterfaceSignals
  def tfRefreshTagsGrid(self, *args):
    self.interface.refreshTagGrid()
  
  ## Add Tags buttons
  @acceptInterfaceSignals
  def tfAddMetaTag(self, *args):
    self.interface.addMetaTag()
  
  @acceptInterfaceSignals
  def tfAddTag(self, *args):
    self.interface.addTag()
  
  ## Search
  @acceptInterfaceSignals
  def tfSearchMatch(self, widget, model, path):
    tag = model[path] # tag[0] = code, tag[1] = name, tag[2] = meta
    self.interface.searchSelected(tag)
    return True
  
  ## Tag edit - Search
  @acceptInterfaceSignals
  def tfSearchTagToggle(self, *args, **kwargs):
    self.interface.searchTagToggled()
  
  @acceptInterfaceSignals
  def tfSearchTagMagnitudeChanged(self, *args):
    self.interface.searchTagMagnitudeChanged(*args)
  
  ## Tag edit - Main grid
  @acceptInterfaceSignals
  def tfTagToggled(self, *args, **kwargs):
    self.interface.tagToggled(*args, **kwargs)
  
  @acceptInterfaceSignals
  def tfTagMagnitudeChanged(self, *args, **kwargs):
    self.interface.tagMagnitudeChanged(*args, **kwargs)
  
#############
## TagFile ##
#############

class TagFile(BasicInterface):

  def __init__(self, tm, filepaths):
    super().__init__(tm)
    self._loadFiles(filepaths)
    self._setup()
    self._loadInterface()
  
  def _setup(self):
    self.initializeVariables()
  
  def initializeVariables(self):
    self.meta_tags = self.tm.getAllMetaTags()
    self.tags = self.tm.getAllTags()
    self.current_meta = self.meta_tags[0]
    # Load item tags
    self.items_tags = {}
    for single_file in self.files:
      single_item_tags = {}
      # set active tags
      tags_mag = self.tm.getTagsOfFile(single_file)
      for tag in self.tags:
        if tag.code in tags_mag:
          single_item_tags[tag] = tags_mag[tag.getCode()]
      self.items_tags[single_file] = single_item_tags
  
  @ignoreSignals
  def _loadInterface(self):
    # Load interface
    self.builder = Gtk.Builder.new()
    ui_file = os.path.join(UI_FOLDER, 'TagFile.glade')
    self.builder.add_from_file(ui_file)
    self._initializeInterfaceConstants()
    # Load css
    self._loadCss()
    # Signal handler
    self.shandler = SHandler(self)
    self.builder.connect_signals(self.shandler)
    # Finalize interface
    self._finalizeInterface()
  
  def _initializeInterfaceConstants(self):
    # Setup main window
    self.main_window = self.builder.get_object('TagFile')
  
  def _finalizeInterface(self):
    # Set title
    if len(self.files) == 1:
      single_file = self.files[0]
      self.main_window.set_title("Tag File " + single_file.name)
    else:
      self.main_window.set_title("Tag File: " + str(len(self.files)) + " files")
    # Create search entry
    self._createSearchEntry()
    # Create grids
    self.populateMainWindow()
    # Resize
    self.main_window.resize(400, 600)
  
  ################  
  ## Load Files ##
  ################
  def _loadFiles(self, filepaths):
    self.files = []
    for filepath in filepaths:
      db_files = self.tm.searchFileByFilepath(filepath)
      if len(db_files) == 0:
        # add to database
        single_file = loadFile(filepath)
        self.tm.addFile(single_file)
        # search again to find id # TODO: find a better way (use last inserted ids?)
        db_files = self.tm.searchFile(single_file)
      self.files.append(db_files[0])
  
  ########################
  ## Interface creation ##
  ########################
  def _createSearchEntry(self):
    ## Setup tags store
    store = self.builder.get_object("TFSearchTagsStore")
    for tag in self.tags:
      store.append([tag.getCode(), tag.getName(), tag.getMetaCode()])
    ## Create an entry with autocompletion (NOTE: Glade sucks)
    cell_area = Gtk.CellAreaBox()
    cell_area.set_name('searchentrysuggestions') # FIXME: does not assign the class correctly (Gtk bug most probabily)
    completion = Gtk.EntryCompletion.new_with_area(cell_area)
    # Set model
    model = self.builder.get_object("TFSearchTagsStore")
    completion.set_model(model)
    completion.set_text_column(1)
    # Settings
    completion.set_inline_completion(False)
    completion.set_popup_completion(True)
    completion.set_popup_set_width(True)
    completion.set_popup_single_match(True)
    completion.set_inline_selection(True)
    # Connect
    completion.connect("match-selected", self.shandler.tfSearchMatch)
    # Add to entry
    sentry = self.builder.get_object("TFSearchEntry")
    sentry.set_completion(completion)
    ### Create magnitude grid
    grid = self.builder.get_object("TFSearchTagMagnitude")
    # Create grid
    meter = []
    base_radio = None
    for i in range(MAGNITUDE_MAX + 1):
      if base_radio is None:
        vote_radio = Gtk.RadioButton()
        base_radio = vote_radio
      else:
        vote_radio = Gtk.RadioButton.new_from_widget(base_radio)
      meter.append(vote_radio)
      grid.add(vote_radio)
    # Connect signals
    i = 0
    for vote_radio in meter:
      vote_radio.connect("toggled", self.shandler.tfSearchTagMagnitudeChanged, i)
      i += 1
    grid.show_all()
    grid.hide()
  
  def populateMainWindow(self):
    self.log.info("populateMainWindow == Starting")
    self.tags_widget = {}
    ## Meta selector
    main_meta_selector = self.builder.get_object("TFCategorySelector")
    # Fill
    self.fillMetaTagSelector(main_meta_selector)
    # Set active
    count = 0
    active = 0
    for meta_tag in self.meta_tags:
      if meta_tag == self.current_meta:
        active = count
        break
      count += 1
    main_meta_selector.set_active(active)
    # Tags grids
    self.tags_grids = {}
    for meta_tag in self.meta_tags:
      self.tags_grids[meta_tag.code] = self._createTagGridFor(meta_tag)
    # Add the tags grids
    all_tags_grid = self.builder.get_object("TFTagsBox")
    self.emptyContainer(all_tags_grid)
    for code in self.tags_grids:
      grid = self.tags_grids[code]
      all_tags_grid.add(grid)
    # Setup add tag line
    tag_meta = self.builder.get_object("TFAddTagCategory")
    self.fillMetaTagSelector(tag_meta)
    tag_meta.set_active(0)
    # Refresh tag grid
    self.refreshTagGrid()
  
  #####################################
  ## Interface creation - Tags grids ##
  #####################################
  def _createTagGridFor(self, meta_tag):
    tags = []
    for tag in self.tags:
      if tag.meta == meta_tag.getCode():
        tags.append(tag)
    if meta_tag.has_magnitude:
      return self._createMagnitudeTagGrid(tags)
    else:
      return self._createToggleTagGrid(tags)
  
  def _createToggleTagGrid(self, tags):
    # Create a liststore
    liststore = Gtk.ListStore(int, str, bool)
    for tag in tags:
      if self._tagIsToggledInAllFiles(tag):
        active = True
      else:
        active = False
      liststore.append([tag.getCode(), tag.name, active])
    # Save to tags widget
    for tag in tags:
      self.tags_widget[tag] = liststore
    # Treeview
    treeview = Gtk.TreeView(model = liststore)
    treeview.set_hexpand(True)
    # Cell renderer
    renderer_toggle = Gtk.CellRendererToggle()
    column_toggle = Gtk.TreeViewColumn("", renderer_toggle, active = 2)
    renderer_toggle.connect("toggled", self.shandler.tfTagToggled, treeview)
    treeview.append_column(column_toggle)
    renderer_text = Gtk.CellRendererText()
    column_text = Gtk.TreeViewColumn("Tag", renderer_text, text = 1)
    treeview.append_column(column_text)
    treeview.set_search_column(1)
    # Add scrolled window
    scrolled_view = Gtk.ScrolledWindow()
    scrolled_view.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled_view.add(treeview) # NOTE: do NOT add with viewport since the widget has native scrolling
    scrolled_view.set_vexpand(True)
    return scrolled_view
  
  def _tagIsToggledInAllFiles(self, tag):
    for single_file in self.files:
      tags = self.items_tags[single_file]
      if tag in tags and tags[tag] == 1:
        pass
      else:
        return False
    return True
  
  def _createMagnitudeTagGrid(self, tags):
    self.log.info("createMagnitudeTagGrid == Starting")
    grid = Gtk.Grid()
    grid.set_hexpand(True)
    grid.set_border_width(10)
    grid.set_column_spacing(20)
    # create the top line
    top_label = Gtk.Label("Tags")
    grid.add(top_label)
    prev_attach = top_label
    for i in range(MAGNITUDE_MAX + 1):
      magn_label = Gtk.Label(str(i))
      grid.attach_next_to(magn_label, prev_attach, Gtk.PositionType.RIGHT, 1, 1)
      prev_attach = magn_label
    # create the tags lines
    prev_label = top_label
    for tag in tags:
      label = Gtk.Label(tag.name)
      meter = self._createTagMagnitudeMeterFor(tag)
      self.tags_widget[tag] = meter
      # attach the label
      grid.attach_next_to(label, prev_label, Gtk.PositionType.BOTTOM, 1, 1)
      prev_label = label
      # attach the meter
      prev_attach = label
      for element in meter:
        grid.attach_next_to(element, prev_attach, Gtk.PositionType.RIGHT, 1, 1)
        prev_attach = element
    scrolled_view = Gtk.ScrolledWindow()
    scrolled_view.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled_view.add_with_viewport(grid)
    scrolled_view.set_vexpand(True)
    return scrolled_view
  
  def _createTagMagnitudeMeterFor(self, tag):
    tag_magnitude = self._getBaseMagnitudeForAllFiles(tag)
    meter = []
    base_radio = None
    for i in range(MAGNITUDE_MAX + 1):
      if i == 0:
        vote_radio = Gtk.RadioButton()
        base_radio = vote_radio
      else:
        vote_radio = Gtk.RadioButton.new_from_widget(base_radio)
      if i == tag_magnitude:
        vote_radio.set_active(True)
      meter.append(vote_radio)
    i = 0
    for vote_radio in meter:
      vote_radio.connect("toggled", self.shandler.tfTagMagnitudeChanged, [tag, i] )
      i += 1
    return meter
  
  def _getBaseMagnitudeForAllFiles(self, tag):
    base_file = self.files[0]
    if tag in self.items_tags[base_file]:
      base_magnitude = self.items_tags[base_file][tag]
    else:
      base_magnitude = 0
    for single_file in self.files:
      magnitude = self.items_tags[single_file]
      if base_magnitude != 0 and tag in magnitude and magnitude[tag] == base_magnitude:
        pass
      elif base_magnitude == 0 and ( not tag in magnitude or magnitude[tag] == 0 ):
        pass
      else:
        return 0
    return base_magnitude
  
  ####################
  ## Interface Edit ##
  ####################
  def emptyContainer(self, cont):
    children = cont.get_children()
    for child in children:
      child.destroy()
  
  def fillMetaTagSelector(self, meta_selector):
    meta_selector.remove_all()
    # Add meta tags
    for meta_tag in self.meta_tags:
      meta_selector.append_text(meta_tag.getName())
  
  def refreshTagGrid(self):
    active_meta = self.getCurrentMetaSelector()
    current_meta = self.meta_tags[active_meta]
    # Show the corresponsing grid
    for meta_code in self.tags_grids:
      grid = self.tags_grids[meta_code]
      if meta_code == current_meta.getCode():
        grid.show_all()
      else:
        grid.hide()
  
  def getCurrentMetaSelector(self):
    main_meta_selector = self.builder.get_object("TFCategorySelector")
    return main_meta_selector.get_active()
  
  ################
  ## Start/Stop ##
  ################
  def show(self):
    self.main_window.show()
  
  def start(self):
    self.show()
  
  def close(self):
    self.main_window.hide()
    self.tm.close()
  
  ##############
  ## Load CSS ##
  ##############
  def _loadCss(self):
    # TODO: add css
    return None
    provider = self._addCssProvider()
    css_file = os.path.join(CSS_FOLDER, 'TagFile.css')
    provider.load_from_path(css_file)

  def _addCssProvider(self):
    display = Gdk.Display.get_default()
    screen = Gdk.Display.get_default_screen(display)
    provider = Gtk.CssProvider()
    Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    return provider
  
  #######################
  ## Tag Edit - Toggle ##
  #######################
  def tagToggled(self, renderer, path, treeview):
    model = treeview.get_model()
    # toggle the value
    model[path][2] = not model[path][2]
    status = model[path][2]
    # get tag id
    tag_code = model[path][0]
    tag = None
    for el in self.tags:
      if el.getCode() == tag_code:
        tag = el
    # Toggle
    self.toggleTag(tag, status)
  
  def toggleTag(self, tag, status=True):
    if tag is not None:
      if status:
        for single_file in self.files:
          item_tags = self.items_tags[single_file]
          if tag in item_tags and item_tags[tag] == 1:
            pass
          else:
            self.tm.addTagToFile(tag, single_file, 1, commit=False)
            self.items_tags[single_file][tag] = 1
      else:
        for single_file in self.files:
          item_tags = self.items_tags[single_file]
          if tag in item_tags and item_tags[tag] == 1:
            self.tm.removeTagFromFile(tag, single_file, commit=False)
            self.items_tags[single_file][tag] = 0
      # Commit changes to db
      self.tm.commit()
    return True
        
  ##########################
  ## Tag Edit - Magnitude ##
  ##########################
  def tagMagnitudeChanged(self, widget, data):
    tag = data[0]
    magnitude = data[1]
    if magnitude == 0:
      for single_file in self.files:
        tags_magnitude = self.items_tags[single_file]
        if tag in tags_magnitude and tags_magnitude[tag] > 0:
          self.tm.removeTagFromFile(tag, single_file, commit=False)
          self.items_tags[single_file][tag] = 0
        else:
          pass
    else:
      for single_file in self.files:
        tags_magnitude = self.items_tags[single_file]
        if tag in tags_magnitude and tags_magnitude[tag] > 0:
          self.tm.changeTagMagnitudeForFile(tag, single_file, magnitude, commit=False)
        else:
          self.tm.addTagToFile(tag, single_file, magnitude, commit=False)
        self.items_tags[single_file][tag] = magnitude
    # Commit changes
    self.tm.commit()
    return True
  
  ##################
  ## Add Tag/Meta ##
  ##################
  def addMetaTag(self):
    entry = self.builder.get_object("TFAddCategoryName")
    meta_tag_name = entry.get_text()
    entry.set_text('')
    meta_tag_name = meta_tag_name.strip()
    has_magn_entry = self.builder.get_object("TFAddCategoryMagnitude")
    meta_has_magnitude = has_magn_entry.get_active()
    new_meta = createMetaTag(meta_tag_name, meta_has_magnitude)
    res = self.tm.addMetaTag(new_meta)
    if res is None:
      self.showErrorWindow("Duplicate name")
    else:
      self.showInfoWindow("Category created")
      self.reloadMainWindow(new_meta.getCode())
  
  def addTag(self):
    entry = self.builder.get_object("TFAddTagName")
    tag_name = entry.get_text()
    entry.set_text('')
    tag_name = tag_name.strip()
    meta_entry = self.builder.get_object("TFAddTagCategory")
    meta_id = meta_entry.get_active()
    meta = self.meta_tags[meta_id]
    tag_meta = meta.getCode()
    new_tag = createTag(tag_name, tag_meta)
    res = self.tm.addTag(new_tag)
    if res is None:
      self.showErrorWindow("Duplicate name")
      return None
    # add tag to the files
    for single_file in self.files:
      self.tm.addTagToFile(new_tag, single_file, magnitude=1, commit=False)
    self.tm.commit()
    self.showInfoWindow("Tag created")
    self.reloadMainWindow(new_tag.getMetaCode())
  
  ############
  ## Search ##
  ############
  def searchSelected(self, tag):
    code = tag[0]
    name = tag[1]
    meta = tag[2]
    # Set search tag
    self.search_tag = None
    for tag in self.tags:
      if tag.getCode() == code:
        self.search_tag = tag
        break
    # Show name
    label = self.builder.get_object("TFSearchTagName")
    label.set_text(name)
    label.show()
    # Clear entry
    entry = self.builder.get_object("TFSearchEntry")
    entry.set_text("")
    # Get meta tag
    for meta_tag in self.meta_tags:
      if meta_tag.getCode() == meta:
        break
    # Show add/set magnitude
    magn_grid = self.builder.get_object("TFSearchTagMagnitude")
    btn = self.builder.get_object('TFSearchTagValue')
    if meta_tag.hasMagnitude():
      # show magnitude grid
      btn.hide()
      magn_grid.show()
      # find magnitude
      for index in range(MAGNITUDE_MAX + 1):
        if self.tags_widget[self.search_tag][index].get_active():
          break
      # set magnitude
      children = magn_grid.get_children()
      children[index].set_active(True)
    else:
      # show button
      magn_grid.hide()
      btn.show()
      if btn.get_active():
        # Add tag (no need to toggle twice)
        self.searchTagToggled()
      else:
        # Toggle button
        btn.set_active(True)
  
  def searchTagMagnitudeChanged(self, widget, index):
    tag = self.search_tag
    self.tags_widget[tag][index].set_active(True)

  def searchTagToggled(self):
    btn = self.builder.get_object('TFSearchTagValue')
    status = btn.get_active()
    # Toggle
    self.toggleTag(self.search_tag, status)
    # Update the interface
    model = self.tags_widget[self.search_tag]
    for el in model:
      if el[0] == self.search_tag.getCode():
        el[2] = status
        break
  
  ######################
  ## Interface reload ##
  ######################
  @ignoreSignals
  def reloadMainWindow(self, current_meta_code=None):
    self.initializeVariables()
    # update meta code
    if current_meta_code is not None:
      for meta_tag in self.meta_tags:
        if meta_tag.getCode() == current_meta_code:
          self.current_meta = meta_tag
    self.populateMainWindow()

######################
## Tag File Browser ##
######################

class TagFileBrowser(TagFile):
    
  def _loadFiles(self, filepaths):
    self.files = filepaths
  
  def start(self):
    self.main_window.set_transient_for(self.tm.browser.main_window)
    self.show()
  
  def close(self):
    self.tm.browser.reloadMainWindow()
    self.main_window.destroy()

def open(*args, **kwargs):
  tf = TagFile(*args, **kwargs)
  return tf

def openFromBrowser(*args, **kwargs):
  tf = TagFileBrowser(*args, **kwargs)
  return tf
  
