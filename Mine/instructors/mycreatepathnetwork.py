import sys, pygame, math, numpy, random, time, copy, itertools
from pygame.locals import *
from itertools import *
from constants import *
from utils import *
from core import *


# Creates a pathnode network that connects the midpoints of each navmesh together
def myCreatePathNetwork(world, agent = None):
	nodes = []
	edges = []
	polys = []
	### YOUR CODE GOES BELOW HERE ###
	worldlines = world.getLines()
	allPoints = world.getPoints()
	allPoints.sort()
	unvisitedLines = world.getLines()
	# unvisitedCopies = unvisitedLines[:]
	obstacles = world.getObstacles()
	polysLines = []	#lines for all convex hulls created

	#### 1. Create mesh of convex hulls ####
	while unvisitedLines:
		leftLine = getLeftLine( unvisitedLines ) 
		unvisitedLines.remove( leftLine )
		## usedAtAll = False 
		for point in allPoints: ## check from leftmost to rightmost point/line in the world
			## cannot be the same point and cannot intersect with any worldlines
			if ( not point in leftLine and \
			not rayTraceWorldWithThreshold(leftLine[0], point, worldlines, 0.5) and \
			not rayTraceWorldWithThreshold(leftLine[1], point, worldlines, 0.5) and \
			not rayTraceWorldWithThreshold(leftLine[0], point, polysLines, 0.5) and \
			not rayTraceWorldWithThreshold(leftLine[1], point, polysLines, 0.5) ):
				
				## new lines that may become a polygon
				newLines = [ (point, leftLine[0]), (point, leftLine[1]), (leftLine[0], leftLine[1]) ] 
				valid = True
				for obs in obstacles:
					for line in newLines: ## check the lines are not inside an obstacle
						midpoint = getLineMidpoint(line) #get the midpoint of the line
						if ( pointInsidePolygonLines( midpoint, obs.getLines() ) and \
							not pointOnPolygonWithThreshold( midpoint, obs.getLines(), 0.01 ) ):
							valid = False

				if valid:
					newPoly = [ point, leftLine[0], leftLine[1] ] ## the new polygon
					# usedAtAll = True 
					if appendPolyNoDuplicates( newPoly, polys ): ## avoid duplicates
						for line in newLines:
							appendLineNoDuplicates(line, polysLines)
							appendLineNoDuplicates(line, unvisitedLines)
						break

	#### optimize mesh, combine convex hulls ####
	polPairs = itertools.combinations(polys, 2)
	for pair in polPairs:
		poly1 = pair[0]
		poly2 = pair[1]
		if poly1 in polys and poly2 in polys and polygonsAdjacent( poly1, poly2 ):
			newPol = set(poly1 + poly2)
			newPol = list(newPol)
			common = commonPoints(poly1, poly2)                # 1. get common points
			nonCommon = [p for p in newPol if p not in common] # 2. get non-common points
			# 3. add one common point that makes a line with the last non-common point	
			newPol = [common[0], nonCommon[0], common[1], nonCommon[1]]
			# drawPolygon(newPol, world.debug, (255,0,0), 5, True)
			if isConvex(newPol):
				polys.remove( poly1 )
				polys.remove( poly2 )
				polys.append( newPol )

	#### 2. Create path nodes ####
	for poly in polys:
		midpoints = [] #nodes of the polygon
		goodPoints = []
		# for lines in itertools.combinations(poly, 2): #returns pairs of lines [ (x1,y1), (x2,y2) ]
		poly.append(poly[0])
		for p1, p2 in pairwise(poly):
			# midpoint = getLineMidpoint(lines)
			midpoint = getLineMidpoint( ( p1, p2 ) )
			drawCross(world.debug,midpoint, (0, 255, 0), 5)
			appendPointNoDuplicates( midpoint, nodes )
			appendPointNoDuplicates( midpoint, midpoints )

	#### 3. Create path node edges ####	
		for point in midpoints:
			valid = True
			for obs in obstacles:
				if point in nodes and ( pointOnPolygon( point, obs.getPoints() ) or pointOnWorldBoundary(point, world) or \
				pointOnPolygonWithThreshold(point, obs.getLines(), world.agent.getRadius() * 0.5 ) ):
					# midpoints.remove(point)
					nodes.remove(point) 
					valid = False
			if valid:
				goodPoints.append( point )
		nodeComb = itertools.combinations( goodPoints, 2 )
		for comb in nodeComb:
			if not rayTraceWorldWithThreshold(comb[0], comb[1], worldlines, 0.5):
				appendLineNoDuplicates( comb, edges )

	### YOUR CODE GOES ABOVE HERE ###
	return nodes, edges, polys

"""
	Returns a list of neighbors to poly1 from polys.
	
"""
def getPolygonNeighbors(poly1, polys):
	neighbors = []
	for poly2 in polys:
		if polygonsAdjacent( poly1, poly2 ):
			neighbors.append(poly2)
	return neighbors

"""
	Returns a convex hull from a set of n points.
"""
def convexHull(points, n):
	hull = [-1] * (n)
	if (n < 3):
		return
	l = 0 #leftmost point
	for i in range(1, n):
		if points[i][0] < points[l][0]:
			l = i
	p = l
	q = ( p + 1 ) % n
	for i in range(0,n):
		if ( getOrientation(points[p], points[i], points[q]) == 2 ):
			q = i
	hull[p] = q
	p = q

	while (p != l):
		q = ( p + 1 ) % n
		for i in range(0,n):
			if ( getOrientation(points[p], points[i], points[q]) == 2 ):
				q = i
		hull[p] = q
		p = q

	hull = [p for p in hull if p != -1]
	convexHull = [ (points[i][0], points[i][1]) for i in hull ]

	return convexHull

"""
# To find orientation of ordered triplet (p, q, r).
# The function returns following values
# 	0 --> p, q and r are colinear
# 	1 --> Clockwise
# 	2 --> Counterclockwise
# p, q, and r are points (x,y)
# """
def getOrientation(p, q, r):
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if (val == 0):
    	return 0  #colinear
    if val > 0:
    	return 1
    else:
    	return 2

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

"""
	Returns true if the two combined polygons have any intersecting polygons
	within their intersection or overlap with any other world line.
"""
def polygonsIntersection(poly1, poly2, world):
	return

"""
	Special routine for appending a polygon (as a list of points), making sure there are 
	no duplicates added. Changes made by side-effect.
	Returns True if the new polygon was appended, False otherwise
"""
def appendPolyNoDuplicates(poly, polys):
	perm = itertools.permutations( poly, len(poly) )
	valid = True
	for comb in perm:
		comb = list(comb)
		if comb in polys:
			valid = False
	if valid:
		polys.append(poly)
	return valid

"""
	Special routine for appending a point to a list of points, making sure there are 
	no duplicates added. Changes made by side-effect.
"""
def appendPointNoDuplicates(point, points):
	if (point in points) == False:
		return points.append(point)
	else:
		return points

"""
	Same as pointOnPolygon but with a threshold and takes a polygon 
	defined as a list of lines.
"""
def pointOnPolygonWithThreshold(point, polygonLines, threshold):
	for line in polygonLines:
		if minimumDistance(line, point) < threshold:
			return True
	return False

"""
	Returns true if a point is on the world line boundaries.
"""
def pointOnWorldBoundary(point, world):
	size = world.dimensions #tuple (x,y)	
	worldPoints = [ (0, 0), (size[0], 0), (0, 0), (0, size[1]), \
	(0, size[1]), (size[0], size[1]), (size[0], size[1]), (size[0], 0) ]
	return pointOnPolygon(point, worldPoints)

"""
	Returns the leftmost line among the given list of lines.
"""
def getLeftLine(linesTuple):
	midpoints = [ ( i, 0.5 * abs( line[0][0] - line[1][0] ) ) for i, line in enumerate(linesTuple) ]
	index, mid = min(midpoints, key = lambda x:x[1])
	return linesTuple[index]

"""
	Returns the midpoint of a line which is a tuple of two points: ( (x1, y1), (x2, y2) )
"""
def getLineMidpoint(line):
	return ( 0.5 * ( line[0][0] + line[1][0] ), 0.5 * ( line[0][1] + line[1][1] ) )
