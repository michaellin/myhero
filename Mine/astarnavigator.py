import sys, pygame, math, numpy, random, time, copy
import heapq
from pygame.locals import * 

from constants import *
from utils import *
from core import *
from mycreatepathnetwork import *
from mynavigatorhelpers import *

###############################
### AStarNavigator
###		
class AStarNavigator(Navigator):

	def __init__(self):
		Navigator.__init__(self)
		

	### Create the pathnode network and pre-compute all shortest paths along the network.
	### self: the navigator object
	### world: the world object
	def createPathNetwork(self, world):
		self.pathnodes, self.pathnetwork, self.navmesh = myCreatePathNetwork(world, self.agent)
		return None
		
	### Finds the shortest path from the source to the destination using A*.
	### self: the navigator object
	### source: the place the agent is starting from (i.e., it's current location)
	### dest: the place the agent is told to go to
	def computePath(self, source, dest):
		if self.agent != None and self.world != None: 
			self.source = source
			self.destination = dest
			### Step 1: If the agent has a clear path from the source to dest, then go straight there.
			###   Determine if there are no obstacles between source and destination (hint: cast rays against world.getLines(), check for clearance).
			###   Tell the agent to move to dest
			### Step 2: If there is an obstacle, create the path that will move around the obstacles.
			###   Find the pathnodes closest to source and destination.
			###   Create the path by traversing the self.next matrix until the pathnode closes to the destination is reached
			###   Store the path by calling self.setPath()
			###   Tell the agent to move to the first node in the path (and pop the first node off the path)
			if clearShot(source, dest, self.world.getLines(), self.world.getPoints(), self.agent):
				self.agent.moveToTarget(dest)
			else:
				start = findClosestUnobstructed(source, self.pathnodes, self.world.getLinesWithoutBorders())
				end = findClosestUnobstructed(dest, self.pathnodes, self.world.getLinesWithoutBorders())
				if start != None and end != None:
					newnetwork = unobstructedNetwork(self.pathnetwork, self.world.getGates())
					closedlist = []
					path, closedlist = astar(start, end, newnetwork)
					if path is not None and len(path) > 0:
						path = shortcutPath(source, dest, path, self.world, self.agent)
						self.setPath(path)
						if self.path is not None and len(self.path) > 0:
							first = self.path.pop(0)
							self.agent.moveToTarget(first)
		return None
		
	### Called when the agent gets to a node in the path.
	### self: the navigator object
	def checkpoint(self):
		myCheckpoint(self)
		return None

	### This function gets called by the agent to figure out if some shortcutes can be taken when traversing the path.
	### This function should update the path and return True if the path was updated.
	def smooth(self):
		return mySmooth(self)

	def update(self, delta):
		myUpdate(self, delta)

def unobstructedNetwork(network, worldLines):
	newnetwork = []
	for l in network:
		hit = rayTraceWorld(l[0], l[1], worldLines)
		if hit == None:
			newnetwork.append(l)
	return newnetwork

# network: a list of lines of the form ((x1, y1), (x2, y2)) that comprise a path network.
def astar(init, goal, network):
	path = []
	open = []
	closed = []
	### YOUR CODE GOES BELOW HERE ###
	openDict = {}
	openDict[init] = 0 + distance(init, goal)
	heapq.heappush( open, ( 0 + distance(init, goal), Node( init, None, 0 ) ) ) # loc, parent, gcost

	while open: # while still items in queue
		current = heapq.heappop(open) # remove node with lowest priority

		if current[1].loc == goal: # if goal is found, return path
			# print "path astar: ", reconstructPath(current)
			return reconstructPath(current), closed

		closed.append(current[1].loc) # nodes already visited
		for line in network:  # look for all succesors
			succesor = inTuple(line, current[1].loc)
			#print "succ ", succesor
			if succesor: # if not None
				gcost = current[1].gcost + 1
				hcost = distance(succesor, goal)
				total = gcost + hcost
				if ( (succesor not in closed and succesor not in openDict) or \
					(succesor in openDict and total < openDict.get(succesor)) ):
					heapq.heappush(open, ( total, Node(succesor, current, gcost) ))
					openDict[succesor] = total
	### YOUR CODE GOES ABOVE HERE ###
	return path, closed

# called every game tick	
def myUpdate(nav, delta):
	### YOUR CODE GOES BELOW HERE ###
	# source = nav.agent.getLocation()
	# destination = nav.agent.getMoveTarget()
	# gates = nav.world.getGates()
	# if rayTraceWorld(source, destination, gates): # if there is an intersection
	# 	nextNode = findClosestUnobstructed(source, nav.pathnodes, nav.world.getLinesWithoutBorders())
	# 	print "replanning"
	# 	if not nextNode:
	# 		nav.agent.stopMoving()
	# 	else:
	# 		nav.agent.moveToTarget(nextNode) # move to the closest unobstructed node
	# 		nav.setPath([nextNode])

	## try 2:
	source = nav.agent.getLocation()
	destination = nav.agent.getMoveTarget()
	gates = nav.world.getGates()
	worldlines = nav.world.getLines()
	# collisions = rayTraceWorld(source, destination, gates)
	if rayTraceWorld(source, destination, worldlines): # if there is an intersection
		nav.agent.stopMoving()
		nextNode = findClosestUnobstructed(source, nav.pathnodes, nav.world.getLinesWithoutBorders())
		# print "replanning"

	## YOUR CODE GOES ABOVE HERE ###
	return None

# called every time the agent reaches one of the nodes in the path it is following.
def myCheckpoint(nav):
	### YOUR CODE GOES BELOW HERE ###
	source = nav.agent.getLocation()
	# destination = nav.agent.getMoveTarget()	
	worldlines = nav.world.getLines()
	if nav.path is not None and len(nav.path) > 0:
		destination = nav.destination
		if rayTraceWorld(source, destination, worldlines): # if there is an intersection
			# print "checkpoint"
			computePath(nav, source, destination)
		if not nav.path: # if path is None, there is no path and agent stops moving
			nav.agent.stopMoving()
	### YOUR CODE GOES ABOVE HERE ###
	return None

def computePath(nav, source, dest):
	if clearShot(source, dest, nav.world.getLines(), nav.world.getPoints(), nav.agent):
		nav.agent.moveToTarget(dest)
	else:
		start = findClosestUnobstructed(source, nav.pathnodes, nav.world.getLinesWithoutBorders())
		end = dest #findClosestUnobstructed(dest, nav.pathnodes, nav.world.getLinesWithoutBorders())
		if start != None and end != None:
			newnetwork = unobstructedNetwork(nav.pathnetwork, nav.world.getGates())
			closedlist = []
			path, closedlist = astar(start, end, newnetwork)
			# print "path computePath: ", path
			if path is not None and len(path) > 0:
				path = shortcutPath(source, dest, path, nav.world, nav.agent)
				nav.setPath(path)
				if nav.path is not None and len(nav.path) > 0:
					first = nav.path.pop(0)
					nav.agent.moveToTarget(first)
	return None

"""
	Returns if var is equivalent to any of the members of the two-member tuple.
	If it is, then it returns the other non-equivalent member.
	Else it returns None. 
"""
def inTuple(tuple, var):
	if var == tuple[0]:
		return tuple[1]
	if var == tuple[1]:
		return tuple[0]
	return None

def reconstructPath(currNode):
	path = []
	#currNode = currNode[1]
	while currNode:
		#print "currNode ", currNode
		path.append(currNode[1].loc)
		currNode = currNode[1].parent
	path.reverse()
	# path = path[1:] # remove init
	# print path
	return path

class Node:
	def __init__(self, loc, parent, gcost):
		"""
		loc: the state to which the node represents
		parent: the node in the tree that generated this node
		gcost: the path cost to reach this node state from the initial state
		"""
		self.loc = loc
		self.parent = parent
		self.gcost = gcost
