import sys, pygame, math, numpy, random, time, copy
from pygame.locals import *

from constants import *
from utils import *
from core import *
from moba import *

import time

############## Constants ##############
HITPOINTSDIFF = 2
HERORANGE = 250
MINIONPERCENT = 0.3
HEROPERCENT = 0.5
BASEPERCENT = 0.8
AREAEFFECTRANGE = 2
RUNRANGE = 250
DODGERANGE = 200
BASERANGE = 1
RUNFROMHERO = 300
RUNCOUNTER = 30
ATDEST = 20
SHUFFLECOUNTER = 150

VERBOSE = 1 # change to 1 to have comments printed
TIMEIT = 0
TIMEIT2 = 0
#######################################
### MyHero

class MyHero(Hero):

    def __init__(self, position, orientation, world, image = AGENT, speed = SPEED, viewangle = 360, hitpoints = HEROHITPOINTS, firerate = FIRERATE, bulletclass = BigBullet, dodgerate = DODGERATE, areaeffectrate = AREAEFFECTRATE, areaeffectdamage = AREAEFFECTDAMAGE):
        Hero.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass, dodgerate, areaeffectrate, areaeffectdamage)
        self.states = [Idle]
        ### Add your states to self.states (but don't remove Idle)
        ### YOUR CODE GOES BELOW HERE ###
        # self.states.append(Run) #TODO
        self.states.extend([HuntEnemyHero, HuntEnemyMinion, TouchBase, Run, Search, HuntEnemyTowers])


        self.worldDim = world.getDimensions()
            

        ### YOUR CODE GOES ABOVE HERE ###

    def start(self):
        Hero.start(self)
        self.changeState(Idle)

############################
### Idle
###
### This is the default state of MyHero. The main purpose of the Idle state is to figure out what state to change to and do that immediately.

class Idle(State):
    
    def enter(self, oldstate):
        if VERBOSE == 1:
            print "entered Idle"
        State.enter(self, oldstate)
        # stop moving
        self.agent.stopMoving()
    
    def execute(self, delta = 0):

        # self.agent.changeState( HuntEnemyMinion )
        self.agent.changeState( HuntEnemyTowers, None, SHUFFLECOUNTER )

        ### YOUR CODE GOES ABOVE HERE ###
        return None

###############################
### YOUR STATE CLASSES GO HERE:

class HuntEnemyTowers(State):

    def parseArgs(self, args):
        self.dest = args[0]
        self.counter = args[1]
        self.bestDestinations = None  
        self.targetTower = None 

    def enter(self, oldstate):

        if VERBOSE == 1:

            print "HuntEnemyTowers"

        towers = self.agent.world.getEnemyTowers(self.agent.getTeam())
        base = self.agent.world.getEnemyBases(self.agent.getTeam())
        enemyHero = getEnemyHero(self.agent)
        # print base
        if len(base) > 0 and len(towers) > 0 and enemyHero != None:

            # base = base[0]
            self.counter = SHUFFLECOUNTER

            self.targetTower = getClosest(towers, self.agent.getLocation())
            targetLoc = self.targetTower.getLocation()
            # targetLoc = base.getLocation()
            possibleDest = self.agent.getPossibleDestinations()
            possibleDest = [d for d in possibleDest if ( distance(d, targetLoc) < HERORANGE \
                             and distance(d, targetLoc) > (HERORANGE - 150) ) ] 

            rankDestinations = []
            for i, nextPos in enumerate(possibleDest):

                towerWeight = sum([0.5*distance(nextPos, t.getLocation()) for t in towers])
                # baseWeight = -1.0*0.5*distance(nextPos, base.getLocation()) 
                baseWeight = sum([0.5*distance(nextPos, t.getLocation()) for t in base])
                heroWeight = 0.5 * distance( nextPos, enemyHero.getLocation() )
                rankDestinations.append( ( i, towerWeight + baseWeight + heroWeight ) )

            rankDestinations = sorted(rankDestinations, key=lambda x: x[1], reverse = True)

            self.bestDestinations = [ possibleDest[rankDestinations[i][0]] for i in range(5) ]

            self.dest = random.choice(self.bestDestinations)
        
            self.agent.navigateTo(self.dest)
            drawCross(self.agent.world.debug,self.dest, (255, 0, 0), 10)

    def execute(self, delta = 0):

        inRangeBullets = bulletsInRange(self.agent)
        enemyAgents = self.agent.world.getEnemyNPCs(self.agent.getTeam())
        enemyAgents = [e for e in enemyAgents if inShootingRange(self.agent, e, HERORANGE)]
        enemyHero = getEnemyHero(self.agent)
        # enemyTowers = self.agent.world.getEnemyTowers(self.agent.getTeam())
        # enemyBases = self.agent.world.getEnemyBases(self.agent.getTeam())

        # dodge a bullet if it's close enough
        if len(inRangeBullets) > 0:
            bullet = inRangeBullets[0]
            angle = getDodgeAngle(self.agent, bullet)
            if angle != None:
                self.agent.dodge(angle)

        if self.agent.getHitpoints() <  MINIONPERCENT*self.agent.getMaxHitpoints():
            self.agent.changeState( TouchBase, None )

        elif (inShootingRange(self.agent, enemyHero, HERORANGE) and ( self.agent.getLevel() - enemyHero.getLevel() ) < HITPOINTSDIFF):
            self.agent.changeState( Run, None, RUNCOUNTER )

        elif inShootingRange(self.agent, self.targetTower, HERORANGE):
            self.agent.turnToFace(self.targetTower.getLocation())
            self.agent.shoot()            

        elif len(enemyAgents) > 0:
            # closestTarget = getClosest(enemyAgents, self.agent.getLocation())
            # self.agent.turnToFace(closestTarget.getLocation())
            # self.agent.shoot()
            if self.agent.canAreaEffect and areaEffectInRange(self.agent, enemyAgents):
                self.agent.areaEffect()
            else:
                target = getClosest( enemyAgents, self.agent.getLocation() )
                if inShootingRange(self.agent, target, HERORANGE):
                    self.agent.turnToFace( target.getLocation() )
                    self.agent.shoot()

        else:
            # if self.dest == None:
            #     self.
            self.agent.changeState(HuntEnemyTowers, self.dest, self.counter  - 1) 

        return

class HuntEnemyHero(State):
    # if hunting hero and hitpoints < 50% then touch base

    # args [ enemyHero ]
    # def parseArgs(self, args):
        # argsList = args[0]
        # self.enemyHero = argsList[0]

    def enter(self, oldstate):

        if VERBOSE == 1:

            print "HuntEnemyHero"

        return None
    
    def execute(self, delta = 0):
        enemyHero = getEnemyHero(self.agent)
        herosList = enemyHerosInShootingRange(self.agent, HERORANGE)
        minionsList = enemyMinionsInShootingRange(self.agent, HERORANGE)
        inRangeBullets = bulletsInRange(self.agent)

        if enemyHero != None and self.agent != None:

            # dodge a bullet if it's close enough
            if len(inRangeBullets) > 0:
                bullet = inRangeBullets[0]
                angle = getDodgeAngle(self.agent, bullet)
                if angle != None:
                    # print "dodge"
                    self.agent.dodge(angle)

            # if agent hitpoints is less than MINIONPERCENT --> TouchBase
            elif self.agent.getHitpoints() <  enemyHero.getHitpoints(): #HEROPERCENT*self.agent.getMaxHitpoints():
                self.agent.changeState( TouchBase, None )
                # self.agent.changeState( Run, None, BASECOUNTER )

            # if agent level is less than the enemy level --> HuntEnemyMinion
            elif ( ( self.agent.getLevel() - enemyHero.getLevel() ) < HITPOINTSDIFF ): 
                self.agent.changeState( HuntEnemyMinion )

            # if enemyHero is visible, shoot
            elif inShootingRange(self.agent, enemyHero, HERORANGE):
                if self.agent.canAreaEffect and areaEffectInRange(self.agent, [enemyHero] + minionsList):
                    self.agent.areaEffect()
                else:
                    target = enemyHero
                    # while inShootingRange(self.agent, target, HERORANGE):
                    self.agent.turnToFace( target.getLocation() )
                    self.agent.shoot()
                self.agent.changeState( HuntEnemyHero )

            # nothing visible or in range --> Search
            else:
                self.agent.changeState( Search, 5 )

        return None

    def exit(self):
        return None

# Heros can gain level-ups by killing enemy agents. A level is gained for each kill the 
# Hero makes (the last agent to damage an opponent before it dies). The Hero gains one extra 
# point of damage per level and maximum hitpoints incresases by one for each level earned.
# change from moving to attack. Stop moving in exit.
# bullet.range
# if isinstance(thing, MOBAAgent) and (thing.getTeam() == None or thing.getTeam() != self.owner.getTeam()):

"""
The goal of the agent when in HuntEnemyMinion state is to shoot as many 
minions as possible while avoiding the enemy hero to sufficiently increase 
its level. The agent will change states to TouchBase if its hitpoints 
drop below 30% or if its level is higher than the enemy hero's level by 
greater than or equal to HITPOINTSDIFF.
"""
class HuntEnemyMinion(State):

    # args [ enemyHero ]
    # def parseArgs(self, args):
    #   # argsList = args[0]
    #   self.world = self.agent.world

    def enter(self, oldstate):

        if VERBOSE == 1:
            print "HuntEnemyMinion"

        return None
 
    def execute(self, delta = 0):

        # self.agent.changeState( HuntEnemyHero )

        enemyHero = getEnemyHero(self.agent)
        minionsList = enemyMinionsInShootingRange(self.agent, HERORANGE)
        inRangeBullets = bulletsInRange(self.agent)

        if enemyHero != None and self.agent != None:

            # dodge a bullet if it's close enough
            # if len(inRangeBullets) > 0:
            #   bullet = inRangeBullets[0]
            #   angle = getDodgeAngle(self.agent, bullet)
            #   if angle:
            #       # print "dodge"
            #       self.agent.dodge(angle)

            # if agent hitpoints is less than MINIONPERCENT --> TouchBase
            if self.agent.getHitpoints() < MINIONPERCENT*self.agent.getMaxHitpoints():
                self.agent.changeState( TouchBase, None )

            # if agent level is greater than the enemy level --> HuntEnemyHero
            elif ( ( self.agent.getLevel() - enemyHero.getLevel() ) >= HITPOINTSDIFF ): 
                self.agent.changeState( HuntEnemyHero )

            # if enemyHero is visible --> Run
            elif inShootingRange(self.agent, enemyHero, RUNFROMHERO):
                self.agent.changeState( Run, None, RUNCOUNTER )

            # if any minion is visible and in shooting range, shoot it
            elif minionsList:
                if self.agent.canAreaEffect and areaEffectInRange(self.agent, minionsList + [enemyHero]):
                    self.agent.areaEffect()
                else:
                    target = getClosest( minionsList, self.agent.getLocation() )
                    if inShootingRange(self.agent, target, HERORANGE):
                        self.agent.turnToFace( target.getLocation() )
                        self.agent.shoot()
                self.agent.changeState( HuntEnemyMinion )

            # if no minions are visible or in range --> Search
            else: 
                # print "6"
                self.agent.changeState( Search, 5 )

        return None

    # def exit(self):
    #   return None

"""
Will move to a destination where a minion is close and in range. If a minion
is close and in range, then will switch to HuntEnemyMinion.
"""
class Search(State):
    # args [  ]
    def parseArgs(self, args):
      # argsList = args[0]
        self.targetCounter = args[0]

    def enter(self, oldstate):
        if TIMEIT == 1:
            self.start_t = time.time()      

        if VERBOSE == 1:
            print "Search"

        # world = self.agent.world
        target = None
        enemyHero = getEnemyHero(self.agent)

        # print "agent level: ", self.agent.getLevel()
        # print "agent health: ", self.agent.getHitpoints()
        # print "enemy level: ", enemyHero.getLevel()
        # print "enemy health: ", enemyHero.getHitpoints()

        # search enemy hero
        if enemyHero != None and self.agent != None:

            # go recover
            if self.agent.getHitpoints() < MINIONPERCENT*self.agent.getMaxHitpoints():

                self.agent.changeState( TouchBase, None )

            elif ( ( self.agent.getLevel() - enemyHero.getLevel() ) >= HITPOINTSDIFF ): 
                
                if VERBOSE == 1:
                    print "Search hero"
                
                target = getEnemyHero(self.agent).getLocation()
            
            # search minion
            else:

                if VERBOSE == 1:
                    print "Search minion"

                allEnemyMinions = getEnemyMinions(self.agent)
                
                if len(allEnemyMinions) > 0:
                    allEnemyMinionScores = []
                    alpha = 0.5 #weight for distance from the minion
                    beta = 0.8 #weight for distance from minion to hero
                    for i, em in enumerate(allEnemyMinions):
                        allEnemyMinionScores.append( (i, alpha*distance(self.agent.getLocation(), em.getLocation()) \
                                                    - beta*distance(em.getLocation(), getEnemyHero(self.agent).getLocation())) )
                        allEnemyMinionScores = sorted(allEnemyMinionScores, key = lambda x: x[1], reverse = True)
                    #closestMinion = getClosest(allEnemyMinions, self.agent.getLocation())
                    #target = getClosestDistances(self.agent.getPossibleDestinations(), closestMinion.getLocation())
                    target = allEnemyMinions[allEnemyMinionScores[0][0]].getLocation()

            self.targetCounter -= 1
            if self.targetCounter == 0 and target != None:
                self.agent.navigateTo( target )
                self.targetCounter = 8

        return None
    
    def execute(self, delta = 0):
        visibleMinions = enemyMinionsInShootingRange(self.agent, HERORANGE)
        enemyHero = getEnemyHero(self.agent)
        inRangeBullets = bulletsInRange(self.agent)
        if enemyHero != None and self.agent != None:

            # hero level > enemy level and enemyHero in shooting range:
            if ( ( self.agent.getLevel() - enemyHero.getLevel() ) >= HITPOINTSDIFF ):
                if inShootingRange( self.agent, enemyHero, HERORANGE ):
                    #self.agent.stopMoving()
                    self.agent.changeState( HuntEnemyHero )
                else:
                    # print "1"
                    self.agent.changeState( Search, self.targetCounter )

            # hero level < enemy level
            else: # self.agent.getLevel() - enemyHero.getLevel() ) < HITPOINTSDIFF 

                # dodge a bullet if it's close enough
                if len(inRangeBullets) > 0:
                    bullet = inRangeBullets[0]
                    angle = getDodgeAngle(self.agent, bullet)
                    if angle != None:
                        self.agent.dodge(angle)

                elif visibleMinions:
                #self.agent.stopMoving()
                    self.agent.changeState( HuntEnemyMinion )
                elif inShootingRange( self.agent, enemyHero, RUNFROMHERO ):
                    self.agent.changeState( Run, None, RUNCOUNTER )
                else:
                    self.agent.changeState( Search, self.targetCounter)

            if TIMEIT:
                print time.time()-self.start_t

        return None

"""
Will move to a destination in opposite direction of the enemyHero.
Takes one argument. If None, then it will re-compute A*.
"""
class Run(State):

    # args [ dest ]
    def parseArgs(self, args):
        # argsList = args[0]
        self.dest = args[0]
        self.runCounter = args[1]
        # print "in parse: ", self.dest
        # self.dest = None # TODO comment out

    def enter(self, oldstate):
        enemyHero = getEnemyHero(self.agent)
        # print "agent ", self.agent.getLocation()
        # print "dest ", self.dest
        if TIMEIT2 == 1:
            self.start_t = time.time()      

        if VERBOSE == 1:
            print "Run"

        if self.dest == None: #or atDestination(self.agent.getLocation(), self.dest ) :
            
            if enemyHero != None:
                self.dest = runDestination(self.agent, enemyHero)
                self.agent.navigateTo(self.dest)

        return None
    
    def execute(self, delta = 0):

        enemyHero = getEnemyHero(self.agent)
        visibleMinions = enemyMinionsInShootingRange(self.agent, HERORANGE)
        inRangeBullets = bulletsInRange(self.agent) 
        minionsList = enemyMinionsInShootingRange(self.agent, HERORANGE)

        if self.dest == None:
            self.agent.changeState( Run, self.dest, self.runCounter )

        # ran away
        # if not inShootingRange(self.agent, enemyHero, HERORANGE) and self.runCounter == 0:
        if (not inShootingRange(self.agent, enemyHero, HERORANGE) and self.runCounter <= 0) or atDestination(self.agent.getLocation(), self.dest):
            # print "stuck here"
            # self.agent.changeState( Search, 5 )
            self.agent.changeState( HuntEnemyTowers, None, SHUFFLECOUNTER )

        # keep running
        else:
            # print "try to dodge"
            # dodge a bullet if it's close enough
            # print inRangeBullets
            if len(inRangeBullets) > 0:
                bullet = inRangeBullets[0]
                angle = getDodgeAngle(self.agent, bullet)
                # print angle
                if angle != None:
                    print "dodge"
                    self.agent.dodge(angle)

            if enemyHero!= None and self.agent!= None:
                if self.agent.canAreaEffect and areaEffectInRange(self.agent, [enemyHero,] + minionsList):
                    self.agent.areaEffect()

                else:
                    target = getClosest( [enemyHero,] + minionsList, self.agent.getLocation() )
                    if target != None:
                        if inShootingRange(self.agent, target, HERORANGE):
                            self.agent.turnToFace( target.getLocation() )
                            self.agent.shoot()

            # print "in else: ", self.dest
            # print "minus 1"
            self.agent.changeState( Run, self.dest, self.runCounter - 1)

            if TIMEIT2:
                print time.time()-self.start_t

        return None

"""
When in TouchBase state, the agent's goal is to reach its home base and heal.
Once it has been healed, it will change to HuntEnemyHero if its level is higher 
than the enemy hero's level by greater than or equal to HITPOINTSDIFF. Otherwise
it will change to HuntEnemyMinion.
Takes one argument. If None, then it will re-compute A*.
"""
class TouchBase(State):
    
    # args [ dest ]
    def parseArgs(self, args):
        self.dest = args[0]

    # navigate to the closest base
    def enter(self, oldstate):

        if VERBOSE == 1:
            print "TouchBase"
    
        # print "enter"
        # print "touch dest ", self.dest
        if self.dest == None:
            # print "re-compute"
            world = self.agent.world
            base = world.getBaseForTeam(self.agent.getTeam())
            if (base != None):
                self.dest = base.getLocation()
                self.agent.navigateTo(self.dest)
            else:
                print "There is no base!"

        return None
    
    # once the agent is healed it will hunt the hero if its level is higher than 
    # the enemy or it will hunt minions to increase its level
    def execute(self, delta = 0):

        enemyHero = getEnemyHero(self.agent)
        inRangeBullets = bulletsInRange(self.agent)     

        if self.agent.getHitpoints() == self.agent.getMaxHitpoints(): #agent is healed
            # self.agent.changeState( HuntEnemyMinion )
            self.agent.changeState( HuntEnemyTowers, None, SHUFFLECOUNTER )

        else:
            # dodge a bullet if it's close enough
            if len(inRangeBullets) > 0:
                bullet = inRangeBullets[0]
                angle = getDodgeAngle(self.agent, bullet)
                if angle:
                    self.agent.dodge(angle)

            self.agent.changeState( TouchBase, self.dest,  )

        return None

    # def exit(self):
    #   return None

############## Helpers ##############
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
    myOrientation = agent.orientation
    if abs(myOrientation - (90 + orientation)) < abs(myOrientation - (270 + orientation)):
        angle = 90 + orientation
    else:
        angle = 270 + orientation

    vector = (math.cos(math.radians(angle)), -math.sin(math.radians(angle)))
    diff = (vector[0]*agent.getRadius()*1.5, vector[1]*agent.getRadius()*1.5)
    newPos = ( agent.getLocation()[0] + diff[0], agent.getLocation()[1] + diff[1] ) 
        
    if inPossibleDestinations(newPos, possibleDest):
        # print "angle, ", angle
        return angle

    return None

def inPossibleDestinations(dest, possibleDest):
    for pos in possibleDest:
        if distance(dest, pos) < 20:
            return True
    return False


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
Returns true if any item in the targets is within range of the agent's
area effect.
"""
def areaEffectInRange(agent, targets):
    for t in targets:
        if distance(agent.getLocation(), t.getLocation()) < (agent.getRadius()*AREAEFFECTRANGE)+(t.getRadius()):
            return True
    return False


"""
Will find a possible destination facing away from the enemy hero given the 
agent.
"""
def runDestination(agent, enemyHero):
    possibleDest = agent.getPossibleDestinations()
    agentLoc = agent.getLocation()
    enemyLoc = enemyHero.getLocation()
    # filter to be at least a certain range away from the c
    #possibleDest = [d for d in possibleDest if distance(d, enemyLoc) > RUNRANGE] 
    enemyBase = agent.world.getBaseForTeam(enemyHero.getTeam()) #edge case, in base
    base = agent.world.getBaseForTeam(agent.getTeam()) #edge case, in base

    alpha = 0.4 #agent weight
    beta = 1.0  #enemy weight
    gamma = 0.15 #enemyBase weight

    rankDestinations = []
    for i, d in enumerate(possibleDest):
        #print "destination ", d
        #print "distance ", -1.0*alpha*distance(d, agentLoc) + beta*distance(d, enemyLoc)
        rankDestinations.append( (i,  -1.0*alpha*distance(d, agentLoc) + beta*distance(d, enemyLoc) ) )

    rankDestinations = sorted(rankDestinations, key=lambda x: x[1], reverse = True)
    #print possibleDest
    return possibleDest[rankDestinations[0][0]]


def atDestination(currPos, dest):
    if ( distance(currPos, dest) < ATDEST ):
        # print "it's true"
        return True
    return False
