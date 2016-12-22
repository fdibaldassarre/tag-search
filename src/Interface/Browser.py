#!/usr/bin/env python3

import os 
import configparser
from subprocess import Popen

from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository.GdkPixbuf import Pixbuf

from src.Constants import MAIN_FOLDER
from src.Constants import ICONS_FOLDER
from src.Constants import UI_FOLDER

from src.Interface import TagEditor

from src.Interface.Utils import BasicInterface
from src.Interface.Utils import acceptInterfaceSignals
from src.Interface.Utils import ignoreSignals

VIDEO_MIMES = ["video/x-msvideo", "video/x-matroska", "video/mp4", "video/x-ogm+ogg"]
IMAGE_MIMES = ["image/gif", "image/png", "image/jpeg", "application/pdf", "image/vnd.djvu"]

RESULT_LIMIT = 20
ICON_SIZE = 64

LABEL_LIMIT = 20

THUMBNAILS_EXTENSION = '.png'

#############
### Tools ###
#############

## PsuedoTag
class PseudoTag():
  
  def __init__(self, name):
    self.name = name
  
  def getName(self):
    return self.name

## PsuedoCategory
class PseudoCategory():
  
  def __init__(self, name):
    self.name = name
  
  def getName(self):
    return self.name


## Signals Handler

class SHandler():

  def __init__(self, interface):
    self.interface = interface
  
  @acceptInterfaceSignals
  def searchTagName(self, *args):
    self.interface.tagNameSearch(*args)
  
  @acceptInterfaceSignals
  def clickOnFile(self, *args):
    self.interface.clickOnFile(*args)
  
  @acceptInterfaceSignals
  def addTagInSearch(self, *args):
    self.interface.addTagInSearch(*args)
  
  @acceptInterfaceSignals
  def removeTagFromSearch(self, *args):
    self.interface.removeTagFromSearch(*args)
  
  @acceptInterfaceSignals
  def changeCategory(self, *args):
    self.interface.changeCategory(*args)
  
  @acceptInterfaceSignals
  def changeName(self, *args):
    self.interface.searchFiles()
  
  @acceptInterfaceSignals
  def loadMoreImages(self, *args):
    self.interface.loadMoreImages()
  
  def closeBrowser(self, *args):
    self.interface.close()
  
  # Settings
  def settingsShow(self, *args):
    self.interface.settingsShow(*args)
  
  def settingsClose(self, *args):
    self.interface.settingsClose()
  
  def settingsChangeRoot(self, *args):
    self.interface.settingsChangeRoot(*args)
  
  def settingsChangeMagnitude(self, *args):
    self.interface.settingsChangeMagnitude(*args)
  
##################
## Browser Menu ##
##################

class BrowserMenu():
  
  def __init__(self, browser):
    self.browser = browser
    self.main_window = self.browser.main_window
    # create base action group
    self.base_actions_group = Gio.SimpleActionGroup()
    self.addToolsActions(self.base_actions_group)
    # add action group to the browser
    self.main_window.insert_action_group("menu_actions", self.base_actions_group)
    # create file actions group
    self.file_actions_group = Gio.SimpleActionGroup()
    self.addFileViewActions(self.file_actions_group)
  
  def addToolsActions(self, group):
    # tag editor
    tag_editor_action = Gio.SimpleAction.new("create_tag_editor")
    tag_editor_action.connect("activate", self.browser.showTagEditor)
    group.add_action(tag_editor_action)
    # search untagged
    search_untagged_action = Gio.SimpleAction.new("search_untagged_files")
    search_untagged_action.connect("activate", self.browser.searchUntaggedFiles)
    group.add_action(search_untagged_action)
    # search missing
    search_missing_action = Gio.SimpleAction.new("search_missing_files")
    search_missing_action.connect("activate", self.browser.openSearchMissingWindow)
    group.add_action(search_missing_action)

  def addFileViewActions(self, group):
    # open folder
    open_folder_action = Gio.SimpleAction.new("open_folder")
    open_folder_action.connect("activate", self.browser.openFolder)
    group.add_action(open_folder_action)
    # tag file
    tag_file_action = Gio.SimpleAction.new("tag_file")
    tag_file_action.connect("activate", self.browser.createTagFileWindow)
    group.add_action(tag_file_action)
    # remove file
    remove_file_action = Gio.SimpleAction.new("remove_file")
    remove_file_action.connect("activate", self.browser.removeFile)
    group.add_action(remove_file_action)
    
  ## Models
  def getToolsModel(self):
    menu = Gio.Menu()
    ## tag editor
    menu.append("Tag editor", 'menu_actions.create_tag_editor')
    ## search untagged
    menu.append("Search untagged files", 'menu_actions.search_untagged_files')
    ## search missing
    menu.append("Search missing files", 'menu_actions.search_missing_files')
    return menu

  def getFileActionsModel(self):
    menu = Gio.Menu()
    ## open
    open_action = Gio.MenuItem.new("Open Folder", 'file_actions.open_folder')
    open_icon = Gio.ThemedIcon.new('gtk-open')
    open_action.set_icon(open_icon)
    menu.insert_item(0, open_action)
    ## edit
    edit = Gio.MenuItem.new("Edit Tags", 'file_actions.tag_file')
    edit_icon = Gio.ThemedIcon.new('gtk-edit')
    edit.set_icon(edit_icon)
    menu.insert_item(1, edit)
    ## remove
    remove = Gio.MenuItem.new("Remove File", 'file_actions.remove_file')
    remove_icon = Gio.ThemedIcon.new('gtk-delete')
    remove.set_icon(remove_icon)
    menu.insert_item(2, remove)
    return menu

  ## Attachments
  def attachFileActionsTo(self, group):
    group.insert_action_group("file_actions", self.file_actions_group)


#############
## Browser ##
#############
class Browser(BasicInterface):

  def __init__(self, ts):
    super().__init__(ts)
    self._setup()
    self._loadInterface()
  
  def _setup(self):
    self.profile = self.ts.getProfileName()
    self.thumbnails_folder = os.path.join(self.ts.config_folder, "thumbnails/")
    if not os.path.exists(self.thumbnails_folder):
      os.mkdir(self.thumbnails_folder)
    # Inizialize variables
    self.initializeVariables()
  
  ##########################
  ## Interface - Creation ##
  ##########################
  def _loadInterface(self):
    # Build interface
    self.builder = Gtk.Builder()
    ui_file = os.path.join(UI_FOLDER, 'Browser.glade')
    self.builder.add_from_file(ui_file)
    self._initializeInterfaceConstants()
    # Load Menu manager
    self.menu_manager = BrowserMenu(self)
    # load accelerators
    self._loadAccels()
    # Initialize UI Stores
    self.updateFilesStore()
    # Connect signals
    self.shandler = SHandler(self)
    self.builder.connect_signals(self.shandler)
    # Finalize
    self._finalizeInterface()
  
  def _loadAccels(self):
    accels = Gtk.AccelGroup()
    accelerator = '<control>q'
    key, mod = Gtk.accelerator_parse(accelerator)
    accels.connect(key, mod, Gtk.AccelFlags.LOCKED, self.close)
    self.main_window.add_accel_group(accels)
  
  def _finalizeInterface(self):
    self.log.info("_finalizeInterface == Finalizing")
    # Header
    self._createHeader()
    # Logo
    self._setLogo()
    self.no_tags_available_label.set_size_request(170, 0)
    # Tags selector
    self.createTagsGrid()
    # resize window
    self.main_window.resize(1300, 800)
    # update files view    
    self.log.info("_finalizeInterface == Update the files view")
    self.updateFilesView()
    # update category selector
    self.log.info("_finalizeInterface == Update the category selector")
    self.updateCategorySelector()
  
  def _createHeader(self):
    # menus
    model = self.menu_manager.getFileActionsModel()
    self.files_view_menu = Gtk.Menu.new_from_model(model)
    self.menu_manager.attachFileActionsTo(self.files_view_menu)
    # header
    header = Gtk.HeaderBar(title = "TagBrowser")
    header.set_subtitle("profile: " + self.profile)
    header.set_show_close_button(True)
    # options button
    button = Gtk.Button()
    pixbuf = Gtk.IconTheme.get_default().load_icon(Gtk.STOCK_PREFERENCES, 16, 0)
    icon = Gtk.Image()
    icon.set_from_pixbuf(pixbuf)
    button.add(icon)
    button.connect("clicked", self.shandler.settingsShow)
    header.pack_end(button)
    # tools button
    button = Gtk.MenuButton()
    pixbuf = Gtk.IconTheme.get_default().load_icon(Gtk.STOCK_EXECUTE, 16, 0)
    icon = Gtk.Image()
    icon.set_from_pixbuf(pixbuf)
    button.add(icon)
    # read the menu model
    menu_model = self.menu_manager.getToolsModel()
    button.set_menu_model(menu_model)
    header.pack_start(button)
    # set titlebar and show
    self.main_window.set_titlebar(header)
    header.show_all()
  
  def _setLogo(self):
    # logo
    logo = self.builder.get_object('Logo')
    logo_file = os.path.join(ICONS_FOLDER, "logo-custom.png")
    if not os.path.exists(logo_file):
      logo_file = os.path.join(ICONS_FOLDER, "logo.png")
    logo.set_from_pixbuf(Pixbuf.new_from_file(logo_file))
  
  #############################
  ## Variable initialization ##
  #############################
  def initializeVariables(self, used_tags=None):
    self.log.info("initializeVariables == Initialize variables")
    # Config
    self.reloadConfig()
    # Tags and Categories lists
    self.categories = self.db.getAllCategories()
    self.tags = self.db.getAllTags()
    # Current used tags/category
    self.current_category = None
    self.used_tags = []
    if used_tags is not None:
      self._importUsedTags(used_tags)
    # Current files
    self.files = self.db.getFilesWithTags(self.used_tags, self.use_magnitude)
    # Status
    self.files_results_limit = RESULT_LIMIT
    # Available tags and categories
    self.available_tags = []
    self.available_categories = [PseudoCategory('')]
    self.updateAvailableTags()
    self.updateAvailableCategories()
    # Interface related
    self.require_files_view_deferred_update = False
  
  def reloadConfig(self):
    self.root = self.ts.config['root']
    self.use_magnitude = self.ts.config['use_magnitude']
  
  def _importUsedTags(self, old_used_tags):
    for tag in old_used_tags:
      for new_tag in self.tags:
        if new_tag.getName() == tag.getName():
          self.used_tags.append(new_tag)
    
  def _initializeInterfaceConstants(self):
    self.log.info("_initializeInterfaceConstants == Initialize interface constants")
    self.main_window = self.builder.get_object('Browser')
    self.settings_window = self.builder.get_object('SettingsWindow')
    self.used_tags_view = self.builder.get_object('UsedTagsList')
    self.category_selector = self.builder.get_object('CategorySelector')
    self.no_tags_available_label = self.builder.get_object('NoTagsAvailable')
    self.files_view = self.builder.get_object('FilesView')
    self.files_view.set_text_column(1)
    self.files_view.set_pixbuf_column(2)
    self.load_more_files_button = self.builder.get_object('LoadMoreFiles')
    self.files_store = self.builder.get_object('FilesStore')
    self.tag_name_filter = self.builder.get_object('TagSearch')
  
  def updateFilesStore(self):
    self.log.info("updateFilesStore == Update Files store")
    self.files_store.clear()
    for single_file in self.files:
      if len(self.files_store) == self.files_results_limit:
        break
      else:
        file_pixbuf = self.getFilePixbuf(single_file)
        self.files_store.append([single_file.getCode(), single_file.getName(), file_pixbuf])
    if self.require_files_view_deferred_update:
      self.require_files_view_deferred_update = False
      self.triggerFilesViewUpdate(True)
  
  ##################
  ## Start / Stop ##
  ##################
  def show(self):
    self.main_window.show()
  
  def start(self):
    self.show()
  
  def close(self, *args):
    self.main_window.hide()
    self.ts.close()
  
  ###################
  ## Display utils ##
  ###################
  def limitNameLenght(self, string):
    if len(string) > LABEL_LIMIT:
      new_string = string[0:LABEL_LIMIT-5] + "..." + string[-4:]
    else:
      new_string = string
    return new_string
  
  ################################
  ## Interface - Grids creation ##
  ################################
  def reloadMainWindow(self, *args):
    self.log.info('reloadMainWindow == Start')
    # re-set the variables
    old_used_tags = self.used_tags.copy()
    self.initializeVariables(old_used_tags)
    # re-create the tags grid
    self.createTagsGrid()
    # name contains
    name_entry = self.builder.get_object('BrowserSearchName')
    name_contains = name_entry.get_text().strip()
    if name_contains == '':
      name_contains = None
    # find the files
    self.files = self.db.getFilesWithTags(self.used_tags, self.use_magnitude, name_contains=name_contains)
    self.updateFilesStore()
    # reload the interface
    self.updateCategorySelector()
    self.updateUsedTagsView()
    self.updateFilesView()
    self.log.info('reloadMainWindow == End')
  
  def createTagsGrid(self):
    tags_grid = self.builder.get_object("TagsList")
    self.emptyContainer(tags_grid)
    self.tags_grids = {}
    for tag in self.tags:
      tag_button = Gtk.LinkButton()
      tag_name = self.limitNameLenght(tag.getName())
      tag_button.set_label(tag_name)
      tag_button.set_size_request(160, 0)
      tag_button.connect("activate-link", self.shandler.addTagInSearch, tag)
      tags_grid.add(tag_button)
      self.tags_grids[tag] = tag_button
  
  def emptyContainer(self, cont):
    children = cont.get_children()
    for child in children:
      child.destroy()
  
  @ignoreSignals
  def updateCategorySelector(self):
    self.log.info("updateCategorySelector == Start")
    self.category_selector.remove_all()
    for category in self.available_categories:
      self.category_selector.append_text(category.getName())
    if not self.current_category in self.available_categories:
      index = 0
    else:
      index = self.available_categories.index(self.current_category)
    self.category_selector.set_active(index)
    self.changeCategory()
    # show/hide
    if len(self.available_categories) == 1:
      self.category_selector.hide()
    else:
      self.category_selector.show_all()

  def updateTagsGrid(self):
    self.log.info("updateTagsGrid == Start")
    tags_grid_is_empty = True
    search_term = self.tag_name_filter.get_text()
    # show grid
    for tag in self.tags_grids:
      btn = self.tags_grids[tag]
      if (self.current_category is None or tag.getCategory() == self.current_category.getCode()) and \
         tag in self.available_tags and search_term.lower() in tag.getName().lower():
        btn.show()
        tags_grid_is_empty = False
      else:
        btn.hide()
    # show available tags grid
    if tags_grid_is_empty:
      self.no_tags_available_label.show()
    else:
      self.no_tags_available_label.hide()
    # show/hide tags filter
    if len(self.available_tags) == 0:
      self.tag_name_filter.hide()
    else:
      self.tag_name_filter.show()

  def updateUsedTagsView(self):
    # clear the grid
    children = self.used_tags_view.get_children()
    for child in children:
      child.destroy()
    # add new tags
    for tag in self.used_tags:
      tag_button = Gtk.LinkButton()
      tag_name = self.limitNameLenght(tag.getName())
      tag_button.set_label(tag_name)
      tag_button.connect("activate-link", self.shandler.removeTagFromSearch, tag)
      self.used_tags_view.add(tag_button)
    self.used_tags_view.show_all()
  
  def updateFilesView(self):
    # set the new model
    #self.files_view.set_model(self.files_store)
    model = self.files_view.get_model()
    if model is None:
      #print('Set model')
      self.files_view.set_model(self.files_store)
    self.files_view.show_all()
    # show/hide the load more button
    if len(self.files) > self.files_results_limit:
      self.load_more_files_button.show()
    else:
      self.load_more_files_button.hide()
  
  ########################
  ## Pseudo-Tags search ##
  ########################
  def searchUntaggedFiles(self, widget=None, data=None):
    # restore the limit
    self.files_results_limit = RESULT_LIMIT
    # rewrite the used tags list
    self.used_tags.clear()
    pseudo_tag = PseudoTag("Untagged files")
    self.used_tags.append(pseudo_tag)
    # search files
    self.files = self.db.getFilesWithNoTags()
    self.updateFilesStore()
    # update interface
    # update the available tags
    self.available_tags.clear()
    self.updateAvailableCategories()
    # update the interface
    self.updateCategorySelector()
    self.updateUsedTagsView()
    self.updateFilesView()
  
  ##########################
  ## Tags/Files selection ##
  ##########################
  def changeCategory(self, *args):
    # Change the current category
    self.log.info("changeCategory == Start")
    index = self.category_selector.get_active()
    if index > 0:
      self.current_category = self.available_categories[index]
    else:
      self.current_category = None
    # Update the interface
    self.updateTagsGrid()
  
  def tagNameSearch(self, *args):
    self.updateTagsGrid()
  
  def addTagInSearch(self, widget, tag):
    # clear the search form
    search_entry = self.builder.get_object("TagSearch")
    search_entry.set_text('')
    # add the tag
    self.used_tags.append(tag)
    # search
    self.searchFiles()
    return False
  
  def removeTagFromSearch(self, widget, tag):
    # remove the taf
    self.used_tags.remove(tag)
    # search
    self.searchFiles()
    return True
  
  ############################
  ## Tag/Category selection ##
  ############################
  def updateAvailableTags(self):
    # update available tags
    self.available_tags.clear()
    if len(self.used_tags) == 0:
      for tag in self.tags:
        self.available_tags.append(tag)
    else:
      valid_tags = self.db.getCommonTags(self.files)
      valid_tags_codes = list(map(lambda t : int(t), valid_tags))
      for tag in self.tags:
        if tag.getCode() in valid_tags_codes and not tag in self.used_tags:
          self.available_tags.append(tag)
    
  def updateAvailableCategories(self):
    self.available_categories.clear()
    self.available_categories = [PseudoCategory('')]
    cat_codes = []
    for tag in self.available_tags:
      if not tag.getCategory() in cat_codes:
        cat_codes.append(tag.getCategory())
    for category in self.categories:
      if category.getCode() in cat_codes:
        self.available_categories.append(category)
  
  ######################
  ## Open file/folder ##
  ######################
  def openFile(self, widget, item):
    file_code = self.files_store[item][0]
    single_file = None
    for el_file in self.files:
      if el_file.getCode() == file_code and self.ts.fileExists(el_file):
        single_file = el_file
    if single_file is not None:
      # open file
      application = Popen(["xdg-open", self.ts.getFilePath(single_file)])
  
  def openFolder(self, widget, data):
    # get selected files
    path_list = self.files_view.get_selected_items()
    files = []
    for ipath in path_list:
    #ipath = path_list[0]
      file_code = self.files_store[ipath][0]
      #single_file = None
      for el_file in self.files:
        if el_file.getCode() == file_code and self.ts.fileExists(el_file):
          files.append(el_file)
    if len(files) > 0:
      single_file = files[0]
      if single_file is not None:
        # open folder
        application = Popen(["xdg-open", self.ts.getFileLocation(single_file)])
  
  #################
  ## Remove File ##
  #################
  def removeFile(self, widget, data):
    # get selected files
    path_list = self.files_view.get_selected_items()
    files = []
    for ipath in path_list:
    #ipath = path_list[0]
      file_code = self.files_store[ipath][0]
      #single_file = None
      for el_file in self.files:
        if el_file.getCode() == file_code:
          files.append(el_file)
    # ask for confirmation
    callback_success = self.removeFilesReal
    callback_failure = None
    callback_data = files
    self.createConfirmationDialog("Do you want to remove this file(s)?", callback_success, callback_failure, callback_data)
  
  def removeFilesReal(self, files):
    self.log.info("removeFilesReal == removing file(s) ")
    # remove files
    for single_file in files:
      self.log.info("removeFilesReal == removing file: " + single_file.getName())
      self.removeThumbnail(single_file)
      self.db.deleteFile(single_file, commit=False)
    self.db.commit()
    # update the main window
    self.reloadMainWindow()
    return True
  
  ##################
  ## Search Files ##
  ##################
  def searchFiles(self):
    # TODO: if I added a tag then search only among the self.files list
    # restore the limit
    self.files_results_limit = RESULT_LIMIT
    # name contains
    name_entry = self.builder.get_object('BrowserSearchName')
    name_contains = name_entry.get_text().strip()
    if name_contains == '':
      name_contains = None
    # search files
    self.files = self.db.getFilesWithTags(self.used_tags, self.use_magnitude, name_contains=name_contains)
    self.updateFilesStore()
    # update the available tags
    self.updateAvailableTags()
    self.updateAvailableCategories()
    # update the interface
    self.updateCategorySelector()
    self.updateUsedTagsView()
    self.updateFilesView()

  def loadMoreImages(self):
    self.files_results_limit += RESULT_LIMIT
    self.updateFilesStore()
    self.updateFilesView()
  
  #################################
  ## Icons/Thumbnails management ##
  #################################
  def getFilePixbuf(self, single_file):
    pixbuf = None
    theme = Gtk.IconTheme.get_default()
    if not self.ts.fileExists(single_file):
      # missing file image
      pixbuf = theme.load_icon(Gtk.STOCK_MISSING_IMAGE, ICON_SIZE, 0)
      pass
    elif single_file.getMime() in VIDEO_MIMES or single_file.getMime() in IMAGE_MIMES:
      thumb_file = self.getThumbFile(single_file)
      if not os.path.exists(thumb_file):
        self.createThumbnail(single_file, thumb_file)
      if os.path.exists(thumb_file):
        try:
          pixbuf = Pixbuf.new_from_file(thumb_file)
        except Exception:
          # todo: insert this thumb in fails
          pixbuf = None
          pass
    if pixbuf is None:
      # try to use the default icon if possible
      # use a generic one otherwise
      gtk_icon = self.getFileGtkIcon(single_file, theme)
      try:
        pixbuf = theme.load_icon(gtk_icon, ICON_SIZE, 0)
      except Exception:
        pixbuf = theme.load_icon(Gtk.STOCK_FILE, ICON_SIZE, 0)
    return pixbuf
  
  def createThumbnail(self, single_file, thumb_file):
    if not self.ts.fileExists(single_file):
      return False
    else:
      if single_file.mime in VIDEO_MIMES:
        self.createVideoThumbnail(single_file, thumb_file)
      elif single_file.mime in IMAGE_MIMES:
        self.createImageThumbnail(single_file, thumb_file)
      else:
        return False
  
  def createVideoThumbnail(self, single_file, thumb_file):
    args = ["ffmpegthumbnailer", "-i", self.ts.getFilePath(single_file), "-o", thumb_file, "-s", str(ICON_SIZE*2) ]
    video_thumbnail_process = Popen(args)
    self.require_files_view_deferred_update = True
  
  def createImageThumbnail(self, single_file, thumb_file):
    icon_format = str(ICON_SIZE*2) + "x" + str(ICON_SIZE*2)
    args = ["convert", self.ts.getFilePath(single_file) + "[0]", "-thumbnail", icon_format, thumb_file]
    image_thumbnail_process = Popen(args)
    self.require_files_view_deferred_update = True
  
  def removeThumbnail(self, single_file):
    thumb_file = self.getThumbFile(single_file)
    if os.path.exists(thumb_file):
      os.remove(thumb_file)
  
  def getThumbFile(self, single_file):
    return os.path.join(self.thumbnails_folder, str(single_file.getCode()) + THUMBNAILS_EXTENSION)
  
  def getFileGtkIcon(self, single_file, theme):  
    mime = single_file.getMime()
    if mime == "folder":
      return 'folder'
    else:
      # Mime icon
      gtk_icon = mime.replace('/','-')
      if theme.has_icon(gtk_icon):
        return gtk_icon
      # Gnome mime
      gtk_icon = 'gnome-mime-' + mime.replace('/','-')
      if theme.has_icon(gtk_icon):
        return gtk_icon
      # Generic mime
      tmp = mime.split('/')
      gmime = tmp[0]
      gtk_icon = gmime
      if theme.has_icon(gtk_icon):
        return gtk_icon
      # Generic gnome mime
      gtk_icon = 'gnome-mime-' + gmime
      if theme.has_icon(gtk_icon):
        return gtk_icon
      return Gtk.STOCK_FILE
  
  def triggerFilesViewUpdate(self, trigger):
    if trigger: 
      timeout_id = GObject.timeout_add(500, self.triggerFilesViewUpdate, False)
    else:
      self.updateFilesStore()
      self.updateFilesView()
  
  #####################
  ## Settings Window ##
  #####################
  def settingsShow(self, *args):
    # update label
    label = self.builder.get_object('SettingsRootLabel')
    label.set_text("Root: " + self.root)
    # update magnitude
    magnitude_check = self.builder.get_object('SettingsUseMagnitude')
    magnitude_check.set_active(self.use_magnitude)
    self.settings_window.show()
  
  def settingsClose(self):
    self.settings_window.hide()
    self.reloadConfig()
  
  def settingsChangeRoot(self, widget):
    dialog = Gtk.FileChooserDialog("Please choose a folder", self.settings_window, Gtk.FileChooserAction.SELECT_FOLDER, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Select", Gtk.ResponseType.OK))
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
      # update options file
      new_root = dialog.get_filename()
      new_root = os.path.abspath(new_root)
      self.ts.config["root"] = new_root
      self.ts.saveConfig()
      self.root = self.ts.config["root"]
      label = self.builder.get_object('SettingsRootLabel')
      label.set_text("Files root:" + new_root)
    dialog.destroy()
  
  def settingsChangeMagnitude(self, widget):
    value = widget.get_active()
    self.ts.config['use_magnitude'] = value
    self.ts.saveConfig()
    self.use_magnitude = self.ts.config['use_magnitude']
  
  def destroyWindow(self, widget, window):
    window.destroy()
  
  ########################
  ## Additional Windows ##
  ########################
  def showTagEditor(self, *args):
    self.ts.openTagEditor()
  
  def openSearchMissingWindow(self, widget=None, data=None):
    self.ts.openSearchMissing()
  
  def createTagFileWindow(self, widget, data):
    # get selected files
    path_list = self.files_view.get_selected_items()
    files = []
    for ipath in path_list:
    #ipath = path_list[0]
      file_code = self.files_store[ipath][0]
      #single_file = None
      for el_file in self.files:
        if el_file.getCode() == file_code and self.ts.fileExists(el_file):
          files.append(el_file)
    if len(files) > 0:
      self.ts.openBrowserTagFile(files)
  
  def createConfirmationDialog(self, question, callback_success, callback_failure, callback_data):
    # create dialog
    dialog = Gtk.Dialog("Confirm action", self.main_window, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))
    dialog.set_default_size(300, 100)
    label = Gtk.Label(question)
    box = dialog.get_content_area()
    box.add(label)
    # show and run
    dialog.show_all()
    response = dialog.run()
    # check response
    if response == Gtk.ResponseType.OK:
      if callback_success != None:
        callback_success(callback_data)
    else:
      if callback_failure != None:
        callback_failure(callback_data)
    # destory dialog
    dialog.destroy()
    return True
  
  ######################
  ## Files View Click ##
  ######################
  def clickOnFile(self, widget, event):
    if event.type == Gdk.EventType.BUTTON_PRESS:
      coords = event.get_coords()     
      ipath = widget.get_path_at_pos(coords[0], coords[1])
      if ipath != None:
        # Something clicked
        if not widget.path_is_selected(ipath):
          # deselect all the other paths
          widget.unselect_all()
          # select the element
          widget.select_path(ipath)
        # Select Action
        if event.button == 3: # Right click
          # open popup
          self.files_view_menu.popup(None, None, None, None, event.button, event.time)
        elif event.button == 1: # Left click
          self.openFile(widget, ipath)
      return True # event handled


def open(*args, **kwargs):
  b = Browser(*args, **kwargs)
  return b
