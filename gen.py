#!/usr/bin/env python
# Generates a blueprint with inserter timer circuits.
# Usage:
#   ./gen.py <drop-offset-x> <drop-offset-y>     OR
#   ./gen.py
# The former will use drop offsets you specify. The latter will use the
# fastest drop offset for each inserter, using previously gathered data
# from the results/ dir.

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


def calcDropOffset(p):
  """x, y range [-1, 1]."""
  return Point(p.x*.2, p.y*.2)

def getFastestDropOffset(row, col):
  global dropOffset
  global fastestOffsetForPos

  key =  '%s,%s' % (row, col)
  if fastestOffsetForPos != None and key in fastestOffsetForPos:
    return calcDropOffset(fastestOffsetForPos[key].offset)
  return calcDropOffset(dropOffset)

class Full:
  """All the chunks together."""
  def __init__(self):
    self.chunks = []

  def genChunks(self):
    chunkMap = {}
    for row in range(7*7):
      chunkMap[row] = {}
      for col in range(7*7):
        py = row / 7
        px = row % 7
        dy = col / 7
        dx = col % 7
        Full._addChunkToMap(chunkMap, row, col, px, py, dx, dy, getFastestDropOffset(row, col))
    self.chunks = [chunk for chunkRow in chunkMap.values() for chunk in chunkRow.values()]

  def genAllFasterThan(self):
    global fasterThanNResults
    row, col = 0, 0
    chunkMap = {0: {}}
    for each in fasterThanNResults:
      resultRow, resultCol = each.pos[0], each.pos[1]
      py = resultRow / 7
      px = resultRow % 7
      dy = resultCol / 7
      dx = resultCol % 7
      Full._addChunkToMap(chunkMap, row, col, px, py, dx, dy, calcDropOffset(each.offset))
      col += 1
      if col > 7*7:
        col = 0
        row += 1
        chunkMap[row] = {}

    self.chunks = [chunk for chunkRow in chunkMap.values() for chunk in chunkRow.values()]

  @staticmethod
  def _addChunkToMap(chunkMap, row, col, px, py, dx, dy, dropOffset):
      chunk = Chunk(col * (Chunk.width+1), row * (Chunk.height+1))
      chunk.moveChests(Point(px-3, py-3), Point(dx-3,dy-3), dropOffset)
      if row > 0:
        # Connect to above chunk
        chunk.connectTo(chunkMap[row-1][col])
      if row == 0 and col > 0:
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
        matches.append(Object(offset = Point(results['offset']['x'], results['offset']['y']), pos = (row, col)))
  return matches

def main():
  global dropOffset
  global fastestOffsetForPos
  global fasterThanNResults

  if len(sys.argv) == 1:
    with open("results/analyzed.json") as f:
      resultSets = json.load(f)
    fastestOffsetForPos = findFastestForPos(resultSets['results'])
    fasterThanNResults = findAllFasterThan(resultSets['results'], 300)
    dropOffset = Point(0, 0) # for invalid chunks
    sys.stderr.write("Using best offsets as indicated by results data\n")
    sys.stderr.write("Found %d results faster than 500\n" % len(fasterThanNResults))
  else:
    dropOffset = Point(int(sys.argv[1]), int(sys.argv[2]))
    assert(-1 <= dropOffset.x <= 1)
    assert(-1 <= dropOffset.y <= 1)
    sys.stderr.write("Using offset=%d,%d\n" % (dropOffset.x, dropOffset.y))

  f = Full()
  f.genChunks()
#  f.genAllFasterThan()
  print(f.substitute())

if __name__ == "__main__":
  main()