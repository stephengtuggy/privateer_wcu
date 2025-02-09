from go_somewhere_significant import *
from go_to_adjacent_systems import *
import Briefing
import Director
import VS
import debug
import faction_ships
import launch
import quest
import universe
import unit
import vsrandom

# global
escort_num=0


class escort_mission (Director.Mission):
    you=VS.Unit()
    escortee=VS.Unit()
    adjsys=0
    arrived=0
    mplay="all"

    def __init__ (self, factionname, missiondifficulty, our_dist_from_jump, dist_from_jump, distance_from_base, creds, enemy_time, numsysaway, jumps=(), var_to_set='', fgname='', dyntype=''):
        Director.Mission.__init__(self);
        self.you = VS.getPlayer();
        self.role= "ESCORTCAP"
        self.gametime=VS.GetGameTime()
        self.adjsys=go_to_adjacent_systems(self.you, numsysaway,jumps)
        self.var_to_set = var_to_set;
        debug.debug("e")
        self.adjsys.Print("You should start in the system named %s","Then jump to %s","Finally, jump to %s, your final destination","escort mission",1)
        debug.debug("f")
        self.distfrombase=distance_from_base
        debug.debug("g")
        self.faction=factionname
        global escort_num
        escort_num+=1
        #self.escortee = launch.launch_wave_around_unit("Escort"+str(escort_num),
        #                                              self.faction,
        #                                              faction_ships.getRandomFighter("merchant"),
        #                                              "default",
        #                                              1,
        #                                              self.you.rSize(),
        #                                              2.0*self.you.rSize(),
        #                                              self.you,
        #                                              "")
        L=launch.Launch()
        if fgname == "":
            L.fg = "Escort"
            L.fgappend = "_"+str(escort_num)
        else:
            L.fg = fgname
            L.fgappend = ""
            L.faction=self.faction
            if (dyntype==''):
                L.type = faction_ships.getRandomFighter("merchant")
            else:
                L.type = dyntype
                L.forcetype=True
            L.dynfg = ""
            L.ai = "default"
            L.num=1
            L.minradius = 2.0*self.you.rSize()
            L.maxradius = 3.0*self.you.rSize()
            self.escortee=L.launch(self.you)
            self.escortee.upgrade("jump_drive",0,0,0,1)
            self.you.SetTarget(self.escortee)
            debug.debug("h")
            self.escortee.setFlightgroupLeader(self.you)
            debug.debug("dd")
            self.difficulty=missiondifficulty
            self.creds = creds

    def initbriefing(self):
        debug.info("init briefing")

    def loopbriefing(self):
        debug.info("loop briefing")
        Briefing.terminate();

    def endbriefing(self):
        debug.info("ending briefing")

    def Execute (self):
        if (VS.GetGameTime()-self.gametime>10):
            self.escortee.setFgDirective('F')
        if self.you.isNull():
            VS.IOmessage (0,"escort",self.mplay,"#ff0000You were to protect your escort. Mission failed.")
            VS.terminateMission(0)
            return
        self.escortee.setFlightgroupLeader(self.you)
        debug.debug('name: '+self.escortee.getFlightgroupLeader().getName())
        #self.escortee.SetVelocity(self.you.GetVelocity())
        if (self.escortee.isNull()):
            VS.IOmessage (0,"escort",self.mplay,"#ff0000You were to protect your escort. Mission failed.")
            universe.punish(self.you,self.faction,self.difficulty)
            if (self.var_to_set!=''):
                quest.removeQuest (self.you.isPlayerStarship(),self.var_to_set,-1)
            VS.terminateMission(0)
            return   
        if (not self.adjsys.Execute()):
            if (self.arrived):
                self.adjsys.SignificantUnit().setSpeed(0.0)
                self.adjsys.SignificantUnit().SetVelocity((0.0,0.0,0.0))
            return
        if (not self.arrived):
            self.arrived=1
            self.adjsys=go_somewhere_significant (self.escortee,1,self.distfrombase+15*self.escortee.rSize(),self.difficulty<=1,self.faction)
            self.role = self.adjsys.SignificantUnit().getCombatRole()
            self.adjsys.SignificantUnit().setCombatRole("INERT");
            self.adjsys.Print ("You must escort your starship to the %s","defend","docked around the %s", 0)
        else:
            self.you.addCredits(self.creds)
            VS.AdjustRelation(self.you.getFactionName(),self.faction,self.difficulty*.01,1)
            VS.IOmessage (0,"escort",self.mplay,"#00ff00Excellent work! You have completed this mission!")
            self.escortee.setFgDirective('b')
            self.escortee.setFlightgroupLeader(self.escortee)
            self.escortee.performDockingOperations(self.adjsys.SignificantUnit(),0)
            self.adjsys.SignificantUnit().setCombatRole(self.role);
            if (self.var_to_set!=''):
                quest.removeQuest (self.you.isPlayerStarship(),self.var_to_set,1)
            VS.terminateMission(1)

def initrandom (factionname, difficulty, creds, entime, numsysaway, jumps=(), var_to_set='', fgname='', dyntype=''):
    return escort_mission(factionname, difficulty, 20000, vsrandom.randrange(5000,7000), vsrandom.randrange(10,300), creds, entime, numsysaway, jumps, var_to_set, fgname, dyntype)
