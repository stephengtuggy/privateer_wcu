
""" This module provides different mission types. """
import Director
import VS
import debug
import difficulty
import dynamic_battle
import dynamic_news
import dynamic_universe
import faction_ships
import fg_util
import news
import trading
import universe
import vsrandom


global dnewsman_
dnewsman_ = dynamic_news.NewsManager()
baseship=None
plr=0
basefac='neutral'
syscreds=750

def formatShip(ship):
    where=ship.find(".blank")
    if (where!=-1):
        ship=ship[0:where]
    return ship.capitalize()

def formatCargoCategory(ship):
    where=ship.rfind("/")
    if (where!=-1):
        ship=ship[where+1:]
    return ship.capitalize()

#Credit to Peter Trethewey, master of python and all things nefarious
def getSystemsKAwayNoFaction( start, k ):
    set = [start]  #set of systems that have been visited
    pathset = [[start]]  #parallel data structure to set, but with paths
    pathtor = [[start]]  #parallel data structure to raw return systems with path
    r = [start]  #raw data structure containing systems n away where n<=k
    for n in range(0,k):
        set.extend(r)
        pathset.extend(pathtor)
        r=[]
        pathtor=[]
        for iind in range(len(set)):
            i = set[iind]
            l = universe.getAdjacentSystemList(i)
            for jind in range(len(l)):
                j=l[jind]
                if not (j in set or j in r):
                    r.append(j)
                    pathtor.append(pathset[iind]+[j])
    return pathtor

def getSystemsNAway (start,k,preferredfaction):
    l = getSystemsKAwayNoFaction(start,k)
    if (preferredfaction==None):
        return l
    lbak=l
    if (preferredfaction==''):
        preferredfaction=VS.GetGalaxyFaction(start)
    i=0
    while i <len(l):
        if (VS.GetRelation(preferredfaction,VS.GetGalaxyFaction(l[i][-1]))<0):
            del l[i]
            i-=1
        i+=1
    if (len(l)):
        return l
    return lbak

def GetRandomCompanyName():
    bnl=[]
    debug.debug('reading company names')
    filename = '../universe/companies.txt'
    try:
        f = open (filename,'r')
        bnl = f.readlines()
        f.close()
    except:
        return ''
    for i in range(len(bnl)):
        bnl[i]=bnl[i].rstrip()
    idx = vsrandom.randint(0,len(bnl)-1)
    return bnl[idx]

def GetRandomCargoBrief():
    bnl=[]
    brief=''
    debug.debug('generating cargo briefing')
    filename = '../universe/cargo_brief.txt'
    try:
        f = open (filename,'r')
        bnl = f.readlines()
        f.close()
    except:
        return ''
    for i in range(len(bnl)):
        bnl[i]=bnl[i].rstrip()
    idx = vsrandom.randint(0,len(bnl)-1)
    brief = bnl[idx]
    return brief

def getCargoName(category):
    l=category.split('/')
    if len(l)>1:
        cargo = l[len(l)-1]+' '+l[0]
    else:
        cargo = category
    cargo = cargo.replace('_',' ')
    return cargo

def getMissionDifficulty ():
    tmp=difficulty.getPlayerUnboundDifficulty(VS.getCurrentPlayer())
    if (tmp>1.5):
        tmp=1.5
    return tmp

def getPriceModifier(isUncapped):
    if (not difficulty.usingDifficulty()):
        return 1.0
    if (isUncapped):
        return getMissionDifficulty()/.5+.9
    return VS.GetDifficulty()/.5+.9

def howMuchHarder(makeharder):
    if  (makeharder==0):
        return 0
    udiff = getMissionDifficulty()
    if (udiff<=1):
        return 0
    return int(udiff*2)-1

def processSystem(sys):
    k= sys.split('/')
    if (len(k)>1):
        k=k[1]
    else:
        k=k[0]
    return k

insysMissionNumber=0
def checkInsysNum():
    global insysMissionNumber
    if insysMissionNumber:
        insysMissionNumber=0
        return True
    return False

totalMissionNumber=0
def checkMissionNum():
    global totalMissionNumber
    if totalMissionNumber:
        totalMissionNumber=0
        return True
    return False

def checkCreatedMission():
    if (checkMissionNum()+checkInsysNum()>0):
        return True
    return False

def isFixerString(s):
    k=str(s)
    if (len(k)<2):
        return 0
    if (k[1]=='F'):
        return 1
    if (k[1]=='G'):
        return 2
    return 0

def writemissionname(name,path,isfixer):
    if (isfixer==0):
        if path[-1]==VS.getSystemFile():
            name="In_System_"+name
            global insysMissionNumber
            insysMissionNumber+=1
        else:
            global totalMissionNumber
            totalMissionNumber+=1
    Director.pushSaveString(plr, "mission_names", name)

def writedescription(name):
    Director.pushSaveString(plr, "mission_descriptions", name.replace("_"," "))

def writemissionsavegame (name):
    Director.pushSaveString(plr, "mission_scripts", name)

def eraseExtras():
    len=Director.getSaveStringLength(plr, "mission_scripts")
    if (len!=Director.getSaveStringLength(plr, "mission_names") or len!=Director.getSaveStringLength(plr, "mission_descriptions")):
        debug.debug("Warning: Number of mission descs., names and scripts are unequal.\n")
    if len>0:
        for i in range(len-1,-1,-1):
            Director.eraseSaveString(plr, "mission_scripts", i)
            Director.eraseSaveString(plr, "mission_names", i)
            Director.eraseSaveString(plr, "mission_descriptions", i)

fixerpct=0.02
guildpct=0.4
def restoreFixerPct():
    global fixerpct
    global guildpct
    fixerpct=.0625
    guildpct=.4

def mungeFixerPct():
    global fixerpct
    global guildpct
    fixerpct=.0375
    guildpct=1

def generateCleansweepMission(path,numplanets,enemy,
        baseprice=800.0,
        pricescale=6.0,
        jumpscale=1.2,
        sweepmod=4.0,
        capshipmod=4.0,
        forceattackmod=0.25
        ):
    fighterprob=vsrandom.random()*.75+.25;
    capshipprob=0.0
    if (vsrandom.random()<.2):
        capshipprob=vsrandom.random()*.25;
    forceattack=vsrandom.randrange(0,2)
    cleansweep=vsrandom.randrange(0,2)
    minships=maxships=vsrandom.randrange(1,4)
    creds = ( pricescale * (
            1+
            cleansweep*sweepmod+
            capshipprob*capshipmod+
            forceattack*forceattackmod
        ) * baseprice * minships * fighterprob
        + jumpscale * syscreds * len(path) )
    creds*=getPriceModifier(False)
    addstr=""
    isFixer=vsrandom.random()
    if isFixer<fixerpct:
        creds*=2
        addstr+="#F#bases/fixers/confed.spr#Talk to the Confed Officer#Thank you.  Your help makes space a safer place.#\n"
    elif isFixer<guildpct:
        creds*=1.5
        if (cleansweep):
            addstr+="#G#Bounty#\n"
        else:
            addstr+="#G#Patrol#\n"
    missiontype="patrol_enemies"
    additional=""
    additionalinstructions=""
    patrolorclean="Patrol"
    dist=1000
    if (cleansweep):
        dist=1500
        additional=",1"
        patrolorclean="Clean_Sweep"
        missiontype="cleansweep"
        additionalinstructions+="  Eliminate all such forces encountered to receive payment."
    if (capshipprob):
        additionalinstructions+="  Capital ships are possibly in the area."
    writemissionsavegame (addstr+"import %s\ntemp=%s.%s(0, %d, %d, %d, %s,'',%d,%d,%f,%f,'%s',%d%s)\ntemp=0\n"%(missiontype,missiontype,missiontype,numplanets, dist, creds, str(path),minships,maxships,fighterprob,capshipprob,enemy,forceattack,additional))
    writedescription("Authorities would like a detailed scan of the %s system. We require %d nav locations be visited on the scanning route.  The pay for this mission is %d. Encounters with %s forces likely.%s"%(processSystem(path[-1]),numplanets,creds,enemy,additionalinstructions))
    ispoint="s"
    if numplanets==1:
        ispoint=""
    writemissionname("%s/%s_%d_Point%s_in_%s"%(patrolorclean,patrolorclean,numplanets,ispoint, processSystem(path[-1])),path,isFixerString(addstr))

def generatePatrolMission (path, numplanets,
        planetprice=100.0,
        baseprice=800.0,
        jumpscale=3.0
        ):
    dist=400
    creds = numplanets*planetprice + jumpscale*baseprice + syscreds*len(path)
    creds*=getPriceModifier(False)
    addstr=""
    isFixer=vsrandom.random()
    if isFixer<fixerpct:
        creds*=2
        addstr+="#F#bases/fixers/confed.spr#Talk to the Confed Officer#Thank you.  Your help makes space a safer place.#\n"
    elif isFixer<guildpct:
        creds*=1.5
        addstr+="#G#Patrol#\n"
    writemissionsavegame (addstr+"import patrol\ntemp=patrol.patrol(0, %d, %d, %d, %s)\ntemp=0\n"%(numplanets, dist, creds, str(path)))
    writedescription("Insystem authorities would like a detailed scan of the %s system. We require %d nav locations be visited on the scanning route.  The pay for this mission is %d."%(processSystem(path[-1]),numplanets,creds))
    ispoint="s"
    if numplanets==1:
        ispoint=""
    writemissionname("Patrol/Patrol_%d_Point%s_in_%s"%(numplanets,ispoint, processSystem(path[-1])),path,isFixerString(addstr))

def isNotWorthy(fac):
    return VS.GetRelation(fac,VS.getPlayer().getFactionName())<0

def generateEscortLocal(path,fg,fac,
        waveprice=3500.0
        ):
    if (isNotWorthy(fac)):
        return
    typ = fg_util.RandomShipIn(fg,fac)
    if typ in faction_ships.unescortable:
        return
    enfac = faction_ships.get_enemy_of(fac)
    diff=vsrandom.randrange(1,4)
    waves=vsrandom.randrange(0,5-diff)
    incoming=vsrandom.randrange(0,2)
    enfg =fg_util.AllFGsInSystem(enfac,path[-1])
    creds=waveprice*diff*(1+waves);
    if (len(enfg)):
      enfg=enfg[vsrandom.randrange(0,len(enfg))]
    else:
      enfg=''
    isFixer=vsrandom.random()
    addstr=""
    if isFixer<fixerpct:
        creds*=2
        addstr+="#F#bases/fixers/merchant.spr#Talk to the Merchant#Thank you. I trust that you will safely escort my colleague to the destination.#\n"
    elif isFixer<guildpct:
        creds*=1.5
        addstr+="#G#Escort#\n"
    additionalinfo="to the jump point"
    if (incoming):
        additionalinfo="from the jump point to a nearby base"
    writemissionsavegame(addstr+"import escort_local\ntemp=escort_local.escort_local('%s',0,%d,%d,500,%d,%d,'%s',(),'','%s','','%s','%s')"%(enfac,diff,waves,creds,incoming,fac,enfg,fg,typ))
    writedescription("Escort %s is required for the %s type %s starship from the %s flightgroup in this system. Attacks from the %s faction are likely. You will be paid %d credits if the starship survives in this starsystem until it reaches its destination."%(additionalinfo,formatShip(typ),fac,fg,enfac,int(creds)))
    writemissionname("Escort/Escort_%s_%s"%(fac,fg),[path[-1]],isFixerString(addstr))

def generateEscortMission (path,fg,fac,
        baseprice=500.0,
        jumpscale=1.2
        ):
    ###
    if (isNotWorthy(fac)):
        return
    typ = fg_util.RandomShipIn(fg,fac)
    if typ in faction_ships.unescortable:
        return
    diff=vsrandom.randrange(0,6)
    creds=baseprice*diff+jumpscale*syscreds*len(path)
    creds*=getPriceModifier(False)
    addstr=""
    isFixer=vsrandom.random()
    if isFixer<fixerpct:
        creds*=2
        addstr+="#F#bases/fixers/merchant.spr#Talk to the Merchant#Thank you. I entrust that you will safely guide my collegue until you reach the destination.#\n"
    elif isFixer<guildpct:
        creds*=1.5
        addstr+="#G#Escort#\n"
    writemissionsavegame (addstr+"import escort_mission\ntemp=escort_mission.initrandom('%s', %d, %g, 0, 0, %s, '','%s','%s')\ntemp=0\n"%(fac, diff, float(creds), str(path),fg,typ))
    writedescription("The %s %s in the %s flightgroup requres an escort to %s. The reward for a successful escort is %d credits."%(fac,formatShip(typ),fg, processSystem(path[-1]),creds))
    writemissionname("Escort/Escort_%s_%s_to_%s"%(fac,fg,processSystem(path[-1])),path,isFixerString(addstr))

def changecat(category):
    l=category.split('/')
    if len(l)>1:
        return l[-1]+'_'+l[0]
    else:
        return category

def pathWarning(path,isFixer):
    global dnewsman_
    message = str()
    factions = list()
    if isFixer:
        message+="\nPrecautions taken to ensure the success of this mission should be taken at your expense."
    else:
        for system in path:
            sysfac = VS.GetGalaxyFaction(system)
            if sysfac not in factions:
                factions.append(sysfac)
        message+="\n\nYou are responsible for the success of this mission.  Precautions taken to ensure this outcome will be taken at your expense.  With that in mind, I will advise you that you will be travalling through systems dominated by the "
        if len(factions) == 1:
            message+=dnewsman_.data.getFactionData(factions[0],'full')[0]+"."
        else:
            message+="following factions: "
            jj=0
            for fac in factions:
                jj+=1
                message+=dnewsman_.data.getFactionData(fac,'full')[0]
                if jj<len(factions)-1:
                    message+=", "
                elif jj<len(factions):
                    message+=" and "
    return message

def adjustQuantityDifficulty(max):
   return 3+int((max-3)*VS.GetDifficulty())

def isHabitable (system):
    planetlist=VS.GetGalaxyProperty(system,"planets")
    if (len(planetlist)==0):
        return False
    planets=planetlist.split(' ')
    for planet in planets:
        if planet=="i" or planet=="a" or planet=="am" or planet=="u" or planet=="com" or planet=="bd" or planet=="s" or planet=="o" or planet=="at" or planet=="bs" or planet=="bdm" or planet=="bsm" or planet=="f" or planet=="fm" or planet=="t":
            return True
    debug.debug(str(planets)+ " Not in Habitable List")
    return False

def generateCargoMission (path, numcargos,category, fac,
        cargoprice=250.0,
        baseprice=500.0,
        contrabandprice=5000.0,
        starshipprice=20000.0
        ):
    #if (isNotWorthy(fac)):
    #    return
    launchcap=(vsrandom.random()>=.97)
    if (not launchcap) and not isHabitable(path[-1]):
        return
    diff=vsrandom.randrange(0,adjustQuantityDifficulty(6))
    creds = (
        cargoprice*numcargos +
        baseprice*diff +
        syscreds*len(path) +
        contrabandprice*(category[:10]=="Contraband") +
        starshipprice*(category[:9]=="starships")
    )
    addstr=""
    creds*=getPriceModifier(False)
    isFixer=vsrandom.random()
    if isFixer<fixerpct:
        creds*=2
        addstr+="#F#bases/fixers/merchant.spr#Talk to the Merchant#Thank you. I entrust you will make the delivery successfully.#\n"
    elif isFixer<guildpct:
        creds*=1.5
        addstr+="#G#Cargo#\n"
    writemissionsavegame (addstr+"import cargo_mission\ntemp=cargo_mission.cargo_mission('%s', 0, %d, %d, %g, %d, 0, '%s', %s, '')\ntemp=0\n"%(fac, numcargos, diff, creds, launchcap, category, str(path)))
    if (category==''):
        category='generic'
    randCompany = GetRandomCompanyName()
    if (randCompany==''):
        strStart = "We need to deliver some "
    else:
          strStart = randCompany+" seeks delivery of "
    brief = GetRandomCargoBrief()
    if brief:  # a comparison to an empty string returns False
        composedBrief = brief.replace('$CL',randCompany)
        composedBrief = composedBrief.replace('$CG',formatCargoCategory(category))
        composedBrief = composedBrief.replace(' $DB','')
        composedBrief = composedBrief.replace('$DS',processSystem(path[-1]))
        composedBrief = composedBrief.replace('$PY',str(int(creds)))
        writedescription(composedBrief)
    else:
        writedescription(strStart+"%s cargo to the %s system. The mission is worth %d credits to us.  You will deliver it to a base owned by the %s.%s"%(formatCargoCategory(category), processSystem(path[-1]),creds,fac,pathWarning(path,isFixer<guildpct)))
    writemissionname("Cargo/Deliver_%s_to_%s"%(changecat(category),processSystem(path[-1])),path,isFixerString(addstr))

def generateRescueMission(path,rescuelist):
    makemissionharder=vsrandom.randrange(0,2)
    numships = vsrandom.randrange(1,adjustQuantityDifficulty(6))+howMuchHarder(makemissionharder)
    creds = (numships+len(path))*vsrandom.randrange(1041,1640)
    creds*=getPriceModifier(makemissionharder!=0)
    if (creds>20000):
        creds=21000
    writemissionsavegame("import rescue\nntemp=rescue.rescue(%d,0,'%s',%d,'%s','%s',%s)\nntemp=0"%(creds,rescuelist[0],numships,rescuelist[2],rescuelist[1],str(path)))
    writedescription("SOS! This is an ejected %s pilot under attack by at least %d %s craft. I request immediate assistance to the %s system and will offer %d credits for a safe return to the local planet where I may recover."%(rescuelist[0],numships,rescuelist[2],processSystem(path[-1]),creds))
    writemissionname("Rescue/Rescue_%s_from_%s_ships"%(rescuelist[0],rescuelist[2]),path,0)

def generateBountyMission (path,fg,fac,
        baseprice=1200.0,
        runawayprice=1000.0,
        diffprice=450.0,
        capscale=4.0
        ):
    typ = fg_util.RandomShipIn(fg,fac)
    cap = faction_ships.isCapital(typ)
    makemissionharder=vsrandom.randrange(0,2)
    diff=vsrandom.randrange(0,adjustQuantityDifficulty(7))+howMuchHarder(makemissionharder)
    runaway=(vsrandom.random()>=.75)
    creds = (
        baseprice +
        runawayprice*runaway +
        diffprice*diff +
        syscreds*len(path)
    )
    if (cap):
        creds *= capscale
    finalprice=creds+syscreds*len(path)
    finalprice*=getPriceModifier(False)
    addstr=""
    isFixer=vsrandom.random()
    if isFixer<fixerpct:
        finalprice*=2
        addstr+="#F#bases/fixers/hunter.spr#Talk with the Bounty Hunter#We will pay you on mission completion.  And as far as anyone knows -- we never met."
        if (runaway):
            addstr += '#Also-- we have information that the target may be informed about your attack and may be ready to run. Be quick!'
        addstr+="#\n"
    elif isFixer<guildpct:
        creds*=1.5
        addstr+="#G#Bounty#\n"
    writemissionsavegame(addstr+"import bounty\ntemp=bounty.bounty(0, 0, %g, %d, %d, '%s', %s, '', '%s','%s')\ntemp=0\n"%(finalprice, runaway, diff, fac, str(path), fg,typ))
    diffstr = ""
    if (diff>0):
        diffstr="  The ship in question is thought to have %d starships for protection."%diff
    writedescription("A %s starship in the %s flightgroup has been harassing operations in the %s system. Reward for the termination of said ship is %d credits.%s"%(formatShip(typ),fg, processSystem(path[-1]), finalprice,diffstr))
    if (cap):
        writemissionname ("Bounty/on_%s_Capital_Vessel_in_%s"%(fac,processSystem(path[-1])),path,isFixerString(addstr))
    else:
        writemissionname ("Bounty/on_%s_starship_in_%s"%(fac,processSystem(path[-1])),path,isFixerString(addstr))

def generateDefendMission (path,defendfg,defendfac, attackfg,attackfac,
        baseprice=1200.0
        ):
    if (isNotWorthy(defendfac)):
        return
    #defendtyp = fg_util.RandomShipIn(defendfg,defendfac)
    attacktyp = fg_util.RandomShipIn(attackfg,attackfac)
    isbase=fg_util.BaseFGInSystemName(path[-1])==defendfg
    creds=baseprice
    minq = 1
    maxq = adjustQuantityDifficulty(5)
    makemissionharder=vsrandom.randrange(0,2)
    quantity = vsrandom.randrange(minq,maxq)+howMuchHarder(makemissionharder)
    reallydefend = "1"
    if (vsrandom.randrange(0,4)==0):
        reallydefend="0"
    addstr=""
    creds=creds*quantity+syscreds*len(path)
    creds*=getPriceModifier(makemissionharder)
    isFixer=vsrandom.random()
    if isFixer<fixerpct:
        creds*=2
        addstr+="#F#bases/fixers/confed.spr#Talk to the Confed Officer#Thank you. Your defense will help confed in the long run.  We appreciate the support of the bounty hunting community.#\n"
    elif isFixer<guildpct:
        creds*=1.5
        addstr+="#G#Defend#\n"
    writemissionsavegame(addstr+"import defend\ntemp=defend.defend('%s', %d, %d, 8000.0, 100000.0, %g, %s, %d, '%s', %s, '%s', '%s', '%s', '%s')\ntemp=0\n"%
                         (attackfac, 0, quantity, creds, reallydefend, isbase, defendfac, str(path), '',attackfg, attacktyp,defendfg))
    iscapitol=""
    if isbase:
        iscapitol="capital "
    writedescription("A %s assault wing named %s has jumped in and is moving for an attack on one of our %sassets in the %s system.\nYour task is to eradicate them before they eliminate our starship.\nIntelligence shows that they have %d starships of type %s. Your reward is %d credits."%(attackfac, attackfg, iscapitol, processSystem(path[-1]),quantity, formatShip(attacktyp),creds))
    writemissionname("Defend/Defend_%s_from_%s"%(defendfac, attackfac),path,isFixerString(addstr))

def generateWingmanMission(fg, faction,
        baseprice=10000.0,
        shipprice=15000.0
        ):
    numships=vsrandom.randrange(1,4)
    creds=baseprice+shipprice*numships
    writemissionsavegame("import wingman\newmission = wingman.wingman (%f, '%s', %d, 0)\newmission=0"%(creds, faction, numships))
    s="A pilot"
    EorA="a"
    are="is"
    if numships > 1:
        s=str(numships)+" pilots"
        EorA="e"
        are="are"
    writedescription(s+" in the %s faction %s willing to help you out and fight with you as long as you pay %d credits."%(faction, are, creds))
    writemissionname("Wingmen/Hire_%d_%s_Wingm%sn"%(numships,faction,EorA),[VS.getSystemFile()],0)

def GetFactionToDefend(thisfaction, fac, cursys):
    m = fg_util.FGsInSystem ("merchant",cursys)
    nummerchant=len(m)
    m+=fg_util.FGsInSystem (thisfaction,cursys)
    numthisfac=len(m)
    m+=fg_util.FGsInSystem (fac,cursys)
    return (m,nummerchant,numthisfac)

def contractMissionsFor(fac,baseship,minsysaway,maxsysaway):
    global totalMissionNumber
    global insysMissionNumber
    totalMissionNumber=0
    insysMissionNumber=0
    facnum=faction_ships.factionToInt(fac)
    enemies = list(faction_ships.enemies[facnum])
    script=''
    cursystem = VS.getSystemFile()
    thisfaction = VS.GetGalaxyFaction (cursystem)
    preferredfaction=None
    if (VS.GetRelation (fac,thisfaction)>=0):
        preferredfaction=thisfaction  #try to stay in this territory
    l=[]
    num_wingmen=2
    num_rescue=2
    num_defend=1
    num_idefend=2
    num_bounty=1
    num_ibounty=1
    num_patrol=1
    num_ipatrol=1
    num_escort=1
    num_iescort=1
    mincount=2
    for i in range (minsysaway,maxsysaway+1):
        for j in getSystemsNAway(cursystem,i,preferredfaction):
            if (i<2 and num_rescue>0):
                if j[-1] in dynamic_battle.rescuelist:
                    generateRescueMission(j,dynamic_battle.rescuelist[j[-1]])
                    if checkCreatedMission():
                        num_rescue-=1
#            if (0 and i==0):
#                generateRescueMission(j,("confed","Shadow","pirates"))
            l = dynamic_battle.BattlesInSystem(j[-1])
            nodefend=1
            for k in l:
                if (VS.GetRelation(fac,k[1][1])>=0):
                    if ((j[-1]==VS.getSystemFile() and num_idefend<=0) or (j[-1]!=VS.getSystemFile() and num_defend<=0)):
                        mungeFixerPct()
                        debug.debug("Munged")
                    else:
                        nodefend=0
                    generateDefendMission(j,k[1][0],k[1][1],k[0][0],k[0][1])
                    restoreFixerPct()
                    if checkInsysNum():
                        num_idefend-=1
                    if checkMissionNum():
                        num_defend-=1
                    debug.debug("Generated defendX with insys at: "+str(num_idefend)+" and outsys at "+str (num_defend))
            (m,nummerchant,numthisfac)=GetFactionToDefend(thisfaction, fac, j[-1])

            if preferredfaction:
                for kk in faction_ships.enemies[faction_ships.factiondict[thisfaction]]:
                    k=faction_ships.intToFaction(kk)
                    for mm in fg_util.FGsInSystem(k,j[-1]):
                        if (i==0 or vsrandom.randrange(0,4)==0):#fixme betterthan 4
                            if nodefend and len(m) and vsrandom.random()<.4:
                                if 1:#for i in range(vsrandom.randrange(1,3)):
                                    insys=(j[-1]==VS.getSystemFile())
                                    if (insys and num_idefend<=0):
                                        mungeFixerPct()
                                    elif (num_defend<=0 and not insys):
                                        mungeFixerPct()
                                    rnd=vsrandom.randrange(0,len(m))
                                    def_fg=m[rnd]
                                    def_fac = "merchant"
                                    if rnd>=nummerchant:
                                        def_fac= thisfaction
                                    if rnd>=numthisfac:
                                        def_fac = fac
                                    generateDefendMission(j,def_fg,def_fac,mm,k)
                                    restoreFixerPct()
                                    if checkInsysNum():
                                        num_idefend-=1
                                    if checkMissionNum():
                                        num_defend-=1
                                    debug.debug("Generated defendY with insys at: "+str(num_idefend)+" and outsys at "+str (num_defend))
                                nodefend=0
                            elif ((i==0 or vsrandom.random()<.5)):
                                if ((j[-1]==VS.getSystemFile() and num_ibounty<=0) or (j[-1]!=VS.getSystemFile() and num_bounty<=0)):
                                   mungeFixerPct()
                                generateBountyMission(j,mm,k)
                                restoreFixerPct()
                                if checkInsysNum():
                                    debug.debug(" decrementing INSYS bounty to "+str(num_ibounty))
                                    num_ibounty-=1
                                if checkMissionNum():
                                    debug.debug(" decrementing bounty to "+str(num_bounty))
                                    num_bounty-=1
            #
            mincount=-2
            if i==0:
                mincount=1
            for k in range(vsrandom.randrange(mincount,4)): ###FIXME: choose a better number than 4.
                if k<0:
                    k=0
                rnd=vsrandom.random()
                if (rnd<.15):    # 15% - nothing
                    pass
                if (rnd<.5 or i==0):    # 35% - Patrol Mission
                    if ((j[-1]==VS.getSystemFile() and num_ipatrol<=0) or (j[-1]!=VS.getSystemFile() and num_patrol<=0)):
                        mungeFixerPct()
                    if (vsrandom.randrange(0,2) or j[-1] in faction_ships.fortress_systems):
                        generatePatrolMission(j,vsrandom.randrange(4,10))
                    else:
                        generateCleansweepMission(j,vsrandom.randrange(4,10),faction_ships.get_enemy_of(fac))
                    restoreFixerPct()
                    if checkInsysNum():
                        num_ipatrol-=1
                    if checkMissionNum():
                        num_patrol-=1
                else:   # 50% - Cargo mission
                    numcargos=vsrandom.randrange(1,25)
                    playership=VS.getPlayer().getName()
                    try:
                        hold=int(VS.LookupUnitStat(playership,"privateer","Hold_Volume"))
                    except:
                        hold=10;
                    if hold<10:
                        hold=10;
                    if hold > 32000:
                        hold = 32000
                    numcargos=vsrandom.randrange(hold//5, hold//2)
                    if numcargos < 20:
                        numcargos=vsrandom.randrange(hold//2, hold)
                    category=''
                    if (rnd>.87 and fac!='confed' and fac != "ISO" and fac!="militia" and fac!="homeland-security" and fac!="kilrathi" and fac!="merchant"):
                        category='Contraband'
                    else:
                        for myiter in range (100):
                            carg=VS.getRandCargo(numcargos,category)
                            category=carg.GetCategory()
                            if (category[:9] != 'Fragments' and category[:10]!='Contraband' and category.find('upgrades')!=0 and (category.find('starships')!=0 or rnd>.999)):
                                break
                            if (myiter!=99):
                                category=''
                        if baseship:
                            faction=fac
                            name=baseship.getName()
                            if baseship.isPlanet():
                                faction="planets"
                                name=baseship.getFullname()
                            debug.info("TRADING")
                            debug.debug("getFullname(): %s, getName(): %s, faction: %s" % (baseship.getFullname(), baseship.getName(), faction))
                            exports=trading.getNoStarshipExports(name,faction,20)
                            debug.debug("exports:\n%s" % (debug.pp(exports)))
                            if (category.find("assengers")==-1 and len(exports)):
                                category=exports[vsrandom.randrange(0,len(exports))][0]
                    #debug.debug("CATEGORY OK "+category)
                    generateCargoMission(j,numcargos,category,fac)
                numescort = vsrandom.randrange(0,2)
                if (numescort>len(m)):
                    numescort=len(m)
                count=0
                for k in m:
                    if (i==0):
                        if vsrandom.random()<.92:
                            count+=1
                            continue
                    elif (vsrandom.random()<.97):
                        count+=1
                        continue
                    f = "merchant"
                    if count>=nummerchant:
                        f= thisfaction
                    if count>=numthisfac:
                        f = fac
                    if (vsrandom.random()<.25):
                        if (num_wingmen>0):
                            generateWingmanMission(k,f)
                            num_wingmen-=1
                    elif (i==0):
                        if (vsrandom.random()<.25):
                            if num_iescort<=0:
                                mungeFixerPct()
                            generateEscortLocal(j,k,f)
                            restoreFixerPct()
                            if checkCreatedMission():
                                num_iescort-=1
                    else:
                        if num_escort<=0:
                            mungeFixerPct()
                        generateEscortMission(j,k,f)
                        restoreFixerPct()
                        if checkCreatedMission():
                            num_escort-=1
                    count+=1

def CreateMissions(minsys=0,maxsys=4):
    eraseExtras()
    global plr,basefac,baseship
    plrun=VS.getPlayer()
    plr=plrun.isPlayerStarship()
    debug.debug("VS.getUnitList()")
    i = VS.getUnitList()
    un = i.current()
    while(not i.isDone() and not un.isDocked(plrun)):
        un = next(i)  # iterate until the docked player unit is found
    if (not un.isNull()):
        baseship=un
        basefac=un.getFactionName()
    if (basefac=='neutral'):
        basefac=VS.GetGalaxyFaction(VS.getSystemFile())
    contractMissionsFor(basefac,baseship,minsys,maxsys)
    news.processNews(plr)
