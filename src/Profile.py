#!/usr/bin/python3

import os

from src.Common import loadFile
from src.Common import Configurable
from src.Database import Database

################
## TSProfile ###
################

class Profile(Configurable):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    db_path = os.path.join(self.config_folder, 'tf.db')
    self.db = Database(db_path)
  
  def loadDefaultConfig(self):
    config = {}
    config['root'] = os.path.join(os.environ['HOME'], 'TagSearch/')
    config['use_magnitude'] = False
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
  
  def changeFilePath(tfile, path):
    pass
    # TODO

def start(*args, **kwargs):
  profile = Profile(*args, **kwargs)
  return profile
