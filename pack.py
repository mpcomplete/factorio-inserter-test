#!/usr/bin/env python

import sys
import zlib
import base64
import json

bp = sys.stdin.read()
bpJson = json.loads(bp)
bpCompressed = zlib.compress(json.dumps(bpJson))
bp64 = base64.b64encode(bpCompressed)
print('0%s' % bp64)
