#!/usr/bin/env python3

import os
import json

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

#############
## MetaTag ##
#############

class MetaTag(DBItem):
  
  def __init__(self, code, name, has_magnitude):
    super().__init__(code, name)
    self.has_magnitude = has_magnitude
  
  def hasMagnitude(self):
    return self.has_magnitude
  
  def giveMagnitude(self, magn=True):
    self.has_magnitude = magn

def createMetaTag(name, has_magnitude):
  meta = MetaTag(-1, name, has_magnitude)
  return meta


#########
## Tag ##
#########

class Tag(DBItem):
  
  def __init__(self, code, name, meta):
    super().__init__(code, name)
    self.meta = meta
  
  def getMetaCode(self):
    return self.meta
  
  def setMetaCode(self, code):  
    self.meta = code

def createTag(name, meta_code):
  tag = Tag(-1, name, meta_code)
  return tag


##########
## File ##
##########

class File(DBItem):
  
  def __init__(self, code, location, name, mime):
    super().__init__(code, name)
    self.location = location
    self.mime = mime
  
  def getMime(self):
    return self.mime
  
  def getLocation(self):
    return self.location
  
  def getFilepath(self):
    return os.path.abspath(os.path.join(self.location, self.name))
  
  def exists(self):
    return os.path.exists(self.getFilepath())

def loadFile(filepath):
  filepath = os.path.abspath(filepath)
  if not os.path.exists(filepath):
    return None
  code = -1
  name = os.path.basename(filepath)
  location = os.path.dirname(filepath)
  if os.path.isdir(filepath):
    mime = 'folder'
  else:
    mime = guessMime(filepath)
  new_file = File(code, location, name, mime)
  return new_file


##################
## Configurable ##
##################

class Configurable():
  
  def __init__(self, config_folder):
    self.config_folder = os.path.abspath(config_folder)
    self.setupConfigFolder()
    self.config_file = os.path.join(self.config_folder, 'main.json')
    self.config = self.loadConfig(self.config_file)
  
  def getProfileName(self):
    return os.path.basename(os.path.dirname(self.config_file))
  
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
    encoder = json.JSONEncoder()
    data = encoder.encode(config)
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
    # Decode
    return decoder.decode(tmp)
  
  def loadDefaultConfig(self):
    config = {}
    return config


