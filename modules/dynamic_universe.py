import Director
import VS
import debug
import dynamic_battle
import dynamic_news
import faction_ships
import fg_util
import generate_dyn_universe
import vsrandom


global dnewsman_
dnewsman_ = dynamic_news.NewsManager()
_ships=[]
player_kill_list=[]

def updatePlayerKillList(playernum,faction):
    fac = VS.GetFactionIndex(faction)
    ret=0
    for i in range (VS.getNumPlayers()-len(player_kill_list)):
        player_kill_list.append([]);
    for i in range(VS.getNumPlayers()):
        numfac=Director.getSaveDataLength(i,"kills")
        for j in range (numfac-len(player_kill_list[i])):
            player_kill_list[i].append(0)
        for j in range (numfac):
            if (i==playernum and j==fac):
                ret = Director.getSaveData(i,"kills",j)-player_kill_list[i][j];
            player_kill_list[i][j]=Director.getSaveData(i,"kills",j)
    return ret

class ShipTracker:
    def __init__ (self,fgname,faction,typ,un):
        self.un=un
        self.fgname=fgname
        self.faction= faction
        self.starsystem = VS.getSystemFile()
        self.type=typ
    def Check(self):
        dead=not self.un
        if (not dead):
            dead = self.un.GetHull()<=0
        if (dead):
            debug.info("Uunit died")
            if (VS.systemInMemory (self.starsystem)):
                if fg_util.RemoveShipFromFG(self.fgname,self.faction,self.type)!=0:
                  if (VS.getPlayerX(0)):
                      debug.info("unit died for real")
                      if (VS.GetRelation(self.faction,VS.getPlayerX(0).getFactionName())>0):
                          dynamic_battle.rescuelist[self.starsystem]=(self.faction,"Shadow",faction_ships.get_enemy_of(self.faction))
                          debug.info("friend in trouble")
                  global dnewsman_
                  numships = updatePlayerKillList(0,self.faction)
                  debug.info("num ships killed: "+numships)
                  if ((numships>0 and VS.getPlayer()) or fg_util.NumShipsInFG(self.fgname,self.faction)==0): #generate news here fg killed IRL
                      varList=[str(Director.getSaveData(0,"stardate",0)),dnewsman_.TYPE_DESTROYED,dnewsman_.STAGE_END,"unknown",self.faction,dnewsman_.SUCCESS_WIN,str(dynamic_battle.getImportanceOfType(self.type)),self.starsystem,dnewsman_.KEYWORD_DEFAULT,"unknown","unknown",self.fgname,self.type]
                      if (numships>0 and VS.getPlayer()):
                          varList=[str(Director.getSaveData(0,"stardate",0)),dnewsman_.TYPE_DESTROYED,dnewsman_.STAGE_END,VS.getPlayer().getFactionName(),self.faction,dnewsman_.SUCCESS_WIN,str(dynamic_battle.getImportanceOfType(self.type)),self.starsystem,dnewsman_.KEYWORD_DEFAULT,VS.getPlayer().getFlightgroupName(),VS.getPlayer().getName(),self.fgname,self.type]
                      dnewsman_.writeDynamicString(varList)
                      debug.info("news about unit dying")
            else:
                fg_util.LandShip(self.fgname,self.faction,self.type)
            return 0
        else:
            sys=self.un.getUnitSystemFile()
            if (len(sys)):
                self.starsystem=sys
        return 1

def TrackLaunchedShip(fgname,fac,typ,un):
    fg_util.LaunchShip(fgname,fac,typ)
    global _ships
    _ships+= [ShipTracker(fgname,fac,typ,un)]

curiter=0

def Execute():
    global curiter, _ships
    if (len(_ships)>curiter):
        if (not _ships[curiter].Check()):
            del (_ships[curiter])
        else:
            curiter+=1
    else:
        curiter=0
