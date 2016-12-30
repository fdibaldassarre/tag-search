#!/usr/bin/env python3

import os
from subprocess import Popen

try:
  from natsort import natsorted
except ImportError:
  def natsorted(data):
    it = list(data)
    it.sort()
    return it

from src.Utils.Magic import guessMime

# Create/view file preview

VIDEO_MIMES = ["video/x-msvideo", "video/x-matroska", "video/mp4", "video/x-ogm+ogg", "video/x-ms-wmv"]
IMAGE_MIMES = ["image/gif", "image/png", "image/jpeg", "application/pdf", "image/vnd.djvu"]

THUMB_VIDEO = 0
THUMB_IMAGE = 1
THUMB_FOLDER = 2

RESULT_WORKING = 0

class ThumbManager():

  def __init__(self, profile):
    self.profile = profile
    self.thumbnails_folder = os.path.join(self.profile.getConfigFolder(), "thumbnails/")
    self.thumbnails_fail_folder = os.path.join(self.profile.getConfigFolder(), "thumbnails_fail/")
    self.thumb_extension = '.' + self.profile.config['thumb_filetype']
  
  def getThumbnail(self, tfile, icon_size):
    path = self.getThumbnailPath(tfile, icon_size)
    fail_path = self.getThumbnailFailPath(tfile, icon_size)
    thumb_type = self.getThumbnailType(tfile)
    if thumb_type is None:
      return None
    elif not os.path.exists(path) and not os.path.exists(fail_path):
      self.createThumbnail(tfile, path, icon_size, thumb_type=thumb_type)
      return RESULT_WORKING
    else:
      return path
    
  def getThumbnailPath(self, tfile, icon_size):
    icon_folder = os.path.join(self.thumbnails_folder, str(icon_size))
    return os.path.join(icon_folder, str(tfile.getCode()) + self.thumb_extension)
  
  def getThumbnailFailPath(self, tfile, icon_size):
    icon_folder = os.path.join(self.thumbnails_fail_folder, str(icon_size))
    return os.path.join(icon_folder, str(tfile.getCode()) + self.thumb_extension)
  
  def removeThumbnail(self, tfile):
    thumb_file = self.getThumbnailPath(tfile)
    thumb_fail_file = self.getThumbnailFailPath(tfile)
    if os.path.exists(thumb_file):
      os.remove(thumb_file)
    if os.path.exists(thumb_fail_file):
      os.remove(thumb_fail_file)
  
  def getThumbnailType(self, tfile):
    if tfile.getMime() == 'folder':
      return THUMB_FOLDER
    elif tfile.getMime() in VIDEO_MIMES:
      return THUMB_VIDEO
    elif tfile.getMime() in IMAGE_MIMES:
      return THUMB_IMAGE
    return None
  
  def createThumbnail(self, tfile, thumb_file, icon_size, thumb_type=None):
    thumb_folder = os.path.dirname(thumb_file)
    if not os.path.isdir(thumb_folder):
      os.makedirs(thumb_folder)
    if not self.profile.fileExists(tfile):
      return False
    else:
      path = self.profile.getFilePath(tfile)
      if thumb_type is None:
        thumb_type = self.getThumbnailType(tfile)
      if thumb_type == THUMB_VIDEO:
        self.createVideoThumbnail(path, thumb_file, icon_size)
      elif thumb_type == THUMB_IMAGE:
        self.createImageThumbnail(path, thumb_file, icon_size)
      elif thumb_type == THUMB_FOLDER:
        self.createFolderThumbnail(path, thumb_file, icon_size)
      else:
        return False
  
  def createVideoThumbnail(self, path, thumb_file, icon_size):
    args = ["ffmpegthumbnailer", "-i", path, "-o", thumb_file, "-s", str(icon_size) ]
    process = Popen(args)
  
  def createImageThumbnail(self, path, thumb_file, icon_size):
    icon_format = str(icon_size) + "x" + str(icon_size)
    args = ["convert", path + "[0]", "-thumbnail", icon_format, thumb_file]
    process = Popen(args)
  
  def createFolderThumbnail(self, path, thumb_file, icon_size):
    fnames = self._getFilesInFolder(path)
    thumb_created = False
    for fname in fnames:
      fpath = os.path.join(path, fname)
      if not os.path.isdir(fpath):
        mime = guessMime(fpath)
        if mime in VIDEO_MIMES:
          self.createVideoThumbnail(fpath, thumb_file, icon_size)
          thumb_created = True
          break
        elif mime in IMAGE_MIMES:
          self.createImageThumbnail(fpath, thumb_file, icon_size)
          thumb_created = True
          break
    return thumb_created
  
  def _getFilesInFolder(self, location):
    result = []
    for root, _, files in os.walk(location):
      for fname in files:
        _, ext = os.path.splitext(fname)
        result.append(os.path.join(root, fname))
    sr = natsorted(result, lambda x : x.lower())
    return sr


def start(*args, **kargs):
  t = ThumbManager(*args, **kargs)
  return t

