#!/usr/bin/python3

import os

from src.Common import loadFile
from src.Common import Configurable
from src import Database
from src import ThumbManager

################
## TSProfile ###
################

class Profile(Configurable):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    db_path = os.path.join(self.config_folder, 'tf.db')
    self.db = Database.start(db_path)
    self.thumb_manager = ThumbManager.start(self)
  
  def loadDefaultConfig(self):
    config = {}
    config['root'] = os.path.join(os.environ['HOME'], 'TagSearch/')
    config['use_magnitude'] = False
    config['show_folder_preview'] = False
    config['thumb_filetype'] = 'png'
    return config
  
  def close(self):
    self.db.close()
  
  def getProfileName(self):
    return os.path.basename(self.config_folder)
  
  def getDatabase(self):
    return self.db
  
  def loadFile(self, path):
    return loadFile(path, self.config['root'])
  
  def getFilePath(self, tfile):
    return self.getCompletePath(tfile.getPath())
  
  def getFileLocation(self, tfile):
    return self.getCompletePath(tfile.getLocation())
  
  def getCompletePath(self, relpath):
    return os.path.join(self.config['root'], relpath)
  
  def getFileByPath(self, path):
    relpath = os.path.relpath(path, self.config['root'])
    return self.db.getFileByRelativePath(relpath)
  
  def fileExists(self, tfile):
    return os.path.exists(self.getFilePath(tfile))
  
  def changeFilePath(self, tfile, path):
    path = os.path.abspath(path)
    if not path.startswith(self.config['root']):
      # Out of tree file
      return None
    relpath = os.path.relpath(path, self.config['root'])
    location = os.path.dirname(relpath)
    name = os.path.basename(relpath)
    self.db.changeFilePath(tfile, location, name)

def start(*args, **kwargs):
  profile = Profile(*args, **kwargs)
  return profile
