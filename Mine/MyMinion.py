import sys, pygame, math, numpy, random, time, copy
from pygame.locals import * 

from constants import *
from utils import *
from core import *
from moba import *

############## Constants ##############
MINIONRANGE = 250
ATDEST = 20
DODGERANGE = 250
PROTECTCOUNTER = 150
DODGECOUNTER = 5

VERBOSE = 0 # change to 1 to have comments printed

class MyMinion(Minion):
    
    def __init__(self, position, orientation, world, image = NPC, speed = SPEED, viewangle = 360, hitpoints = HITPOINTS, firerate = FIRERATE, bulletclass = SmallBullet):
        Minion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass)
        self.states = [Idle]
        ### Add your states to self.states (but don't remove Idle)
        ### YOUR CODE GOES BELOW HERE ###
        self.states.extend([ProtectBase, Dodge])
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
        self.agent.changeState(ProtectBase, None, PROTECTCOUNTER)
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

class ProtectBase(State):

    def parseArgs(self, args):
        self.dest = args[0]
        self.counter = args[1]
        self.bestDestinations = None

    def enter(self, oldstate):

        if VERBOSE == 1:

            print "ProtectBase"

        towers = self.agent.world.getTowersForTeam(self.agent.getTeam())
        base = self.agent.world.getBaseForTeam(self.agent.getTeam())

        if self.dest == None or self.counter == 0:

            # self.targetTower = getClosest(towers, self.agent.getLocation())
            # targetLoc = self.targetTower.getLocation()

            self.counter = PROTECTCOUNTER

            targetLoc = base.getLocation()
            possibleDest = self.agent.getPossibleDestinations()
            possibleDest = [d for d in possibleDest if ( distance(d, targetLoc) < MINIONRANGE \
                             and distance(d, targetLoc) > (MINIONRANGE - 100) ) ] 

            rankDestinations = []
            for i, nextPos in enumerate(possibleDest):

                towerWeight = sum([-1.0*0.5*distance(nextPos, t.getLocation()) for t in towers])
                baseWeight = -1.0*0.5*distance(nextPos, base.getLocation()) 

                rankDestinations.append( ( i, towerWeight + baseWeight ) )

            rankDestinations = sorted(rankDestinations, key=lambda x: x[1], reverse = True)

            self.bestDestinations = [ possibleDest[rankDestinations[i][0]] for i in range(5) ]

            self.dest = random.choice(self.bestDestinations)
        
        self.agent.navigateTo(self.dest)
        drawCross(self.agent.world.debug,self.dest, (255, 0, 0), 10)

        # print self.counter
    
    def execute(self, delta = 0):        

        inRangeBullets = bulletsInRange(self.agent)
        enemyAgents = self.agent.world.getEnemyNPCs(self.agent.getTeam())
        enemyAgents = [e for e in enemyAgents if inShootingRange(self.agent, e, MINIONRANGE)]

        # enemyTowers = self.agent.world.getEnemyTowers(self.agent.getTeam())
        # enemyBases = self.agent.world.getEnemyBases(self.agent.getTeam())

        if len(enemyAgents) > 0:
            closestTarget = getClosest(enemyAgents, self.agent.getLocation())
            self.agent.turnToFace(closestTarget.getLocation())
            self.agent.shoot()

        if len(inRangeBullets) > 0:
            bullet = getClosest(inRangeBullets, self.agent.getLocation())
            self.agent.changeState(Dodge, DODGECOUNTER, None) 

        else:
            # if self.dest == None:
            #     self.
            self.agent.changeState(ProtectBase, self.dest, self.counter  - 1) 


class Dodge(State):

    def parseArgs(self, args):
        # self.originalDest = args[0]
        # self.object = args[1]
        self.counter = args[0]
        self.dest = args[1]

    def enter(self, oldstate):

        if VERBOSE == 1:
            print "Dodge"

        base = self.agent.world.getBaseForTeam(self.agent.getTeam())
        if self.counter == None:
            possibleDest = self.agent.getPossibleDestinations()

            if base != None:
                possibleDest = [d for d in possibleDest if \
                ( distance(self.agent.getLocation(), d) < 50 and distance(d, base.getLocation()) < 100 ) ]

            else:
                possibleDest = [d for d in possibleDest if (distance(self.agent.getLocation(), d) < 50)]

            self.dest = random.choice(possibleDest)
            self.agent.navigateTo( self.dest )

    def execute(self, delta = 0):

        if self.counter == 0:

            self.agent.changeState(ProtectBase, self.dest, PROTECTCOUNTER)

        else:
            self.agent.changeState(Dodge, self.counter - 1, self.dest)


class HuntTower(State):

    def parseArgs(self, args):
        self.dest = args[0]
        self.targetTower = args[1]
        self.bestDestinations = None
        self.destCounter = None

    def enter(self, oldstate):

        if VERBOSE == 1:
            print "HuntTower"
        
        enemyTowers = self.agent.world.getEnemyTowers(self.agent.getTeam())
        if self.dest == None and len(enemyTowers) > 0:
            self.targetTower = getClosest(enemyTowers, self.agent.getLocation())
            otherTower = getOtherTower(self.targetTower, enemyTowers)

            targetLoc = self.targetTower.getLocation()
            otherLoc = otherTower.getLocation()
            baseLoc = self.agent.world.getEnemyBases(self.agent.getTeam())[0].getLocation()

            possibleDest = self.agent.getPossibleDestinations()
            possibleDest = [d for d in possibleDest if ( distance(d, targetLoc) < MINIONRANGE \
                             and distance(d, targetLoc) > (MINIONRANGE - 100) ) ] 
            for d in possibleDest:
                drawCross(self.agent.world.debug, d, (0, 255, 0), 5)

            alpha = -1.0 * 0.5 #weight for distance to tower 
            beta = 0.5 #weight for distance to other tower 
            gamma = 0.5

            rankDestinations = []
            for i, nextPos in enumerate(possibleDest):
                rankDestinations.append( (i, alpha * distance(nextPos, targetLoc) + beta * \
                                distance(nextPos, otherLoc) + gamma * distance(nextPos, baseLoc) ) )

            rankDestinations = sorted(rankDestinations, key=lambda x: x[1], reverse = True)
            # print rankDestinations
            self.bestDestinations = [ possibleDest[rankDestinations[i][0]] for i in range(5) ]
            self.dest = self.bestDestinations[0]
            self.destCounter = 0
        
        if atDestination( self.agent.getLocation(), self.dest ):

            if self.destCounter == 5:
                self.destCounter = 0

            self.navigateTo(self.bestDestinations[self.destCounter])

        else:
            self.agent.navigateTo(self.dest)
        
        drawCross(self.agent.world.debug,self.dest, (255, 0, 0), 10)

        # print self.agent.isMoving()
        # if atDestination(self.agent.getLocation(), self.dest):
    
    def execute(self, delta = 0):        

        inRangeBullets = bulletsInRange(self.agent)
        enemyAgents = self.agent.world.getEnemyNPCs(self.agent.getTeam())
        enemyAgents = [e for e in enemyAgents if inShootingRange(self.agent, e, MINIONRANGE)]
        enemyTowers = self.agent.world.getEnemyTowers(self.agent.getTeam())
        enemyBases = self.agent.world.getEnemyBases(self.agent.getTeam())

        if len(enemyTowers) == 0 and len(enemyBases) > 0:
            self.agent.changeState(HuntBase)

        # elif len(inRangeBullets) > 0:
        #     bullet = getClosest(inRangeBullets, self.agent.getLocation())
        #     self.agent.changeState(Dodge, self, None, bullet) 

        elif inShootingRange(self.agent, self.targetTower, MINIONRANGE):
            self.agent.turnToFace(self.targetTower.getLocation())
            self.agent.shoot()

        elif len(enemyAgents) > 0:
            closestTarget = getClosest(enemyAgents, self.agent.getLocation())
            self.agent.turnToFace(closestTarget.getLocation())
            self.agent.shoot()

        else:
            self.agent.changeState(HuntTower, self.dest, self.targetTower) 

class HuntBase(State):

    def parseArgs(self, args):
        return

    def enter(self, oldstate):

        if VERBOSE == 1:
            print "HuntBase"


############## Helpers ##############
def minionDodgeLoc(agent, bullet):
    possibleDest = agent.getPossibleDestinations()
    orientation = bullet.orientation
    # TODO change
    for a in [90, 270]:
        angle = orientation + a
        vector = (math.cos(math.radians(angle)), -math.sin(math.radians(angle)))
        diff = (vector[0]*agent.getRadius()*1.5, vector[1]*agent.getRadius()*1.5)
        newPos = ( agent.getLocation()[0] + diff[0], agent.getLocation()[1] + diff[1] ) 
        if inPossibleDestinations(newPos, possibleDest):
            return newPos
    return None

def getDodgeAngle(agent, bullet):
    possibleDest = agent.getPossibleDestinations()
    orientation = bullet.orientation
    # TODO change
    for a in range(0, 360): #[90, 270]:
        angle = orientation + a
        vector = (math.cos(math.radians(angle)), -math.sin(math.radians(angle)))
        diff = (vector[0]*agent.getRadius()*1.5, vector[1]*agent.getRadius()*1.5)
        newPos = ( agent.getLocation()[0] + diff[0], agent.getLocation()[1] + diff[1] ) 
        if inPossibleDestinations(newPos, possibleDest):
            # print "angle, ", angle
            return angle
    return None

"""
Get the other tower.
"""
def getOtherTower(tower, enemyTowers):
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
        # print bullet.getOwner().getTeam()
        if ( (bullet.getOwner().getTeam() != agent.getTeam()) and ( distance( bullet.getLocation() , agent.getLocation() ) < DODGERANGE ) ):
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
    if ( (target in visible) and (distance(target.getLocation(), agent.getLocation()) < range) ):
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
