#!/usr/bin/env python3

import os

##########
## Json ##
##########

try:
  import simplejson as json
  from simplejson import loads as json_loads
  from simplejson import dumps as json_dumps
except ImportError:
  import json
  from json import loads as json_loads
  from json import dumps as json_dumps
  
import json

###############
## guessMime ##
###############

from src.Utils.Magic import guessMime

############
## DBItem ##
############

class DBItem():
  
  def __init__(self, code, name): 
    self.code = code
    self.name = name
  
  def getCode(self):
    return self.code
  
  def getName(self):
    return self.name
  
  def setCode(self, code):
    self.code = code
  
  def setName(self, name):  
    self.name = name
  
  def toArray(self):
    return {'code':  self.getCode(), 'name' : self.getName()}
  
  def __int__(self):
    return int(self.code)
  
##############
## Category ##
##############

class Category(DBItem):
  
  def __init__(self, code, name, has_magnitude):
    super().__init__(code, name)
    self.has_magnitude = has_magnitude
  
  def hasMagnitude(self):
    return self.has_magnitude
  
  def setMagnitude(self, magnitude=True):
    self.has_magnitude = magnitude
  
  def toArray(self):
    res = super().toArray()
    res['has_magnitude'] = self.hasMagnitude()
    return res
  
def createCategory(name, has_magnitude):
  category = Category(-1, name, has_magnitude)
  return category


#########
## Tag ##
#########

class Tag(DBItem):
  
  def __init__(self, code, name, category):
    super().__init__(code, name)
    self.category = category
  
  def getCategory(self):
    return self.category
  
  def setCategoryCode(self, code):  
    self.category = code
  
  def toArray(self):
    res = super().toArray()
    res['category'] = self.getCategory()
    return res
  
def createTag(name, category_code):
  tag = Tag(-1, name, category_code)
  return tag


##########
## File ##
##########

class File(DBItem):
  
  def __init__(self, code, name, location, mime):
    super().__init__(code, name)
    self.location = location
    self.path = os.path.join(self.location, self.name)
    self.mime = mime
  
  def getLocation(self):
    return self.location
  
  def getPath(self):
    return self.path
  
  def getMime(self):
    return self.mime
  
  def toArray(self):
    res = super().toArray()
    res['location'] = self.getLocation()
    res['mime'] = self.getMime()
    return res
  
def loadFile(filepath, root):
  filepath = os.path.abspath(filepath)
  if not filepath.startswith(root):
    # Out of tree file
    return None
  if not os.path.exists(filepath):
    return None
  code = -1
  mime = guessMime(filepath)
  relpath = os.path.relpath(filepath, root)
  location = os.path.dirname(relpath)
  name = os.path.basename(relpath)
  new_file = File(code, name, location, mime)
  return new_file

##################
## Configurable ##
##################

class Configurable():
  
  def __init__(self, config_folder):
    self.config_folder = config_folder
    self.setupConfigFolder()
    self.config_file = os.path.join(self.config_folder, 'main.json')
    self.config = self.loadConfig(self.config_file)
    if not os.path.exists(self.config_file):
      self.saveConfig()
  
  def setupConfigFolder(self):
    if not os.path.exists(self.config_folder):
      os.makedirs(self.config_folder)
  
  def loadConfig(self, path, load_default=True):
    # Initialize
    if load_default:
      config = self.loadDefaultConfig()
    else:
      config = {}
    # Read config file
    if os.path.exists(path):
      new_config = self.parseJson(path)
      # Add default values
      config = self.overwriteConfig(config, new_config)
    return config
  
  def overwriteConfig(self, config, new_config):
    for key in new_config:
      config[key] = new_config[key]
    return config
  
  def saveConfig(self, config=None, path=None):
    if config is None:
      config = self.config
    if path is None:
      path = self.config_file
    # save
    data = json_dumps(config)
    hand = open(path, 'w')
    hand.write(data)
    hand.close()
  
  def parseJson(self, path):
    # Json decoder
    decoder = json.JSONDecoder()
    # Read the json file
    hand = open(path, 'r')
    tmp = []
    for line in hand:
      line = line.strip()
      tmp.append(line)
    hand.close()
    tmp = ''.join(tmp)
    return json_loads(tmp)
  
  def loadDefaultConfig(self):
    config = {}
    return config


def getConfigFolder(profile_name):
  return os.path.join(os.environ['HOME'], ".config/tag-search/" + profile_name)
