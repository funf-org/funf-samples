#!/usr/bin/env python
#
# Acknowledgments: Alan Gardner and Cody Sumter
# Contact: funf@media.mit.edu
#
# You can redistribute this and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
# 
# This is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public
# License. If not, see <http://www.gnu.org/licenses/>.
# 

'''
Created on Jul 5, 2011

@author: nadav
'''

import os,sys
from datetime import date, datetime, timedelta
from collections import namedtuple

import simplekml
import heatmap


time_fmt = "%Y-%m-%dT%H:%MZ%z"
LocTuple = namedtuple('LocTuple', ['lat', 'long', 'time'])#, verbose=True)
COLORS = ['ff0000ff',  # Red
          'ffee82ee', #violet
          'ff800000', #navy
          'ff00ff7f', #chartreuse
          'ffd3d3d3', #lightgrey 
          'ff00d7ff', #gold   
          'ff008080', #olive
          'ffffffe0', #lightcyan
          'ff7280fa', # salmon
          'ff00a5ff', #orange
          #'ff2a2aa5', #brown                        
          ]



def get_bbc_data(name, data):
    phone_dict = {}
    phone_dict[name] = data
       
    return phone_dict

def make_color_paths(l_dict):
    kml = simplekml.Kml()
    person_count = 1 # how many phones to do
    c=0
    for tname, loc_list in l_dict.iteritems():
        cfolder = kml.newfolder(name = "heatmaps_%s" %(tname,))
        t_path = []
        print "doing person %s, color: %s" % (c, COLORS[c])
        print loc_list
        for i in range(len(loc_list)):
            
            loc = loc_list[i]
            stime= loc.time.strftime(time_fmt) 
            etime = (loc.time + timedelta(minutes = 720)).strftime(time_fmt) 
            pt = cfolder.newpoint(name="", coords=[[loc.lat, loc.long]])            
            #pt.timestamp.when =stime
            pt.timespan.begin = stime
            pt.timespan.end = etime      
            pt.iconstyle.icon = "white_man.png"# "man_walk_sml.png"
            pt.iconstyle.colormode = "normal"
            pt.iconstyle.color = COLORS[c]#'ff0000ff'  # Red
            pt.iconstyle.scale = 0.25       
            
            if i>0:
#               pt.timespan.begin = loc.time
#                pt.timespan.end = loc_list
                ln = cfolder.newlinestring(name="", #description="A pathway in Kirstenbosch",
                                       coords=[[loc_list[i-1].lat, loc_list[i-1].long], [loc.lat, loc.long]])
                ln.timespan.begin = stime  
                ln.timespan.end = etime
                ln.linestyle.colormode = "normal"
                ln.linestyle.color =  COLORS[c] #'ff0000ff'  # Red
                ln.linestyle.width = 2.0                                        
        c +=1
        if c==person_count:
            break;    
        
    kml.save("movement_path.kml")

    
    
    
    
def make_kml(l_dict):
    kml = simplekml.Kml()

    for tname, loc_list in l_dict.iteritems():
        t_path = []
        for i in range(len(loc_list)):
            loc = loc_list[i]
            stime= loc.time.strftime(time_fmt) 
            pt = kml.newpoint(name="", coords=[[loc.lat, loc.long]])            
            pt.timestamp.when =stime            
            pt.iconstyle.icon = "blue_man.png"# "man_walk_sml.png"
        #    pt.iconstyle.colormode = "random"
        #    pt.iconstyle.color = 'ff0000ff'  # Red
            pt.iconstyle.scale = 0.5        
            
            if i>0:
#               pt.timespan.begin = loc.time
#                pt.timespan.end = loc_list
                ln = kml.newlinestring(name="", #description="A pathway in Kirstenbosch",
                                       coords=[[loc_list[i-1].lat, loc_list[i-1].long], [loc.lat, loc.long]])
                ln.timespan.begin = stime                                            
        break;
    kml.save("test_name_me.kml")

    
        
def _ranges(points):
        """ walks the list of points and finds the 
        max/min x & y values in the set """
        minX = points[0][0]; minY = points[0][1]
        maxX = minX; maxY = minY
        for x,y in points:
            minX = min(x, minX)
            minY = min(y, minY)
            maxX = max(x, maxX)
            maxY = max(y, maxY)        
        return ((minX, minY), (maxX, maxY))
    
def in_boundary(coord, minXY, maxXY):
    if (coord[0] >= minXY[0]) and (coord[0]<=maxXY[0])\
     and (coord[1] >= minXY[1]) and (coord[1]<=maxXY[1]):
        return True    
    return False    
 
def make_multi_heatmap_kml(l_dict, window = None):
    HEATMAP_DAYS = 3 #how many days to include in the heatmap.       
    BOUND1 = [(-71.12826944444444,42.37585), ( -71.0441388888889, 42.33949444444445,)] # boston/cambridge
    BOUND2 = [(-71.10965555555556,42.35016944444445), (-71.07928333333334,42.36591111111111)] # MIT area
    BOUND3 = [(-71.23165,42.42990277777778),(70.94180833333333,42.27036944444444)]
    curr_bound = BOUND1    
    minXY, maxXY =  _ranges(curr_bound)
    
    kml = simplekml.Kml()

    person_count = 3 # how many phones to do
    for tname, loc_list in l_dict.iteritems():
        cfolder = kml.newfolder(name = "heatmaps_%s" %(tname,))

        daylist = []
        pts = []
        cdate = loc_list[0].time.date()
        for i in range(len(loc_list)):             
            loc = loc_list[i]
            
            if loc.time.date() == cdate:
                pts.append(loc)    
            else:
                daylist.append(pts)
                cdate = loc.time.date()
                print cdate
                pts = []
                #print daylist
        
        #print len(daylist)
        for i in range(len(daylist)-HEATMAP_DAYS+1):
            stime = daylist[i][0].time.date()
            etime = daylist[i+HEATMAP_DAYS-1][0].time.date()          
            print "Generating heatmap: " + "%s_%s_%s"%(tname,str(stime),str(etime))

            pts = []            
            for k in range(HEATMAP_DAYS):
                for loc in daylist[i+k]:                    
                    if in_boundary((loc.lat,loc.long), minXY, maxXY):                             
                        pts.append((loc.lat, loc.long))
            
            hm = heatmap.Heatmap()
            hm.heatmap(pts, "%s_%s_%s.png"%(tname,str(stime),str(etime)), boundary = curr_bound)
            #hm.saveKML("10_ppl_5_days.kml")
            overlay_dict = hm.exportToSimpleKML()
            
            heatol = cfolder.newgroundoverlay(name = "%s_%s_%s"%(tname,str(stime),str(etime)))
            heatol.icon = overlay_dict["icon"]
            heatol.latlonbox.east = overlay_dict["east"]
            heatol.latlonbox.west = overlay_dict["west"]
            heatol.latlonbox.north = overlay_dict["north"]
            heatol.latlonbox.south = overlay_dict["south"]
            heatol.latlonbox.rotation = 0
            heatol.timespan.begin = stime.strftime(time_fmt)
            heatol.timespan.end = (stime + timedelta(days=1)).strftime(time_fmt)
            #heatol.timespan.end = etime.strftime(time_fmt)
                    
        person_count -=1
        if person_count==0:
            break;            
            
    
#    kml.newpoint(name="Kirstenbosch", coords=[(18.432314,-33.988862)])
#    lin = kml.newlinestring(name="Pathway", description="A pathway in Kirstenbosch", 
#                            coords=[(18.43312,-33.98924), (18.43224,-33.98914), (18.43144,-33.98911), (18.43095,-33.98904)])
#    line_points = [[-134.713527, 34.435267000000003, 0],
#                     [-133.726201, 36.646867, 0],
#                     [-132.383655, 35.598272999999999, 0],
#                     [-132.48034200000001, 36.876308999999999, 0],
#                     [-131.489846, 36.565426000000002, 0]]
#    
#    lin2 = kml.newlinestring(name="Another One", description="A pathway for testing", 
#                            coords=line_points)
#    
#    
#    
#    
#    pol = kml.newpolygon(name="Atrium Garden",
#                         outerboundaryis=[(18.43348,-33.98985), (18.43387,-33.99004), (18.43410,-33.98972),\
#                                          (18.43371,-33.98952), (18.43348,-33.98985)],
#                         innerboundaryis=[(18.43360,-33.98982), (18.43386,-33.98995), (18.43401,-33.98974),\
#                                          (18.43376,-33.98962), (18.43360,-33.98982)])
    kml.save("heatmap_movement.kml")

def make_heatmap(l_dict):    
    pts = []
    c=0    
    for tname, loc_list in l_dict.iteritems():
        for i in range(len(loc_list)):
            loc = loc_list[i]
            pts.append([loc.lat, loc.long])
        c +=1
        if c==10:
            break;
        #break;

    hm = heatmap.Heatmap()
    hm.heatmap(pts, "classic.png")
    hm.saveKML("10_ppl_5_days.kml")


# main entry
def main(loc_data):
    
    location_dict = get_bbc_data("animated", loc_data)
    print location_dict.keys()
#    make_kml(location_dict)
#    make_heatmap(location_dict)
#    make_multi_heatmap_kml(location_dict)
    make_color_paths(location_dict)
    print "Done!"


if __name__ == "__main__":
    main()
    
    