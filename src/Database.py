#!/usr/bin/python3

import os
import sys
import sqlite3
from subprocess import Popen

from src.Common import Configurable
from src.Common import Tag
from src.Common import MetaTag
from src.Common import File
from src.Common import loadFile

from src.Constants import MAIN_FOLDER
from src.Constants import SQL_FOLDER

#################
## TSDatabase ###
#################

def databaseCommit(method):
  def new(self, *args, **kwargs):
    commit = True
    if 'commit' in kwargs:
      commit = kwargs['commit']
      del kwargs['commit']
    res = method(self, *args, **kwargs)
    if commit:
      self.commit()
    return res
  return new

SEARCH_PATH = 1
SEARCH_NAME = 2

class Database(Configurable):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.db_folder = os.path.join(self.config_folder, "db/")
    self._setupDBFolder()
    self._loadDatabase()
  
  def _setupDBFolder(self):
    if not os.path.exists(self.db_folder):
      os.mkdir(self.db_folder)
  
  def commit(self):
    self._conn.commit()
    
  ## LOAD DATABASE
  def _loadDatabase(self):
    db_file = os.path.join(self.db_folder, "data.db" )
    if not os.path.exists(db_file):
      # create db file
      sql_filepath = os.path.join(SQL_FOLDER, "data.sql" )
      sql_file = open(sql_filepath, "r")
      process = Popen(["sqlite3", db_file], stdin=sql_file)
      process.communicate()
    # Load db
    self._conn = sqlite3.connect(db_file)
    self.db = self._conn.cursor()
    
  ## GET
  def getFilesWithTags(self, tags, use_magnitude=False, limit=None, name_contains=None):
    codes = self.getTagsCodes(tags)
    # parameters
    params = {}
    if name_contains is not None:
      params['name_contains'] = '%' + name_contains + '%'
    # base query
    query = 'SELECT F.Code, F.Location, F.Name, F.Mime FROM Files F'
    for code in codes:
      query += ' INTERSECT SELECT F.Code, F.Location, F.Name, F.Mime FROM Files F, TagsFiles TF WHERE F.Code = TF.File AND TF.Tag = ' + str(code)
    if name_contains is not None:
      query += ' INTERSECT SELECT F.Code, F.Location, F.Name, F.Mime FROM Files F WHERE LOWER(F.Name) LIKE :name_contains'
    query += ' ORDER BY F.Name'
    # limit
    if limit is not None:
      query += ' LIMIT ' + str(limit)
    if len(codes) > 0 and use_magnitude:
      # NOTE: I order the file using the sum of the magnitudes of the chosen tags
      # find the files
      self.db.execute(query, params)
      files_data = self.db.fetchall()
      related_files = self.getFilesFromDBData(files_data)
      files_codes = self.getFilesCodes(related_files)
      codes_list = " ,".join( map(str, codes) )
      files_codes_list = " ,".join( map(str, files_codes) )
      query = 'SELECT F.Code, F.Location, F.Name, F.Mime, SUM(TF.Magnitude) AS Magnitude FROM Files F, TagsFiles TF WHERE F.Code = TF.File AND TF.Tag IN ( ' + codes_list + ') AND F.Code IN ( ' + files_codes_list + ' ) GROUP BY F.Code ORDER BY Magnitude DESC'
    # execute query
    self.db.execute(query, params)
    # fetch result
    files_data = self.db.fetchall()
    # organize results
    result_data = self.getFilesFromDBData(files_data)
    return result_data
  
  def getFilesWithNoTag(self):
    query = 'SELECT Code, Location, Name, Mime FROM Files WHERE Code NOT IN (SELECT File FROM TagsFiles GROUP BY File)'
    self.db.execute(query)
    files_data = self.db.fetchall()
    all_files = self.getFilesFromDBData(files_data)
    return all_files
    
  def getAllTags(self):
    query = 'SELECT Code, Name, Meta FROM Tags ORDER BY Name'
    self.db.execute(query)
    tags_data = self.db.fetchall()
    all_tags = self.getTagsFromDBData(tags_data)
    return all_tags
  
  def getTagFromCode(self, code):
    query = 'SELECT Code, Name, Meta FROM Tags WHERE Code=?'
    self.db.execute(query, (code,))
    data = self.db.fetchone()
    if data is None:
      return None
    else:
      return self.getTagFromDBData(data)
  
  def getTagFromName(self, name):
    query = 'SELECT Code, Name, Meta FROM Tags WHERE Name=?'
    self.db.execute(query, (name,))
    tag_data = self.db.fetchone()
    if tag_data is None:
      tag = None
    else:
      tag = self.getTagFromDBData(tag_data)
    return tag
  
  def getAllMetaTags(self):
    query = 'SELECT Code, Name, HasMagnitude FROM MetaTags ORDER BY Name'
    self.db.execute(query)
    metatags_data = self.db.fetchall()
    all_meta = self.getMetaTagsFromDBData(metatags_data)
    return all_meta
  
  def getMetaTagFromCode(self, code):
    query = 'SELECT Code, Name, HasMagnitude FROM MetaTags WHERE Code=?'
    self.db.execute(query, (code,))
    data = self.db.fetchone()
    if data is None:
      return None
    else:
      return self.getMetaTagFromDBData(data)
  
  def getMetaTagFromName(self, name):
    query = 'SELECT Code, Name, HasMagnitude FROM MetaTags WHERE Name=?'
    self.db.execute(query, (name,))
    metatag_data = self.db.fetchone()
    if metatag_data is None:
      meta = None
    else:
      meta = self.getMetaTagFromDBData(metatag_data)
    return meta
    
  def getAllFiles(self):
    query = 'SELECT Code, Location, Name, Mime FROM Files'
    self.db.execute(query)
    files_data = self.db.fetchall()
    all_files = self.getFilesFromDBData(files_data)
    return all_files
  
  def getAllTagsWithMeta(self, meta_tag):
    query = 'SELECT Code, Name, Meta FROM Tags WHERE Meta = ? ORDER BY Name'
    self.db.execute(query, ( meta_tag.getCode(), ))
    tags_data = self.db.fetchall()
    tags = self.getTagsFromDBData(tags_data)
    return tags
  
  def getTagsOfFile(self, single_file):
    query = 'SELECT T.Code, T.Name, T.Meta, TF.Magnitude FROM TagsFiles TF, Tags T WHERE T.Code = TF.Tag AND TF.File = ? ORDER BY T.Name'
    self.db.execute(query, (single_file.getCode(), ))
    all_data = self.db.fetchall()
    tags = self.getTagsFromDBData(all_data)
    result = {}
    for i in range(len(all_data)):
      tag = tags[i]
      magnitude = all_data[i][3]
      result[tag.getCode()] = magnitude
    return result
  
  def getCommonTags(self, files):
    codes = self.getFilesCodes(files)
    if len(codes) == 0:
      return []
    if len(codes) > 1:
      files_codes = " ,".join(map(str, codes))
      query = 'SELECT T.Code, T.Name, T.Meta FROM TagsFiles TF, Tags T WHERE T.Code = TF.Tag AND TF.File IN (' + files_codes + ') ORDER BY T.Name'
    else:
      code = codes[0]
      query = 'SELECT T.Code, T.Name, T.Meta FROM TagsFiles TF, Tags T WHERE T.Code = TF.Tag AND TF.File = ' + str(code) + ' ORDER BY T.Name'
    self.db.execute(query)
    tags_data = self.db.fetchall()
    tags = self.getTagsFromDBData(tags_data)
    return tags
  
  ## ADD/DELETE
  @databaseCommit
  def addTag(self, tag):
    query = 'INSERT INTO Tags(Name, Meta) VALUES (?, ?)'
    try:
      self.db.execute(query, (tag.getName(), tag.getMetaCode()))
    except sqlite3.IntegrityError:
      return None
    code = self.db.lastrowid
    tag.setCode(code)
    return code
  
  @databaseCommit
  def deleteTag(self, tag):
    query = 'DELETE FROM Tags WHERE Code = ?'
    self.db.execute(query, (tag.getCode(), ))
    query = 'DELETE FROM TagsFiles WHERE Tag = ?'
    self.db.execute(query, (tag.getCode(), ))
  
  @databaseCommit
  def addFile(self, nfile):
    query = 'INSERT INTO Files(Location, Name, Mime) VALUES (?, ?, ?)'
    file_data = (nfile.getLocation(), nfile.getName(), nfile.getMime())
    try:
      self.db.execute(query, file_data)
    except sqlite3.IntegrityError:
      return None
    code = self.db.lastrowid
    nfile.setCode(code)
    return code
  
  @databaseCommit
  def addFiles(self, files):
    codes = []
    for single_file in files:
      code = self.addFile(single_file, commit=False)
      codes.append(code)
    return codes
    '''
    add_data = []
    for single_file in files:
      file_data = (single_file.getLocation(), single_file.getName(), single_file.getMime())
      add_data.append(file_data)
    query = 'INSERT INTO Files(Location, Name, Mime) VALUES (?, ?, ?)'
    self.db.executemany(query, add_data)
    '''
  
  @databaseCommit
  def deleteFile(self, del_file):
    query = 'DELETE FROM Files WHERE Code = ?'
    self.db.execute(query, (del_file.getCode(), ))
    query = 'DELETE FROM TagsFiles WHERE File = ?'
    self.db.execute(query, (del_file.getCode(), ))
  
  @databaseCommit
  def addMetaTag(self, metatag):
    has_magnitude = 1 if metatag.hasMagnitude() else 0
    query = 'INSERT INTO MetaTags(Name, HasMagnitude) VALUES (?, ?)'
    try:
      self.db.execute(query, (metatag.getName(), has_magnitude))
    except sqlite3.IntegrityError:
      return None
    code = self.db.lastrowid
    metatag.setCode(code)
    return code
  
  @databaseCommit
  def deleteMetaTag(self, metatag):
    # delete only if there are no associated tags
    query = 'SELECT Code FROM Tags WHERE Meta = ?'
    self.db.execute(query, (metatag.getCode(), ))
    result = self.db.fetchall()
    if len(result) == 0:
      # delete this meta
      query = 'DELETE FROM MetaTags WHERE Code = ?'
      self.db.execute(query, (metatag.getCode(), ))
      return True
    else:
      return False
  
  ## TAG EDIT
  @databaseCommit
  def renameTag(self, tag, new_name):
    query = 'UPDATE Tags SET Name = ? WHERE Code = ?'
    try:
      self.db.execute(query, (new_name, tag.getCode()))
    except sqlite3.IntegrityError:
      return None
    return True
    
  @databaseCommit
  def changeTagMeta(self, tag, new_meta):
    query = 'UPDATE Tags SET Meta = ? WHERE Code = ?'
    self.db.execute(query, (new_meta.getCode(), tag.getCode()))
  
  @databaseCommit
  def renameMetaTag(self, meta_tag, new_name):
    query = 'UPDATE MetaTags SET Name = ? WHERE Code = ?'
    try:
      self.db.execute(query, (new_name, meta_tag.getCode()))
    except sqlite3.IntegrityError:
      return None
    return True
 
  ## TAG FILE
  @databaseCommit
  def addTagToFile(self, tag, single_file, magnitude=1):
    query = 'INSERT INTO TagsFiles(Tag, File, Magnitude) VALUES (?, ?, ?)'
    self.db.execute(query, (tag.getCode(), single_file.getCode(), magnitude))
  
  @databaseCommit
  def removeTagFromFile(self, tag, single_file):
    query = 'DELETE FROM TagsFiles WHERE Tag = ? AND File = ?'
    self.db.execute(query, (tag.getCode(), single_file.getCode()))
  
  @databaseCommit
  def changeTagMagnitudeForFile(self, tag, single_file, new_magnitude):
    query = 'UPDATE TagsFiles SET Magnitude = ? WHERE Tag = ? AND File = ?'
    self.db.execute(query, (new_magnitude, tag.getCode(), single_file.getCode()))
  
  @databaseCommit
  def changeFilePath(self, single_file, new_filepath):
    # check if empty
    if len(new_filepath) == 0:
      return False
    new_file = loadFile(new_filepath)
    # update database
    query = 'UPDATE Files SET Location = ?, Name = ?, Mime = ? WHERE Code = ?'
    location = new_file.getLocation()
    name = new_file.getName()
    mime = new_file.getMime()
    self.db.execute(query, (location, name, mime, single_file.getCode()))
  
  ## Search file
  def searchFileByFilepath(self, filepath):
    location = os.path.dirname(filepath)
    name = os.path.basename(filepath)
    single_file = File(-1, location, name, None)
    return self.searchFile(single_file, SEARCH_PATH)
  
  def searchFile(self, single_file, mode=SEARCH_PATH):  
    # I have no code
    if mode == SEARCH_PATH:
      query = 'SELECT Code, Location, Name, Mime FROM Files WHERE Location = ? AND Name = ?'
      self.db.execute(query, (single_file.getLocation(), single_file.getName()))
    elif mode == SEARCH_NAME:
      query = 'SELECT Code, Location, Name, Mime FROM Files WHERE Name = ?'
      self.db.execute(query, (single_file.getName(), ))
    else:
      return []
    # fetch result
    files_data = self.db.fetchall()
    # organize results
    result_data = self.getFilesFromDBData(files_data)
    return result_data
  
  ## File/Tag/MetaTag DATA EXTRACTION
  def getTagsNames(self, tags):
    names = []
    for tag in tags:
      names.append(tag.getName())
    return names
  
  def getTagsCodes(self, tags):
    codes = []
    for tag in tags:
      codes.append(tag.getCode())
    return codes

  def getFilesCodes(self, files):
    codes = []
    for single_file in files:
      codes.append(single_file.getCode())
    return codes
  
  ## File/Tag/MetaTag CREATION
  def getFilesFromDBData(self, files_data):
    files = []
    for file_data in files_data:
      code = file_data[0]
      path = file_data[1]
      name = file_data[2]
      mime = file_data[3]
      new_file = File(code, path, name, mime)
      files.append(new_file)
    return files
  
  def getTagsFromDBData(self, tags_data):
    tags = []
    for tag_data in tags_data:
      new_tag = self.getTagFromDBData(tag_data)
      tags.append(new_tag)
    return tags
  
  def getTagFromDBData(self, tag_data):
    code = tag_data[0]
    name = tag_data[1]
    meta = tag_data[2]
    return Tag(code, name, meta)
  
  def getMetaTagsFromDBData(self, metatags_data):
    meta_tags = []
    for metatag_data in metatags_data:
      new_meta = self.getMetaTagFromDBData(metatag_data)
      meta_tags.append(new_meta)
    return meta_tags
  
  def getMetaTagFromDBData(self, metatag_data):
    code = metatag_data[0]
    name = metatag_data[1]
    has_magnitude = metatag_data[2]
    return MetaTag(code, name, has_magnitude)

def start(*args, **kwargs):
  db = Database(*args, **kwargs)
  return db
