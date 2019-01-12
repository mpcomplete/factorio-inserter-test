#!/usr/bin/env python
# Examines results of a test run via a blueprint of all chunks.

import sys
import zlib
import base64
import json

def analyzeFile(f):
  bpString = f.read()
  bpCompressed = base64.b64decode(bpString[1:])
  bpJsonStr = zlib.decompress(bpCompressed)
  bpJson = json.loads(bpJsonStr)

  entities = bpJson["blueprint"]["entities"]
  results = []
  for e in entities:
    if e["name"] == "express-stack-inserter" and "drop_position" in e:
      dropX = float(e["drop_position"]["x"])
      dropY = float(e["drop_position"]["y"])
      # Normalize to (-1,-1), (1,1)
      offsetX = int(5*(dropX - round(dropX)))
      offsetY = int(5*(dropY - round(dropY)))
    if e["name"] == "SNTD-nixie-tube-small" and "control_behavior" in e:
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

  # Convert y,x to row,col and make a map of it.
  width = 8
  height = 10
  resultMap = {(r[0]/height, r[1]/width): r[2] for r in results}
  return (offsetX, offsetY, resultMap)

def findFastest(resultSets):
  bests = {}
  for pos, time in resultSets[0][2].items():
    best = resultSets[0]
    for results in resultSets[1:]:
      if results[2][pos] < best[2][pos]:
        best = results
    bests[pos] = (best[0], best[1], best[2][pos])

  return bests

def main():
  resultSets = []
  for each in sys.argv[1:]:
    with open(each, "r") as f:
      results = analyzeFile(f)
      resultSets.append(results)
      print(each, results[0:2])

  bests = findFastest(resultSets)
  print(bests)

if __name__ == "__main__":
  main()