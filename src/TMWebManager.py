#!/usr/bin/env python3

import os

from src.Profile import Profile

class TMWebManager(Profile):
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # Setup web folder
    self.web_folder = 'archive/' + self.getProfileName()
    self.web_thumbs_folder = 'thumbs/' + self.getProfileName()
  
  def getFileHref(self, tfile):
    return os.path.join(self.web_folder, tfile.getPath())
  
  def getFileThumb(self, tfile):
    return os.path.join(self.web_thumbs_folder, str(tfile.getCode()) + '.' + self.config['thumb_filetype'])
    
  def convertFileToDict(self, tfile):
    res = tfile.toArray()
    res['href'] = self.getFileHref(tfile)
    res['thumb'] = self.getFileThumb(tfile)
    return res
  
  def getTags(self):
    # Categories
    categories = self.db.getAllCategories()
    cat_list = []
    for cat in categories:
      cat_list.append(cat.toArray())
    # Tags
    tags = self.db.getAllTags()
    tag_list = []
    for tag in tags:
      tag_list.append(tag.toArray())
    # Result
    result = {'tags' : tag_list, 'categories' : cat_list}
    return result
  
  def getFilesAndTagsWith(self, tags_codes, name_contains=None):
    # Files
    files = self.db.getFilesWithTags(tags_codes, name_contains=name_contains)
    file_list = list( map(self.convertFileToDict, files) )
    # Tags
    tag_list = []
    tags = self.db.getCommonTags(files)
    tag_list = list( map(lambda t : t.toArray(), tags) )
    # Result
    result = {'tags' : tag_list, 'files' : file_list}
    return result
  
  def getFileWithTags(self, fcode):
    tfile = self.db.getFileByCode(fcode)
    if tfile is None:
      return None
    magn, tags = self.db.getTagsOfFile(tfile)
    result = {}
    result['file'] = self.convertFileToDict(tfile)
    result['tags'] = list(map(lambda t : t.toArray(), tags))
    result['tags_magnitude'] = magn
    return result
  
  def addTagToFile(self, tcode, fcode):
    self.db.addTagToFile(tcode, fcode)
    return True
  
  def removeTagFromFile(self, tcode, fcode):
    self.db.removeTagFromFile(tcode, fcode) 
    return True
  
  def toggleTagForFile(self, tcode, fcode):
    manitude, tags = self.db.getTagsOfFile(fcode)
    tags_codes = list( map(int, tags) )
    if int(tcode) in tags_codes:
      return self.removeTagFromFile(tcode, fcode)
    else:
      return self.addTagToFile(tcode, fcode)
  
# Start the main class
def start(config_folder):
  wm = TMWebManager(config_folder)
  return wm
