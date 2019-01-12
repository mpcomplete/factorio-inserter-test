#!/usr/bin/env python
# Examines results of a test run via a blueprint of all chunks.

import sys
import zlib
import base64
import json

class Object(dict):
  def __init__(self,**kw):
    dict.__init__(self,kw)
    self.__dict__.update(kw)

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
  return Object(offset = (offsetX, offsetY), posToTimeMap = resultMap)

def analyzeFiles(files):
  resultSets = []
  for each in files:
    with open(each, "r") as f:
      results = analyzeFile(f)
      resultSets.append(results)
  return resultSets

def findFastest(resultSets):
  bests = {}
  for pos, time in resultSets[0].posToTimeMap.items():
    best = resultSets[0]
    for results in resultSets[1:]:
      if pos not in results.posToTimeMap:
        # Indicates an invalid chunk (pickup/dropoff/inserters overlap).
        # Older results have invalid chunks, newer do not.
        best = None
        break
      if results.posToTimeMap[pos] < best.posToTimeMap[pos]:
        best = results
    if best != None:
      bests[pos] = Object(offset = best.offset, time = best.posToTimeMap[pos])

  return bests

def main():
  sys.stderr.write("Analyzing files: %s\n" % sys.argv[1:])
  resultSets = analyzeFiles(sys.argv[1:])
  bests = findFastest(resultSets)
  sys.stderr.write("Results gathered for these offsets: %s\n" % sorted(set([(b.offset[0], b.offset[1]) for b in bests.values()])))
  sys.stderr.write("Fastest time was: %s\n" % min(bests.values(), key = lambda b: b.time))

  with open("results/analyzed.json", "w") as f:
    jsonObj = {'results': []}
    for results in resultSets:
      jsonObj['results'].append({
        'offset': {'x': results.offset[0], 'y': results.offset[1]},
        'posToTimeMap':  {('%s,%s' % (r[0][0], r[0][1])): r[1] for r in results.posToTimeMap.items()}
      })
    json.dump(jsonObj, f, indent=2)
 
if __name__ == "__main__":
  main()