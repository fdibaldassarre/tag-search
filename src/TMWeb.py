#!/usr/bin/env python3

import os

from urllib import parse

from src import TMWebManager
from src.Common import json_dumps
from src.Common import getConfigFolder

OPERATION_GET_TAGS = 'get_tags'
OPERATION_GET_FILES = 'get_files'
OPERATION_GET_FILE_WITH_TAGS = 'get_file_tags'
OPERATION_ADD_TAG_TO_FILE = 'add_tag_to_file'
OPERATION_REMOVE_TAG_FROM_FILE = 'remove_tag_from_file'
OPERATION_TOGGLE_TAG_FOR_FILE = 'toggle_tag_for_file'

KEY_PROFILE = 'profile'
KEY_OPERATION = 'op'
KEY_TAGS = 'tags'
KEY_CODE = 'code'
KEY_CODE_TAG = 'code_tag'
KEY_NAME_CONTAINS = 'name_contains'
KEY_LIMIT = 'limit'

RESULT_OK = {"success": True}
RESULT_ERROR = {"success": False}
RESULT_ERROR_OPERATION = {"success": False, "error" : "Operation unknown"}
RESULT_ERROR_MISSING_ARGUMENTS = {"success": False, "error" : "Missing arguments"}

## Decorators
def returnJson(method):
  def new(self, *args, **kargs):
    res = method(self, *args, **kargs)
    return json_dumps(res)
  return new

def requireData(data_keys):
  def decorator(method):
    def new(self, *args, **kwargs):
      for key in data_keys:
        if not key in self.data:
          return RESULT_ERROR_MISSING_ARGUMENTS
      return method(self, *args, **kwargs)
    return new
  return decorator

## TMWeb class

class TMWeb():
  
  def __init__(self, profile):
    self.profile = profile
    self.data = []
    self.manager = None
  
  def startManager(self, profile):
    config_folder = getConfigFolder(profile)
    self.manager = TMWebManager.start(config_folder)
  
  def stopManager(self):
    self.manager.close()
    self.manager = None
  
  ## Utils ##
  def dataUnquote(self, string):
    return parse.unquote(string)
  
  def requestData(self, keys):
    for key in keys:
      if not key in self.data:
        return False
      elif self.data[key] == '':
        return False
    return True
  
  ## Run ##
  @returnJson
  def run(self, data):
    self.data = data
    operation = self.getOperation()
    profile = self.getProfile()
    if profile is None or operation is None:
      return RESULT_ERROR
    self.startManager(profile)
    result = self.executeOperation(operation)
    self.stopManager()
    return result
  
  def getOperation(self):
    if self.requestData([KEY_OPERATION]):
      return self.data[KEY_OPERATION]
    else:
      return None
  
  def getProfile(self):
    if self.requestData([KEY_PROFILE]):
      return self.data[KEY_PROFILE]
    else:
      return None
  
  def executeOperation(self, operation):
    if operation == OPERATION_GET_TAGS:
      return self.getTags()
    elif operation == OPERATION_GET_FILES:
      return self.getFiles()
    elif operation == OPERATION_GET_FILE_WITH_TAGS:
      return self.getFileWithTags()
    elif operation == OPERATION_ADD_TAG_TO_FILE:
      return self.addTagToFile()
    elif operation == OPERATION_REMOVE_TAG_FROM_FILE:
      return self.removeTagFromFile()
    elif operation == OPERATION_TOGGLE_TAG_FOR_FILE:
      return self.toggleTagForFile()
    else:
      return RESULT_ERROR_OPERATION
  
  ## Operations ##
  def getTags(self):
    return self.manager.getTags()
  
  @requireData([KEY_TAGS])
  def getFiles(self):
    tag_list = self.data[KEY_TAGS]
    if len(tag_list) == 0:
      tags = []
    else:
      tags = tag_list.split(',')
    name_contains = None
    if KEY_NAME_CONTAINS in self.data:
      name_contains = self.dataUnquote(self.data[KEY_NAME_CONTAINS])
    return self.manager.getFilesAndTagsWith(tags, name_contains)
  
  @requireData([KEY_CODE])
  def getFileWithTags(self):
    code = self.data[KEY_CODE]
    return self.manager.getFileWithTags(code)
  
  @requireData([KEY_CODE, KEY_CODE_TAG])
  def addTagToFile(self):
    fcode = self.data[KEY_CODE]
    tcode = self.data[KEY_CODE_TAG]
    self.manager.addTagToFile(tcode, fcode)
    return RESULT_OK
  
  @requireData([KEY_CODE, KEY_CODE_TAG])
  def removeTagFromFile(self):
    fcode = self.data[KEY_CODE]
    tcode = self.data[KEY_CODE_TAG]
    self.manager.removeTagFromFile(tcode, fcode)
    return RESULT_OK
  
  @requireData([KEY_CODE, KEY_CODE_TAG])
  def toggleTagForFile(self):
    fcode = self.data[KEY_CODE]
    tcode = self.data[KEY_CODE_TAG]
    self.manager.toggleTagForFile(tcode, fcode)
    return RESULT_OK
    
def start(config_folder):
  aw = TMWeb(config_folder)
  return aw
