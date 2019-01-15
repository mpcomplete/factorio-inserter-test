#!/usr/bin/env python
# An attempt to correlate the travel angle and distance change of an inserter with its speed.

import sys
import string
import os
import json
import math
from analyze import Object
from gen import Point
from gen import findAllFasterThan

def calcDropOffset(p):
  """x, y range [-1, 1]."""
  return Point(p.x*.2, p.y*.2)

def dotp(u, v):
  return u.x*v.x + u.y*v.y

def dist(u):
  return math.hypot(u.x, u.y)

def clamp(minX, x, maxX):
  return max(min(x, maxX), minX)

def getAngle(u, v):
  return math.acos(clamp(-1.0, dotp(u,v)/(dist(u) * dist(v)), 1.0))

def getAngleAndLen(c):
  o = Point(3, 3)
  p = Point(c.row / 7, c.row % 7) - o
  d = Point(c.col / 7, c.col  % 7) - o + calcDropOffset(c.offset)
  if dist(p) == 0 or dist(d) == 0:
    return Object(angle = 0, len = 0, time = 0)
  return Object(angle = getAngle(p, d), len = abs(dist(p) - dist(d)), time = c.time)

def getAngleVsTime(results):
  avt = [getAngleAndLen(c) for c in results]
  avt.sort(key = lambda each: (each.len, each.angle))
  return avt

def main():
  with open("results/analyzed.json") as fp:
    resultSets = json.load(fp)
  matches = findAllFasterThan(resultSets['results'], 1000000)
  avt = getAngleVsTime(matches)
  for each in avt:
    if each.time == 0:
      continue
    print("%d = %.05f,%.05f" % (each.time, each.angle, each.len))

if __name__ == "__main__":
  main()