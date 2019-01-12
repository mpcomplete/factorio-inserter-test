#!/usr/bin/env python
# Examines results of a test run via a blueprint of all chunks.

import sys
import zlib
import base64
import json

bpString = sys.stdin.read()
bpCompressed = base64.b64decode(bpString[1:])
bpJsonStr = zlib.decompress(bpCompressed)
bpJson = json.loads(bpJsonStr)

entities = bpJson["blueprint"]["entities"]
results = []
for e in entities:
  if e["name"] != "SNTD-nixie-tube-small" or "control_behavior" not in e:
      continue
  result = int(e["control_behavior"]["circuit_condition"]["constant"])
  y = int(e["position"]["y"])
  x = int(e["position"]["x"])
  results.append((y, x, result))

# Sort by y, with x breaking ties. sorted() is stable.
results = sorted(results, key = lambda r: r[1])
xmin = results[0][1]
results = sorted(results, key = lambda r: r[0])
ymin = results[0][0]

# Normalize top left to (0,0).
results = [(r[0] - ymin, r[1] - xmin, r[2]) for r in results]

# Convert y,x to row,col
width = 8
height = 10
results = [(r[0]/height, r[1]/width, r[2]) for r in results]
for r in sorted(results, key = lambda r: r[2]):
    print(r)