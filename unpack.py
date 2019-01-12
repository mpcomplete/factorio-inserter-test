#!/usr/bin/env python

import sys
import zlib
import base64
import json

bpString = sys.stdin.read()
bpCompressed = base64.b64decode(bpString[1:])
bpJsonStr = zlib.decompress(bpCompressed)
bpJson = json.loads(bpJsonStr)
print(json.dumps(bpJson, indent=4))