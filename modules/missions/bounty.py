import Briefing
import Director
import Vector
import VS
import debug
import faction_ships
import launch
import quest
import unit
import universe
import vsrandom
from go_somewhere_significant import go_somewhere_significant
from go_to_adjacent_systems import go_to_adjacent_systems


class bounty (Director.Mission):
    def SetVar (self,val):
        if (self.var_to_set!=''):
            quest.removeQuest (self.you.isPlayerStarship(),self.var_to_set,val)
    def __init__ (self, minnumsystemsaway, maxnumsystemsaway, creds, run_away, shipdifficulty, tempfaction, jumps=(), var_to_set='', namefg='', dyntype="", displayLocation=1, greetingText=['It appears we have something in common, privateer.','My name may be on your list, but now your name is on mine.'], dockable_unit=False):
        Director.Mission.__init__ (self)
        self.firsttime=VS.GetGameTime()
        self.newship=dyntype
        self.namefg=namefg
        self.mplay="all"
        self.var_to_set = var_to_set
        self.istarget=0
        self.obj=0
        self.curiter=0
        self.arrived=0
        self.faction = tempfaction
        self.difficulty = shipdifficulty
        self.runaway=run_away
        self.greetingText=greetingText
        self.cred=creds
        mysys=VS.getSystemFile()
        sysfile = VS.getSystemFile()
        self.you=VS.getPlayer()
        #debug.debug("VS.Unit()")
        self.enemy=VS.Unit()
        self.adjsys=go_to_adjacent_systems (self.you,vsrandom.randrange(minnumsystemsaway,maxnumsystemsaway+1),jumps)
        self.dockable_unit=dockable_unit
        self.mplay=universe.getMessagePlayer(self.you)
        self.displayLocation=displayLocation
        if (self.you):
            VS.IOmessage (0,"bounty mission",self.mplay,"[Computer] Bounty Mission Objective: (%.2f Credits)" % self.cred)
            self.adjsys.Print("From %s system","Procede to %s","Search for target at %s, your final destination","bounty mission",1)
            VS.IOmessage (1,"bounty mission",self.mplay,"Target is a %s unit." % (self.faction))
        else:
            default.info("aboritng bounty constructor...")
            VS.terminateMission (0)

    def AdjLocation(self):
        debug.info("ADJUSTING LOCATION")
        self.enemy.SetPosition(Vector.Add(self.enemy.LocalPosition(),Vector.Scale(self.enemy.GetVelocity(),-40))) #eta 20 sec
    def Win (self,un,terminate):
        self.SetVar(1)
        VS.IOmessage (0,"bounty mission",self.mplay,"[Computer] #00ff00Bounty Mission Accomplished!")
        un.addCredits(self.cred)
        if (terminate):
            debug.info("you win bounty mission!")
            VS.terminateMission(1)

    def Lose (self,terminate):
        VS.IOmessage(0,"bounty mission",self.mplay,"[Computer] #ff0000Bounty Mission Failed.")
        self.SetVar(-1)
        if (terminate):
            debug.info("you lose bounty mission")
            VS.terminateMission(0)
    def LaunchedEnemies(self,significant):
        pass
    def Execute (self):
        isSig=0
        if (self.you.isNull()):
            self.Lose (1)
            return
        if (self.arrived==2):
            if (not self.runaway):
                if (not self.istarget):
                    if (self.enemy):
                        #debug.debug("curun=VS.getUnit(self.curiter)")
                        curun=VS.getUnit(self.curiter)
                        self.curiter+=1
                        if (curun==self.enemy):
                            self.enemy.SetTarget(self.you)
                        elif (curun.isNull()):
                            self.curiter=0
            else:
                if (VS.GetGameTime()>self.firsttime+2.5 and self.enemy):
                    self.firsttime+=1000000
                    self.AdjLocation()
            if (self.enemy.isNull()):
                self.Win(self.you,1)
                return
        elif (self.arrived==1):
            significant=self.adjsys.SignificantUnit()
            if (significant.isNull ()):
                debug.info("significant is null")
                VS.terminateMission(0)
                return
            else:
                if (self.you.getSignificantDistance(significant)<self.adjsys.distfrombase):
                    if (self.newship==""):
                        self.newship=faction_ships.getRandomFighter(self.faction)
                    #self.enemy=launch.launch_wave_around_unit("Shadow",self.faction,self.newship,"default",1+self.difficulty,3000.0,4000.0,significant)
                    L = launch.Launch()
                    if self.namefg == "":
                        L.fg = "Shadow"
                    else:
                        L.fg = self.namefg
                    L.dynfg=""
                    L.type = self.newship
                    L.faction = self.faction
                    L.ai = "default"
                    L.num=1+self.difficulty
                    L.minradius=3000.0
                    L.maxradius = 4000.0
                    try:
                        L.minradius*=faction_ships.launch_distance_factor
                        L.maxradius*=faction_ships.launch_distance_factor
                    except:
                        pass
                    self.enemy=L.launch(significant)
                    self.you.SetTarget(self.enemy)
                    universe.greet(self.greetingText,self.enemy,self.you)
                    self.obj=VS.addObjective("Destroy the %s ship." % (self.enemy.getName ()))
                    if (self.enemy):
                        if (self.runaway):
                            self.enemy.SetTarget(significant) #CHANGE TO SetTarget ==>NOT setTarget<==
                            self.enemy.ActivateJumpDrive(0)
                            self.firsttime=VS.GetGameTime()
                            #self.enemy.SetPosAndCumPos(Vector.Add(self.you.Position(),Vector.Vector(0,0,self.you.rSize()*1.2)))
                        self.LaunchedEnemies(significant)
                        self.arrived=2
                    else:
                        debug.info("enemy is null")
                        VS.terminateMission(0)
                        return
        else:
            if (self.adjsys.Execute()):
                self.arrived=1
                if (self.newship==""):
                    self.newship=faction_ships.getRandomFighter(self.faction)
                self.adjsys=go_somewhere_significant(self.you,self.dockable_unit,10000.0,0,'','',self.displayLocation)
                if not self.displayLocation:
                    VS.addObjective("Search/Destroy "+self.faction.capitalize()+" mark");
                localdestination=self.adjsys.SignificantUnit().getName()
                tmpfg=self.namefg
                if len(tmpfg)==0:
                    tmpfg="Shadow"
                VS.IOmessage (3,"bounty mission",self.mplay,"Hunt the %s unit in the %s flightgroup in this system." % (self.newship,tmpfg))
                if (self.runaway): #ADD OTHER JUMPING IF STATEMENT CODE HERE
                    VS.IOmessage (4,"bounty mission",self.mplay,"Target is fleeing to the jump point!")
                    VS.IOmessage (5,"bounty mission",self.mplay,"Target Destination appears to be %s" % (localdestination))
                elif (self.displayLocation):
                    VS.IOmessage (4,"bounty mission",self.mplay,"Scanners detect bounty target!")
                    VS.IOmessage (5,"bounty mission",self.mplay,"Coordinates appear near %s" % (localdestination))
                else:
                    debug.info("Location is "+str(self.displayLocation))
                    VS.IOmessage (4,"bounty mission",self.mplay,"[Computer] Mission description indicates bounty target may be in this system.")
    def initbriefing(self):
        debug.info("init bounty briefing")

    def loopbriefing(self):
        debug.info("loop bounty briefing")
        Briefing.terminate()

    def endbriefing(self):
        debug.info("ending bounty briefing")

def initrandom (minns, maxns, credsmin, credsmax, run_away, minshipdifficulty, maxshipdifficulty,jumps=(),var_to_set=''):
    you=VS.getPlayer()
    tempfaction='unknown'
    if (you):
        name = you.getFactionName ()
        i=vsrandom.randrange(0,len(faction_ships.factionsInNormalMissions))
        tempfaction=faction_ships.factionsInNormalMissions[i]
        i=0
        while ((name==tempfaction or name=="unknown") and i<10):
            i=vsrandom.randrange(0,len(faction_ships.factionsInNormalMissions))
            tempfaction=faction_ships.factionsInNormalMissions[i]
            i+=1
        sd = vsrandom.random()*(maxshipdifficulty-minshipdifficulty)+minshipdifficulty
        return bounty (minns,maxns,(1.0+(sd*0.5))*(vsrandom.random ()*(credsmax-credsmin)+credsmin),run_away,sd,tempfaction,jumps,var_to_set)
    else:
        debug.info("aborting bounty initrandom")
        VS.terminateMission(0)

