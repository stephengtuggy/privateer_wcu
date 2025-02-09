import Director
import VS
import ambush
import debug
import directions_mission
import faction_ships
import launch
import universe

class ambush_scan(ambush.ambush):
    def __init__(self,savevar,systems,delay,faction,numenemies,dyntype='',dynfg='',greetingText=["You have been scanned and contraband has been found in your hold.","You should have dumped it while you had the chance.","Now you die!"], directions=[], destination='',AdjustFaction=True,cargotype="Brilliance",altGreetingText=["Thank you for delivering the cargo to us instead.","We appreciate your candor in this matter."]):
        ambush.ambush.__init__(self,savevar,systems,delay,faction,numenemies,dyntype,dynfg,greetingText,directions,destination,AdjustFaction)
        self.altGreetingText=altGreetingText
        self.cargotype=cargotype
        self.counter=0

    def FriendlyLaunch(self):
        self.havelaunched=1
        L=launch.Launch()
        L.fg="Shadow"

        if(self.dyntype==""):
            self.dyntype=faction_ships.getRandomFighter(self.faction)
        L.type=self.dyntype
        L.dyntype=self.dyntype
        L.num=self.numenemies
        L.faction=self.faction
        L.minradius=3000
        L.maxradius=4000
        try:
            L.minradius*=faction_ships.launch_distance_factor
            L.maxradius*=faction_ships.launch_distance_factor
        except:
            debug.debug("failed to set up minradius and maxradius for faction_ships.launch")
            pass
        you=VS.getPlayerX(self.cp)
        friendly=L.launch(you)
        universe.greet(self.altGreetingText,friendly,you);
        
    def Execute(self):
        ambush.ambush.Execute(self)
        if(self.inescapable):
            you=VS.getPlayerX(self.cp)
            if you.getUnitSystemFile()==self.systems[0]:
                self.timer=VS.GetGameTime();
            if you.GetCargo(self.cargotype).GetQuantity()==0:
                self.inescapable=0
            debug.debug("un=VS.getUnit(%d)" % (self.counter))
            un=VS.getUnit(self.counter)
            if(not un.isNull()):
                if un.getName()==self.cargotype or un.getName()=="Mission_Cargo":
                    self.counter=0
                    debug.debug("un=VS.getUnit(0)")
                    un=VS.getUnit(0)
                    while(not un.isNull()):
                        self.counter+=1
                        debug.debug("un=VS.getUnit(%d)" % (self.counter))
                        un=VS.getUnit(self.counter)
                    while (self.counter>0):
                        self.counter-=1
                        debug.debug("un=VS.getUnit(%d)" % (self.counter))
                        un=VS.getUnit(self.counter)
                        if (un):
                            if un.getName()==self.cargotype or un.getName()=="Mission_Cargo":
                                un.Kill()
                    if not self.havelaunched:
                        self.FriendlyLaunch()
                else:
                    debug.debug(self.cargotype +" not matched with "+un.getName())
                    self.counter+=1
            else:
                self.counter=0
