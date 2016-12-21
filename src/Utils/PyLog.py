#!/usr/bin/env python3

import os
import shutil
from datetime import datetime

import logging

## PyLog: simple logger

BACKUP_LOGS = 2

class PyLog():
  
  def __init__(self, log_folder):
    self.log_folder = log_folder
    if not os.path.exists(self.log_folder):
      os.mkdir(self.log_folder)
    self.formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(name)s :: %(message)s', '%m-%d %H:%M:%S')
    
  def moveOldLogs(self, log_filepath):
    for i in range(BACKUP_LOGS-1, 0, -1):
      log_file = log_filepath + '.' + str(i)
      if os.path.exists(log_file):
        move_to = log_filepath + '.' + str(i+1)
        shutil.move(log_file, move_to)
    if os.path.exists( log_filepath ):
      move_to = log_filepath + ".1"
      shutil.move(log_filepath, move_to)
  
  def createDebugLogger(self, log_name, instance=None):
    return self.createLogger(log_name, instance, logging.DEBUG)
  
  def createInfoLogger(self, log_name, instance=None):
    return self.createLogger(log_name, instance, logging.INFO)
  
  def createLogger(self, log_name, instance=None, log_type=logging.INFO):
    if instance is None:
      logger = logging.getLogger()
    else:
      logger = logging.getLogger(instance.__class__.__name__)
    logger.setLevel(log_type)
    # Set log file
    if log_name is None:
      log_name = 'main.log'
    log_file = os.path.join(self.log_folder, log_name)
    # Backup old logs
    self.moveOldLogs(log_file)
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(self.formatter)
    logger.addHandler(fh)
    if log_type == logging.DEBUG:
      # add a print to screen handler
      ch = logging.StreamHandler()
      ch.setLevel(log_type)
      ch.setFormatter(self.formatter)
      logger.addHandler(ch)
    return logger
    
def new(*args, **kwargs):
  pl = PyLog(*args, **kwargs)
  return pl
