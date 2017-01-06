#!/usr/bin/env python3

from mimetypes import guess_extension as guessExtension

import magic

def guessMime(path):
  el = magic.detect_from_filename(path)
  return el.mime_type
