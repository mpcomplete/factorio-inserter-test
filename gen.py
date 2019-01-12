#!/usr/bin/env python

import sys
import string

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
    return Chunk.template.substitute(
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


def calcDropOffset(x, y):
  """x, y range [-1, 1]."""
  return Point(x*.2, y*.2)


class Full:
  """All the chunks together."""
  def __init__(self):
    self.chunks = []

  def genChunks(self):
    row, col = 0, 0
    for py in range(7):
      for px in range(7):
        for dy in range(7):
          for dx in range(7):
            row = py*7 + px
            col = dy*7 + dx
            chunk = Chunk(col * (Chunk.width+1), row * (Chunk.height+1))
            chunk.moveChests(Point(px-3, py-3), Point(dx-3,dy-3), calcDropOffset(0, 0))
            if row > 0:
              # Connect to above chunk
              chunk.connectTo(self.chunks[(row-1)*7*7 + col])
            if row == 0 and col > 0:
              # Connect to left chunk
              chunk.connectTo(self.chunks[row*7*7 + col-1])

            self.chunks.append(chunk)
            col += 1
      row += 1

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
            kind = "hazard-concrete-left" if y < 2 else "concrete" 
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
with open("full-template.json", "r") as f:
  Full.template = string.Template(f.read())

f = Full()
f.genChunks()
print(f.substitute())