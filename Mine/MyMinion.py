import sys, pygame, math, numpy, random, time, copy
from pygame.locals import * 

from constants import *
from utils import *
from core import *
from moba import *

############## Constants ##############
MINIONRANGE = 250
ATDEST = 20

VERBOSE = 1 # change to 1 to have comments printed

class MyMinion(Minion):
    
    def __init__(self, position, orientation, world, image = NPC, speed = SPEED, viewangle = 360, hitpoints = HITPOINTS, firerate = FIRERATE, bulletclass = SmallBullet):
        Minion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass)
        self.states = [Idle]
        ### Add your states to self.states (but don't remove Idle)
        ### YOUR CODE GOES BELOW HERE ###
        self.states.extend([HuntTower])
        ### YOUR CODE GOES ABOVE HERE ###

    def start(self):
        Minion.start(self)
        self.changeState(Idle)

############################
### Idle
###
### This is the default state of MyMinion. The main purpose of the Idle state is to figure out what state to change to and do that immediately.

class Idle(State):
    
    def enter(self, oldstate):
        State.enter(self, oldstate)
        # stop moving
        self.agent.stopMoving()
    
    def execute(self, delta = 0):
        State.execute(self, delta)
        ### YOUR CODE GOES BELOW HERE ###
        self.agent.changeState(HuntTower)
        ### YOUR CODE GOES ABOVE HERE ###
        return None

##############################
### Taunt
###
### This is a state given as an example of how to pass arbitrary parameters into a State.
### To taunt someome, Agent.changeState(Taunt, enemyagent)

class Taunt(State):

    def parseArgs(self, args):
        self.victim = args[0]

    def execute(self, delta = 0):
        if self.victim is not None:
            print "Hey " + str(self.victim) + ", I don't like you!"
        self.agent.changeState(Idle)

##############################
### YOUR STATES GO HERE:

class HuntTower(State):

    def enter(self):
        enemyTowers = getEnemyTowers(self.agent.getTeam())
        targetTower = getClosest(enemyTowers, self.agent.getLocation())
        otherTower = otherTower(targetTower, enemyTowers)
        possibleDest = self.agent.getPossibleDestinations()
        possibleDest = [d for d in possibleDest if distance(d, targetTower) < MINIONRANGE] 

        alpha = 0.5 #weight for distance to tower 
        beta = -1.0 * 0.5 #weight for distance to other tower 

        rankDestinations = []
        for i, tower in enumerate(possibleDest):
            rankDestinations.append( (i, alpha * distance(self.agent.getLocation(), targetTower) + beta * \
                            distance(self.agent.getLocation(), otherTower) ) )

        rankDestinations = sorted(rankDestinations, key=lambda x: x[1], reverse = True)
        dest = possibleDest[rankDestinations[0][0]]
        self.agent.navigateTo(dest)

        return None
    
    def execute(self, delta = 0):

        return None

############## Helpers ##############
"""
Get the other tower.
"""
def otherTower(tower, enemyTowers):
    for t in enemyTowers:
        if t != tower:
            return t
    return None

"""
Given a list of positions and a current agent position, compute distances
to every position in the list. Return the closest distance. Distances are 
calculated as Manhattan distances.
"""
def getClosestDistances(list, currPos):
    dist = []
    for l in list:
        dist.append( (l, distance( currPos, l )) )
    dist.sort(key = lambda x:x[1])
    # tuple (item, distance)
    return dist[0][0]

"""
Given a list of NPCs and a current agent position, compute distances
to every item in the list. Return the closest item. Distances are 
calculated as Manhattan distances.
"""
def getClosest(list, currPos):

    if list == None or currPos == None or len(list) == 0:
        return None

    else:
        dist = []
        for l in list:
            dist.append( (l, distance( currPos, l.getLocation() )) )
        dist.sort(key = lambda x:x[1])
        # tuple (item, distance)
        return dist[0][0]

"""
Returns a pointer to the hero with opposite team flag to the agent hero
given as a parameter.
"""
def getEnemyHero(agent):
    world = agent.world
    enemyNPC = world.getEnemyNPCs(agent.getTeam())
    for thing in enemyNPC:
        if isinstance(thing, Hero):
            return thing

"""
Returns a list of all minions in the world (whether visible or not)
in the opposite team to the team of the agent given as parameter.
"""
def getEnemyMinions(agent):
    world = agent.world
    enemyNPC = world.getEnemyNPCs(agent.getTeam())
    enemyMinions = []
    for thing in enemyNPC:
        if isinstance(thing, Minion):
            enemyMinions.append(thing)
    return enemyMinions

"""
Returns a list of enemy minions that are visible and in the shooting range 
given as parameter.
"""
def enemyMinionsInShootingRange(agent, range):
    minionsList = agent.getVisibleType(Minion)
    minionsList = [ m for m in minionsList if \
        ( (distance(m.getLocation(), agent.getLocation()) < range) and (m.getTeam() != agent.getTeam()) ) ]
    return minionsList

"""
Returns a list of enemy heros that are visible and in the shooting range 
given as parameter.
"""
def enemyHerosInShootingRange(agent, range):
    herosList = agent.getVisibleType(Hero)
    herosList = [ m for m in herosList if \
        ( (distance(m.getLocation(), agent.getLocation()) < range) and (m.getTeam() != agent.getTeam()) ) ]
    return herosList

"""
Returns a list of bullets that are withing a distance of DODGERANGE of the agent.
"""
def bulletsInRange(agent):
    world = agent.world
    allBullets = world.getBullets()
    inRangeBullets = []
    for bullet in allBullets:
        if ( distance( bullet.getLocation() , agent.getLocation() ) < DODGERANGE ):
            inRangeBullets.append( bullet )
    return inRangeBullets

"""
Returns a dodge angle that will result in a valid position
Else return None.
"""
def getDodgeAngle(agent, bullet):
    possibleDest = agent.getPossibleDestinations()
    orientation = bullet.orientation
    # TODO change
    for a in [90, 270]:
        angle = orientation + a
        vector = (math.cos(math.radians(angle)), -math.sin(math.radians(angle)))
        diff = (vector[0]*agent.getRadius()*1.5, vector[1]*agent.getRadius()*1.5)
        newPos = ( agent.getLocation()[0] + diff[0], agent.getLocation()[1] + diff[1] ) 
        
        if inPossibleDestinations(newPos, possibleDest):
            # print "angle, ", angle
            return angle

    return None

"""
Returns True if the target is visible and within shooting range of the agent.
The shooting range is given as a parameter.
"""
def inShootingRange(agent, target, range):
    visible = agent.getVisible()
    if (target in visible) and (distance(target.getLocation(), agent.getLocation()) < range):
        return True
    return False

"""
Given a current position and a destination, checks if agent is
at the destination with a threshold given by ATDEST.
"""
def atDestination(currPos, dest):
    if ( distance(currPos, dest) < ATDEST ):
        # print "it's true"
        return True
    return False

"""
Given a target destination and a list of possible locations,
returns if the destination is within the possible locations.
"""
def inPossibleDestinations(dest, possibleDest):
    for pos in possibleDest:
        if distance(dest, pos) < ATDEST:
            return True
    return False