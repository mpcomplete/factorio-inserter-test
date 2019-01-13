#!/usr/bin/env python
# Generates a blueprint with inserter timer circuits.
# Usage:
#   ./gen.py <drop-offset-x> <drop-offset-y>     OR
#   ./gen.py <max-time>                          OR
#   ./gen.py
# Version 1 will use drop offsets you specify. Version 2 will generate
# every that transferred 2000 items faster than the given time (171 is
# the fastest I measured). Version 3 will use the fastest drop offset
# for each inserter, using previously gathered data from the results/ dir.

import sys
import string
import os
import json
from analyze import Object

nextId = 0
def genId():
  global nextId
  nextId += 1
  return nextId


class Point:
  def __init__(self, x=0, y=0):
    self.x = x
    self.y = y
  def toStr(self):
    return '"x": %s, "y": %s' % (self.x, self.y)
  def __add__(self, other):
    return Point(self.x + other.x, self.y + other.y)
  def __sub__(self, other):
    return Point(self.x - other.x, self.y - other.y)
  def __eq__(self, other):
    return self.x == other.x and self.y == other.y
  def __ne__(self, other):
    return not (self == other)
  def __hash__(self):
    return hash((self.x, self.y))


class Entity:
  """One thing - e.g. inserter, combinator, etc."""
  def __init__(self, x, y):
    self.pos = Point(x, y)
    self.id = genId()


class Chunk:
  """One instance of inserter + chests + timing circuit."""
  width = 7
  height = 9

  def __init__(self, x, y):
    self.pos = Point(x, y)
    self.n = Entity(x + 5, y + 0)
    self.e = Entity(x + 6, y + 0)
    self.c1 = Entity(x + 0.5, y + 1)
    self.c2 = Entity(x + 5.5, y + 1)
    self.i = Entity(x + 3, y + 5)
    # Pickup/drop chest positions will be overwritten.
    self.p = Entity(x + 4, y + 2)
    self.d = Entity(x + 4, y + 4)
    self.connectedChunks = []

  def substitute(self):
    template = Chunk.template if self._isValid() else Chunk.emptyTemplate
    return template.substitute(
        nixieLeading = self._getNixieStr(),
        nid = self.n.id,
        npos = self.n.pos.toStr(),
        eid = self.e.id,
        epos = self.e.pos.toStr(),
        c1id = self.c1.id,
        c1pos = self.c1.pos.toStr(),
        c2id = self.c2.id,
        c2pos = self.c2.pos.toStr(),
        iid = self.i.id,
        ipos = self.i.pos.toStr(),
        ipickup = self._getPickup().toStr(),
        idrop = self._getDrop().toStr(),
        pid = self.p.id,
        ppos = self.p.pos.toStr(),
        did = self.d.id,
        dpos = self.d.pos.toStr(),
        chunkConnections = self._getChunkConnectionsStr()
      )

  def moveChests(self, pickupPos, dropPos, dropOffset):
    """Positions are relative to inserter."""
    self.p.pos = self.i.pos + pickupPos
    self.d.pos = self.i.pos + dropPos
    self.dropOffset = dropOffset

  def connectTo(self, chunk):
    self.connectedChunks.append(chunk)

  def _getPickup(self):
    return self.p.pos - self.i.pos

  def _getDrop(self):
    return self.d.pos - self.i.pos + self.dropOffset

  def _getNixieStr(self):
    template = string.Template("""
            {
                "position": {
                    "y": $y, 
                    "x": $x
                }, 
                "entity_number": $id, 
                "name": "SNTD-nixie-tube-small"
            }""")
    nixies = [template.substitute(x = self.pos.x + x, y = self.pos.y + 0, id = genId()) for x in range(4,5)]
    return string.join(nixies, ",")

  def _getChunkConnectionsStr(self):
    if len(self.connectedChunks) == 0:
      return ""

    template = string.Template("""
                            {
                                "circuit_id": 1,
                                "entity_id": $id
                            }""")
    connections = [template.substitute(id = chunk.c1.id) for chunk in self.connectedChunks]
    return ",\n" + string.join(connections, ",")

  def _isValid(self):
    if self.d.pos == self.p.pos:
      return False
    if self.i.pos == self.d.pos:
      return False
    if self.i.pos == self.p.pos:
      return False
    return True


class Full:
  """All the chunks together."""

  maxChunksPerRow = 7*7

  def __init__(self):
    self.chunks = []

  def genChunksInGrid(self, getDropOffsetForPos):
    chunkMap = {}
    for row in range(7*7):
      chunkMap[row] = {}
      for col in range(7*7):
        p = Point(row / 7, row % 7)
        d = Point(col / 7, col % 7)
        Full._addChunkToMap(chunkMap, row, col, p, d, getDropOffsetForPos(row, col))
    self.chunks = [chunk for chunkRow in chunkMap.values() for chunk in chunkRow.values()]

  def genChunksFromSet(self, candidatesIn):
    # Sort candidates according to pickup/dropoff locations. Tuple sort is lexicographic - pickup.y sorted first.
    candidates = [Object(
        p = Point(c.row / 7, c.row % 7),
        d = Point(c.col / 7, c.col  % 7),
        offset = calcDropOffset(c.offset)
    ) for c in candidatesIn]
    candidates.sort(key = lambda c: (c.p.y, c.p.x, c.d.y, c.d.x))

    lastPickup = candidates[0].p
    chunkMap = {0: {}}
    row, col = 0, 0
    for candidate in candidates:
      if lastPickup.y != candidate.p.y or col > Full.maxChunksPerRow:
        col = 0
        row += 1
        chunkMap[row] = {}
      lastPickup = candidate.p
      Full._addChunkToMap(chunkMap, row, col, candidate.p, candidate.d, candidate.offset)
      col += 1

    self.chunks = [chunk for chunkRow in chunkMap.values() for chunk in chunkRow.values()]

  @staticmethod
  def _addChunkToMap(chunkMap, row, col, p, d, dropOffset):
      chunk = Chunk(col * (Chunk.width+1), row * (Chunk.height+1))
      chunk.moveChests(Point(p.x-3, p.y-3), Point(d.x-3,d.y-3), dropOffset)
      if row > 0 and col in chunkMap[row-1]:
        # Connect to above chunk
        chunk.connectTo(chunkMap[row-1][col])
      if col > 0:
        # Connect to left chunk
        chunk.connectTo(chunkMap[row][col-1])
      chunkMap[row][col] = chunk

  def getTilesStr(self):
    template = string.Template("""
            {
                "position": {
                    "y": $y, 
                    "x": $x
                }, 
                "name": "$kind"
            }""")
    tiles = []
    for chunk in self.chunks:
      for y in range(Chunk.height):
        for x in range(Chunk.width):
          tiles.append(template.substitute(
            x = x + chunk.pos.x,
            y = y + chunk.pos.y,
            kind = "hazard-concrete-left" if (y < 2 or not chunk._isValid()) else "concrete" 
          ))
    return string.join(tiles, ",")

  def substitute(self):
    chunkStrs = [chunk.substitute() for chunk in self.chunks]
    return Full.template.substitute(
      starterid = genId(),
      allEntities = string.join(chunkStrs, ","),
      allTiles = self.getTilesStr()
    )

with open("chunk-template.json", "r") as f:
  Chunk.template = string.Template(f.read())
with open("chunk-empty-template.json", "r") as f:
  Chunk.emptyTemplate = string.Template(f.read())
with open("full-template.json", "r") as f:
  Full.template = string.Template(f.read())

def findFastestForPos(resultSets):
  bests = {}
  for pos, time in resultSets[0]['posToTimeMap'].items():
    best = resultSets[0]
    for results in resultSets[1:]:
      if pos not in results['posToTimeMap']:
        # Indicates an invalid chunk (pickup/dropoff/inserters overlap).
        # Older results have invalid chunks, newer do not.
        best = None
        break
      if results['posToTimeMap'][pos] < best['posToTimeMap'][pos]:
        best = results
    if best != None:
      bests[pos] = Object(offset = Point(best['offset']['x'], best['offset']['y']), time = best['posToTimeMap'][pos])

  return bests

def findAllFasterThan(resultSets, maxTime):
  matches = []
  for results in resultSets:
    for pos, time in results['posToTimeMap'].items():
      if int(time) < maxTime:
        row, col = [t(s) for t,s in zip((int,int), pos.split(','))]
        matches.append(Object(offset = Point(results['offset']['x'], results['offset']['y']), row = row, col = col))
  return matches

def calcDropOffset(p):
  """x, y range [-1, 1]."""
  return Point(p.x*.2, p.y*.2)

def getFastestDropOffset(row, col, fastestOffsetForPos):
  key =  '%s,%s' % (row, col)
  if fastestOffsetForPos != None and key in fastestOffsetForPos:
    return calcDropOffset(fastestOffsetForPos[key].offset)
  # Fallback - only happens for invalid chunks anyway.
  return calcDropOffset(Point(-1, -1))

def main():
  f = Full()

  if len(sys.argv) == 1:
    with open("results/analyzed.json") as fp:
      resultSets = json.load(fp)
    fastestOffsetForPos = findFastestForPos(resultSets['results'])
    sys.stderr.write("Using fastest offsets per pickup/dropoff as indicated by results data\n")
    f.genChunksInGrid(lambda r,c: getFastestDropOffset(r, c, fastestOffsetForPos))
  elif len(sys.argv) == 2:
    with open("results/analyzed.json") as fp:
      resultSets = json.load(fp)
    maxTime = int(sys.argv[1])
    matches = findAllFasterThan(resultSets['results'], maxTime)
    f.genChunksFromSet(matches)
    sys.stderr.write("Found %d results faster than %d\n" % (len(matches), maxTime))
  else:
    offset = Point(int(sys.argv[1]), int(sys.argv[2]))
    assert(-1 <= offset.x <= 1)
    assert(-1 <= offset.y <= 1)
    sys.stderr.write("Using offset=%d,%d\n" % (offset.x, offset.y))
    dropOffset = calcDropOffset(offset)
    f.genChunksInGrid(lambda r,c: dropOffset)

  print(f.substitute())

if __name__ == "__main__":
  main()