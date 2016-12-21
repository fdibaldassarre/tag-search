#!/usr/bin/python3

import os
import sqlite3
from subprocess import Popen

from src.Common import Tag
from src.Common import Category
from src.Common import File

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

class Database():

  def __init__(self, db_path):
    self.db_path = db_path
    self._setupDBFolder()
    self._loadDatabase()
  
  def _setupDBFolder(self):
    db_folder = os.path.dirname(self.db_path)
    if not os.path.exists(db_folder):
      os.makedirs(db_folder)
  
  def commit(self):
    self._conn.commit()
    
  ## Database
  def _loadDatabase(self):
    if not os.path.exists(self.db_path):
      # create db file
      sql_filepath = os.path.join(SQL_FOLDER, "data.sql" )
      sql_file = open(sql_filepath, "r")
      process = Popen(["sqlite3", self.db_path], stdin=sql_file)
      process.communicate()
    # Load db
    self._conn = sqlite3.connect(self.db_path)
    self.db = self._conn.cursor()
    
  ## Get
  def getFilesWithTags(self, tags, use_magnitude=False, limit=None, name_contains=None):
    # parameters
    params = {}
    if name_contains is not None:
      params['name_contains'] = '%' + name_contains + '%'
    # base query
    query = 'SELECT F.Code, F.Location, F.Name, F.Mime FROM Files F'
    for tag in tags:
      query += ' INTERSECT SELECT F.Code, F.Location, F.Name, F.Mime FROM Files F, TagsFiles TF WHERE F.Code = TF.File AND TF.Tag = ' + str(int(tag))
    if name_contains is not None:
      query += ' INTERSECT SELECT F.Code, F.Location, F.Name, F.Mime FROM Files F WHERE LOWER(F.Name) LIKE :name_contains'
    query += ' ORDER BY F.Name'
    # limit
    if limit is not None:
      query += ' LIMIT ' + str(limit)
    if len(tags) > 0 and use_magnitude:
      # NOTE: I order the file using the sum of the magnitudes of the chosen tags
      # find the files
      self.db.execute(query, params)
      files_data = self.db.fetchall()
      related_files = self.getFilesFromDBData(files_data)
      codes_list = " ,".join(map(lambda t : str(int(t)), tags))
      files_codes_list = " ,".join(map(lambda f : str(int(f)), related_files))
      query = 'SELECT F.Code, F.Location, F.Name, F.Mime, SUM(TF.Magnitude) AS Magnitude FROM Files F, TagsFiles TF WHERE F.Code = TF.File AND TF.Tag IN ( ' + codes_list + ') AND F.Code IN ( ' + files_codes_list + ' ) GROUP BY F.Code ORDER BY Magnitude DESC'
    # execute query
    self.db.execute(query, params)
    # fetch result
    files_data = self.db.fetchall()
    # organize results
    result_data = self.getFilesFromDBData(files_data)
    return result_data
  
  def getFilesWithNoTags(self):
    query = 'SELECT Code, Location, Name, Mime FROM Files WHERE Code NOT IN (SELECT File FROM TagsFiles GROUP BY File)'
    self.db.execute(query)
    files_data = self.db.fetchall()
    all_files = self.getFilesFromDBData(files_data)
    return all_files
    
  def getAllTags(self):
    query = 'SELECT Code, Name, Category FROM Tags ORDER BY Name'
    self.db.execute(query)
    tags_data = self.db.fetchall()
    all_tags = self.getTagsFromDBData(tags_data)
    return all_tags
  
  def getTagFromCode(self, code):
    query = 'SELECT Code, Name, Category FROM Tags WHERE Code=?'
    self.db.execute(query, (code,))
    data = self.db.fetchone()
    if data is None:
      return None
    else:
      return self.getTagFromDBData(data)
  
  def getTagFromName(self, name):
    query = 'SELECT Code, Name, Category FROM Tags WHERE Name=?'
    self.db.execute(query, (name,))
    tag_data = self.db.fetchone()
    if tag_data is None:
      tag = None
    else:
      tag = self.getTagFromDBData(tag_data)
    return tag
  
  def getAllCategories(self):
    query = 'SELECT Code, Name, HasMagnitude FROM Categories ORDER BY Name'
    self.db.execute(query)
    categories_data = self.db.fetchall()
    all_category = self.getCategoriesFromDBData(categories_data)
    return all_category
  
  def getCategoryFromCode(self, code):
    query = 'SELECT Code, Name, HasMagnitude FROM Categories WHERE Code=?'
    self.db.execute(query, (code,))
    data = self.db.fetchone()
    if data is None:
      return None
    else:
      return self.getCategoryFromDBData(data)
  
  def getCategoryFromName(self, name):
    query = 'SELECT Code, Name, HasMagnitude FROM Categories WHERE Name=?'
    self.db.execute(query, (name,))
    category_data = self.db.fetchone()
    if category_data is None:
      category = None
    else:
      category = self.getCategoryFromDBData(category_data)
    return category
    
  def getAllFiles(self):
    query = 'SELECT Code, Location, Name, Mime FROM Files'
    self.db.execute(query)
    files_data = self.db.fetchall()
    all_files = self.getFilesFromDBData(files_data)
    return all_files
  
  def getAllTagsWithCategory(self, category):
    query = 'SELECT Code, Name, Category FROM Tags WHERE Category = ? ORDER BY Name'
    self.db.execute(query, (int(category), ))
    tags_data = self.db.fetchall()
    tags = self.getTagsFromDBData(tags_data)
    return tags
  
  def getTagsOfFile(self, single_file):
    query = 'SELECT T.Code, T.Name, T.Category, TF.Magnitude FROM TagsFiles TF, Tags T WHERE T.Code = TF.Tag AND TF.File = ? ORDER BY T.Name'
    self.db.execute(query, (int(single_file), ))
    all_data = self.db.fetchall()
    tags = self.getTagsFromDBData(all_data)
    result = {}
    for i in range(len(all_data)):
      tag = tags[i]
      magnitude = all_data[i][3]
      result[tag.getCode()] = magnitude
    return result
  
  def getCommonTags(self, files):
    if len(files) == 0:
      return []
    if len(files) > 1:
      files_codes = " ,".join(map(lambda f : str(int(f)), files))
      query = 'SELECT T.Code, T.Name, T.Category FROM TagsFiles TF, Tags T WHERE T.Code = TF.Tag AND TF.File IN (' + files_codes + ') ORDER BY T.Name'
    else:
      f = files[0]
      query = 'SELECT T.Code, T.Name, T.Category FROM TagsFiles TF, Tags T WHERE T.Code = TF.Tag AND TF.File = ' + str(int(f)) + ' ORDER BY T.Name'
    self.db.execute(query)
    tags_data = self.db.fetchall()
    tags = self.getTagsFromDBData(tags_data)
    return tags
  
  ## ADD/DELETE
  @databaseCommit
  def addTag(self, tag):
    query = 'INSERT INTO Tags(Name, Category) VALUES (?, ?)'
    try:
      self.db.execute(query, (tag.getName(), tag.getCategory()))
    except sqlite3.IntegrityError:
      return None
    code = self.db.lastrowid
    tag.setCode(code)
    return code
  
  @databaseCommit
  def deleteTag(self, tag):
    query = 'DELETE FROM Tags WHERE Code = ?'
    self.db.execute(query, (int(tag), ))
    query = 'DELETE FROM TagsFiles WHERE Tag = ?'
    self.db.execute(query, (int(tag), ))
  
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
  
  @databaseCommit
  def deleteFile(self, del_file):
    query = 'DELETE FROM Files WHERE Code = ?'
    self.db.execute(query, (del_file.getCode(), ))
    query = 'DELETE FROM TagsFiles WHERE File = ?'
    self.db.execute(query, (del_file.getCode(), ))
  
  @databaseCommit
  def addCategory(self, category):
    has_magnitude = 1 if category.hasMagnitude() else 0
    query = 'INSERT INTO Categories(Name, HasMagnitude) VALUES (?, ?)'
    try:
      self.db.execute(query, (category.getName(), has_magnitude))
    except sqlite3.IntegrityError:
      return None
    code = self.db.lastrowid
    category.setCode(code)
    return code
  
  @databaseCommit
  def deleteCategory(self, category):
    # delete only if there are no associated tags
    query = 'SELECT Code FROM Tags WHERE Category = ?'
    self.db.execute(query, (int(category), ))
    result = self.db.fetchall()
    if len(result) == 0:
      # delete this category
      query = 'DELETE FROM Categories WHERE Code = ?'
      self.db.execute(query, (int(category), ))
      return True
    else:
      return False
  
  ## TAG EDIT
  @databaseCommit
  def renameTag(self, tag, new_name):
    query = 'UPDATE Tags SET Name = ? WHERE Code = ?'
    try:
      self.db.execute(query, (new_name, int(tag)))
    except sqlite3.IntegrityError:
      return None
    return True
    
  @databaseCommit
  def changeTagCategory(self, tag, new_category):
    query = 'UPDATE Tags SET Category = ? WHERE Code = ?'
    self.db.execute(query, (int(new_category), int(tag)))
  
  @databaseCommit
  def renameCategory(self, category, new_name):
    query = 'UPDATE Categories SET Name = ? WHERE Code = ?'
    try:
      self.db.execute(query, (new_name, int(new_category)))
    except sqlite3.IntegrityError:
      return None
    return True
 
  ## TAG FILE
  @databaseCommit
  def addTagToFile(self, tag, single_file, magnitude=1):
    query = 'INSERT INTO TagsFiles(Tag, File, Magnitude) VALUES (?, ?, ?)'
    self.db.execute(query, (int(tag), int(single_file), magnitude))
  
  @databaseCommit
  def removeTagFromFile(self, tag, single_file):
    query = 'DELETE FROM TagsFiles WHERE Tag = ? AND File = ?'
    self.db.execute(query, (int(tag), int(single_file)))
  
  @databaseCommit
  def changeTagMagnitudeForFile(self, tag, single_file, new_magnitude):
    query = 'UPDATE TagsFiles SET Magnitude = ? WHERE Tag = ? AND File = ?'
    self.db.execute(query, (new_magnitude, int(tag), int(single_file)))
  
  @databaseCommit
  def changeFilePath(self, single_file, location, name):
    query = 'UPDATE Files SET Location = ?, Name = ? WHERE Code = ?'
    self.db.execute(query, (location, name, int(single_file)))
  
  def changeFileMime(self, single_file, mime):
    query = 'UPDATE Files SET Mime = ? WHERE Code = ?'
    self.db.execute(query, (mime, int(single_file)))
    
  ## Search file
  def getFileByRelativePath(self, path):
    location = os.path.dirname(path)
    name = os.path.basename(path)
    query = 'SELECT Code, Location, Name, Mime FROM Files WHERE Location = ? AND Name = ?'
    self.db.execute(query, (location, name))
    data = self.db.fetchone()
    if data is None:
      return None
    else:
      return self.getFileFromDBData(data)
  
  def getFilesByName(self, name):
    query = 'SELECT Code, Location, Name, Mime FROM Files WHERE Name = ?'
    self.db.execute(query, (name,))
    files_data = self.db.fetchall()
    result = self.getFilesFromDBData(files_data)
    return result
  
  ## DB Item creation
  def getFilesFromDBData(self, files_data):
    files = []
    for file_data in files_data:
      new_file = self.getFileFromDBData(file_data)
      files.append(new_file)
    return files
  
  def getFileFromDBData(self, file_data):
    code = file_data[0]
    location = file_data[1]
    name = file_data[2]
    mime = file_data[3]
    return File(code, name, location, mime)
  
  def getTagsFromDBData(self, tags_data):
    tags = []
    for tag_data in tags_data:
      new_tag = self.getTagFromDBData(tag_data)
      tags.append(new_tag)
    return tags
  
  def getTagFromDBData(self, tag_data):
    code = tag_data[0]
    name = tag_data[1]
    category = tag_data[2]
    return Tag(code, name, category)
  
  def getCategoriesFromDBData(self, categories_data):
    categorys = []
    for category_data in categories_data:
      new_category = self.getCategoryFromDBData(category_data)
      categorys.append(new_category)
    return categorys
  
  def getCategoryFromDBData(self, category_data):
    code = category_data[0]
    name = category_data[1]
    has_magnitude = category_data[2]
    return Category(code, name, has_magnitude)

def start(db_path):
  db = Database(db_path)
  return db
