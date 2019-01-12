#!/usr/bin/env python

import sys
import zlib
import base64
import json

bpString = sys.stdin.read()
compressedBP = base64.b64decode(bpString[1:])
bpJson = zlib.decompress(compressedBP)
bp = json.loads(bpJson)
print(json.dumps(bp, indent=4))