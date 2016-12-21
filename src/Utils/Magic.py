#!/usr/bin/env python3

import os

from mimetypes import guess_extension as guessExtension
from mimetypes import guess_type

from subprocess import Popen
from subprocess import PIPE

def guessMime(path):
  if os.path.isdir(path):
    return 'folder'
  mime, _ = guess_type(path)
  if mime is None:
    return _guessMimeAlt(path)
  else:
    return mime

def _guessMimeAlt(path):
  process = Popen(['file', '--mime-type', path], stdout=PIPE)
  res = process.communicate()
  data = res[0].decode('utf-8').strip()
  mime = data.split(': ')[-1]
  return mime
  
