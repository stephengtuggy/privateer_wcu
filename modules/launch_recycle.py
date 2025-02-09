import Vector
import VS
import debug
import dynamic_universe
import faction_ships
import fg_util
import launch
import unit
import vsrandom


def NextPos (un, pos):
    rad=un.rSize ()
    whichcoord = vsrandom.randrange(0,3)
    x = pos[whichcoord]
    pos = list(pos)
    x=x+3.0*rad
    pos[whichcoord]=x
    return tuple(pos)
  
def move_to (un, where):
    un.SetPosition(where)
    #debug.debug("VS.Unit()")
    un.SetTarget (VS.Unit())
    return NextPos (un,where)
  
def whereTo (radius, launch_around):
    if (type(launch_around)==type( (1,2,3))):
        pos=launch_around
    else:
        pos = launch_around.Position ()    
    rsize = ((launch_around.rSize())*5.0)+5.0*radius
    if (rsize > faction_ships.max_radius):
        rsize=faction_ships.max_radius
    return (pos[0]+rsize*vsrandom.randrange(-1,2,2),
            pos[1]+rsize*vsrandom.randrange(-1,2,2),
            pos[2]+rsize*vsrandom.randrange(-1,2,2))
  
def unOrTupleDistance(un,unortuple,significantp):
    if (type(unortuple)==type((1,2,3))):
        return Vector.Mag(Vector.Sub(un.Position(),unortuple))-un.rSize()
    else:
        if (significantp):
            return un.getSignificantDistance(unortuple)
        else:
            return un.getDistance(unortuple)
      
def look_for (fg, faction, numships,myunit, pos, gcd,newship=[None]):
    i=0
    debug.debug("VS.getUnit (%d)" % (i))
    un = VS.getUnit (i)
    while (not un.isNull()):
        i+=1
        debug.debug("VS.getUnit (%d)" % (i))
        un = VS.getUnit (i)
    i-=1 #now our i is on the last value
    while ((i>=0) and (numships>0)):
        debug.debug("VS.getUnit (%d)" % (i))
        un = VS.getUnit (i)
        if (not un.isNull()):
            if (unOrTupleDistance(un,myunit,1)>gcd ):
                fac = un.getFactionName ()
                fgname = un.getFlightgroupName ()
                name = un.getName ()
                if ((fg==fgname) and (fac==faction)):
                    if (numships>0):
                        if (vsrandom.random()<0.75):
                            pos=move_to (un,pos)
                            numships-=1
                            newship[0]=un
                            debug.info("TTYmoving %s to current area" % (name))
                    else:
                        #toast 'im!
                        un.Kill()
                        debug.info("TTYaxing %s" % (name))
        i-=1
    return (numships,pos)
  
def LaunchNext (fg, fac, type, ai, pos, logo,newshp=[None],fgappend=''):
    debug.info("Launch nexting "+str(type))
    combofg=fg+fgappend
    if (fgappend=='Base'):
        combofg=fgappend
    newship = launch.launch (combofg,fac,type,ai,1,1,pos,logo)
    dynamic_universe.TrackLaunchedShip(fg,fac,type,newship)
    rad=newship.rSize ()
#VS.playAnimation ("warp.ani",pos,(3.0*rad))
    newshp[0]=newship
    return NextPos (newship,pos)

def launch_dockable_around_unit (fg,faction,ai,radius,myunit,garbage_collection_distance,logo='',fgappend=''):
    for i in fg_util.LandedShipsInFG(fg,faction):
        if (i[0]=='mule.blank' or i[0]=='mule' or faction_ships.isCapital(i[0])):
            un=launch_types_around (fg,faction,[i],ai,radius,myunit,garbage_collection_distance,logo,fgappend)
            if (un.isDockableUnit()):
                return un
    if (fgappend=='Base'):
        fg=fgappend
    else:
        fg=fg+fgappend
    return launch.launch_wave_around_unit(fg,faction,faction_ships.getRandomCapitol(faction),ai,1,radius,radius*1.5,myunit,logo)

def launch_types_around ( fg, faction, typenumbers, ai, radius, myunit, garbage_collection_distance,logo,fgappend=''):
    pos = whereTo(radius, myunit)
    nr_ships=0
    for t in typenumbers:
        nr_ships+=t[1]
    debug.info("launch_types_around: before"+str(nr_ships))
    retcontainer=[None]
    if (fgappend=='' and nr_ships>1):
        (nr_ships,pos) = look_for (fg,faction,nr_ships-1,myunit,pos,garbage_collection_distance,retcontainer)
        nr_ships+=1
    debug.info("launch_types_around: after "+str(nr_ships)+ str(retcontainer))
    count=0
    ret=retcontainer[0]
    found=0
    for tn in typenumbers:
        num = tn[1]
        if num>nr_ships:
            num=nr_ships
        for i in range(num):
            newship=[None]
            pos = LaunchNext (fg,faction,tn[0], ai, pos,logo,newship,fgappend)
            if (i==0 and found==0):
                ret=newship[0]
                found=1
        nr_ships-=num
        if (nr_ships==0):
            return ret
    return ret
    
  
def launch_wave_around ( fg, faction, ai, nr_ships, capship, radius, myunit, garbage_collection_distance,logo):
    pos = whereTo(radius, myunit)
    debug.info("launch_wave_around: before"+str(nr_ships))
    (nr_ships,pos) = look_for (fg,faction,nr_ships,myunit,pos,garbage_collection_distance)
    debug.info("launch_wave_around: after "+str(nr_ships))
    while (nr_ships>0):
        type=""
        if (capship):
            type = faction_ships.getRandomCapitol(faction)
        else:
            type = faction_ships.getRandomFighter(faction)
        pos = LaunchNext (fg,faction,type, ai, pos,logo)
        nr_ships-=1
     
