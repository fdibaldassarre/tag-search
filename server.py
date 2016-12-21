#!/usr/bin/env python3

import argparse

from flask import Flask
from flask import request

from src import TMWeb

parser = argparse.ArgumentParser(description='Tag Search Server')
parser.add_argument('--port', help='port to use', default=44660)
parser.add_argument('--profile', help='profile to use', default='default')
parser.add_argument('--debug', action='store_true', help='debug mode')

args = parser.parse_args()

profile = args.profile
port = args.port
debug = args.debug

app = Flask('TagSearchServer')
aw = TMWeb.start(profile)

@app.route('/tagsearch/manager.py', methods=['GET'])
def pass_update():
  data = request.values.to_dict()
  return aw.run(data)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=port, debug=debug)
