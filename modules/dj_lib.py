import VS
import debug
import vsrandom

BATTLELIST=0
PEACELIST=1
PANICLIST=2
VICTORYLIST=3
LOSSLIST=4
HOSTILE_AUTODIST=1600
HOSTILE_NEWLAUNCH_DISTANCE=6000

peacelist={"aera":VS.musicAddList('aera.m3u'),
            "confed":VS.musicAddList('terran.m3u'),
            "iso":VS.musicAddList('iso.m3u'),
            "AWACS":VS.musicAddList('AWACS_peace.m3u'),
            None:PEACELIST
            }

battlelist={"aera":VS.musicAddList('aerabattle.m3u'),
            "confed":VS.musicAddList('terranbattle.m3u'),
            "iso":VS.musicAddList('isobattle.m3u'),
            "AWACS":VS.musicAddList('AWACS.m3u'),
            None:BATTLELIST
            }

paniclist={None:PANICLIST,
            "AWACS":VS.musicAddList('AWACS.m3u')}

asteroidmisic=VS.musicAddList('asteroids.m3u')

def LookupTable(list,faction):
    if faction in list:
        if (list[faction]!=-1):
            return list[faction]
        else:
            return list[None]
    else:
        return list[None]

situation=PEACELIST

def mpl(list,newsituation,forcechange):
    global situation
    debug.info("SITUATION IS "+str( situation)+" force change "+str(forcechange) + " bool "+ str(forcechange or newsituation!=situation))
    if (forcechange or newsituation!=situation):
        debug.info("SITUATION IS RESET TO "+str( newsituation))
        situation=newsituation
        VS.musicPlayList(list)

def PlayMusik(forcechange=1, hostile_dist=0):
    un = VS.getPlayer()
    if (not un):
        mpl (PEACELIST,PEACELIST,forcechange)
        debug.info("PlayMusik: Peace (not un)")
    else:
        perfect = 1
        #debug.debug("before 'uni = VS.getUnitList()'")
        uni = VS.getUnitList()
        #debug.debug("after 'uni = VS.getUnitList()'")
        unlist = []
        asteroid = 0
        while (not uni.isDone()):
            #debug.debug("before 'target = next(uni)'")
            target = next(uni)
            #debug.debug("after 'target = next(uni)'")
            if not target.isNull():
                #debug.debug("inside 'if not target.isNull():'")
                ftmp = 2 * target.getRelation(un)
                nam = target.getName().lower()
                if un.getSignificantDistance(target) <= 2 * target.rSize() and ('afield' == nam[:6] or 'asteroid'== nam[:8]):
                    asteroid = 1
                hdis = HOSTILE_AUTODIST
                if (hostile_dist != 0):
                    hdis = hostile_dist
                if (target.GetTarget() == un or (ftmp < 0 and un.getDistance(target) < hdis)):
                    unlist.append(target.getFactionName())
                    perfect = 0
        if (perfect):
            if asteroid and asteroidmisic != -1 and vsrandom.random() < .7:
                mpl(asteroidmisic, PEACELIST, forcechange)
                return
            sys = VS.getSystemFile()
            fact = VS.GetGalaxyFaction(sys)
            if vsrandom.random() < .5:
                fact = None
            mpl(LookupTable(peacelist, fact), PEACELIST, forcechange)
            debug.info("PlayMusik: Peace")
        else:
            ftmp = (un.FShieldData() + 2 * un.GetHullPercent() + un.RShieldData() - 2.8) * 2
            fact = None
            if len(unlist) and vsrandom.random() < .5:
                fact = unlist[vsrandom.randrange(0, len(unlist))]
            debug.info("faction: %s" % (fact))
            if (ftmp < -.5):
                mpl(LookupTable(paniclist, fact), BATTLELIST, forcechange)
                debug.info("PlayMusik: Panic")
            else:
                mpl(LookupTable(battlelist, fact), BATTLELIST, forcechange)
                debug.info("PlayMusik: Battle")
