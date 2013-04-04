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

import sqlite3
import ast
from datetime import datetime, date
import heatmap
import os, sys, glob
import time
from optparse import OptionParser
import kml_movement
from collections import namedtuple


class VizGen:
    
    def __init__(self, db_name):
        #Connect to zeh db!
        self.conn = sqlite3.connect(db_name)
        
    
    def generate(self):
        self.generate_general_vis()
        self.generate_location_vis()
        self.generate_activity_vis()
        self.generate_battery_vis()
        self.generate_screen_vis()
        self.output_page()
        
        
    def generate_general_vis(self):
        #Data to record
        self.startDate = 0
        self.endDate = 0
        
        #General Info
        c = self.conn.cursor()
        c.execute('select * from data WHERE probe like "edu.mit.media.funf.probe.builtin.%" ORDER BY timestamp ASC LIMIT 1')
        for row in c:
            data = row[4]
            data = data.replace("true", "True")
            data = data.replace("false", "False")
            data_dict = ast.literal_eval(data.rstrip())
            self.startDate = datetime.fromtimestamp(float(data_dict['timestamp']))
            
        c.execute('select * from data WHERE probe like "edu.mit.media.funf.probe.builtin.%" ORDER BY timestamp DESC LIMIT 1')
        for row in c:
            data = row[4]
            data = data.replace("true", "True")
            data = data.replace("false", "False")
            data_dict = ast.literal_eval(data.rstrip())
            self.endDate = datetime.fromtimestamp(float(data_dict['timestamp']))
        
    
    def generate_location_vis(self):
        LOCATION_PROBE = 'edu.mit.media.funf.probe.builtin.LocationProbe'
        LocTuple = namedtuple('LocTuple', ['lat', 'long', 'time'])
        
        location_data = []
        self.movement_location_data = []
        self.locationScans = 0
        self.last_loc_long = 0
        self.last_loc_lat = 0
        
        #Location Data
        c = self.conn.cursor()
        t = (LOCATION_PROBE,)
        c.execute('select * from data where probe = ? ORDER BY timestamp', t)
        i = 0
        last_date = 0
        for row in c:
            i += 1
            data = row[4]
            data = data.replace("true", "True")
            data = data.replace("false", "False")
            data_dict = ast.literal_eval(data.rstrip())
            if int(data_dict["timestamp"]) - last_date >= 60:
                location_data.append([data_dict['mLongitude'], data_dict['mLatitude']])
                last_date = int(data_dict["timestamp"])
            self.movement_location_data.append(LocTuple(data_dict['mLongitude'], data_dict['mLatitude'], datetime.fromtimestamp(float(data_dict["timestamp"]))))
            print self.movement_location_data[-1].time
        
        self.locationScans = i
        if len(location_data) > 0:
            self.last_loc_lat = location_data[-1][1]
            self.last_loc_long = location_data[-1][0]
            
            hm = heatmap.Heatmap()
            #Check if there is data
            if i > 0:
                hm.heatmap(location_data, "classic.png", dotsize=50)
            else:
                hm.heatmap([[0,0]], "classic.png", dotsize=50)
            hm.saveKML("most_visited.kml")
            hm.saveKMZ("most_visited")
            
            #Try movement kml
            kml_movement.main(self.movement_location_data)
        else:
            self.last_loc_lat = "42.36125551"
            self.last_loc_long = "-71.08763113"
        
        print "Done with location"
        
        
    def generate_activity_vis(self):
        ACTIVITY_PROBE = 'edu.mit.media.funf.probe.builtin.ActivityProbe'
        
        activity_list = []
        self.activityScans = 0
        self.activity_html = ""
        
        #Activity Data (oh god)
        c = self.conn.cursor()
        t = (ACTIVITY_PROBE,)
        c.execute('select * from data where probe = ? ORDER BY timestamp', t)
        print "Entering query"
        for row in c:
            print "in query"
            print row
            data = row[4]
            data_dict = ast.literal_eval(data.rstrip())
            
            total_intervals = 3
            active_intervals = 0
            if data_dict['activityLevel'] == "none":
                active_intervals = 0
            elif data_dict['activityLevel'] == "low":
                active_intervals = 1
            elif data_dict['activityLevel'] == "medium":
                active_intervals = 2
            elif data_dict['activityLevel'] == "high":
                active_intervals = 3

            activity_list.append([data_dict['timestamp'], total_intervals, active_intervals])
                
        self.activityScans = len(activity_list)
        
        if self.activityScans > 0:
            activity, wdays=self.calcluate_hour_activity(activity_list)
            self.activity_html = self.format_activity_html(activity, wdays)
        else:
            self.activity_html = "No activity data recorded"
        
        print "Done with activity"
        
        
    def calcluate_hour_activity(self, data):
        """takes a list of lists entry: [timestamp(since epoch) x y z]
        x,y,z being the acceleration vectors, and calculates a relative
        activity score.
        """
        print data
        start=date.fromtimestamp(data[0][0])
        end=date.fromtimestamp(data[-1][0])
        #get the total no. of days recording
        total=end-start;
        total_days = total.days +1;
        max_value = 1
        #weekdays ... Mon = 0 etc.
        wdays =[ ((start.weekday()+i)%7) for i in range(total_days)]
            
        results = [[0 for i in range(24)] for i in range(total_days)] 
        results_count = [[0 for i in range(24)] for i in range(total_days)]
        for i in data:
            total_intervals = i[1]
            active_intervals = i[2]
            mag = float(active_intervals) / float(total_intervals)
            current = date.fromtimestamp(i[0])
            #get the day of the recorded sample
            delta = current -start
    
            t = time.localtime(i[0])
            adding=results[delta.days][t.tm_hour]+mag
            results[delta.days][t.tm_hour]=adding
            results_count[delta.days][t.tm_hour] += 1
            if (max_value <= adding):
                max_value = adding
        
        i = 0; j = 0;
        max_val = 1
        for day_values, day_counts in zip(results, results_count):
            for h_values, h_counts in zip(day_values, day_counts):
                if h_counts != 0:
                    results[j][i] = (h_values / h_counts)
                    if results[j][i] > max_val:
                        max_val = results[j][i]
                i += 1
            j+=1;i=0
            
        i = 0; j =0;
        for day_values, day_counts in zip(results, results_count):
            for h_values, h_counts in zip(day_values, day_counts):
                if h_counts != 0:
                    results[j][i] = (results[j][i] / max_val) * 60.0
                i += 1
            j+=1;i=0
        return results,wdays
    
    Weekdays =['Mon','Tue','Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    W_DAY = "<tbody><tr><th scope=\"row\">{0}</th>"
    FOOT ="</table><div id=\"chart\"></div>"
    
    def format_activity_html(self, results, wdays):
        HEAD ="<table id=\"for-chart\"><tfoot><tr> \
                            <td>&nbsp;</td> \
                            <th>12am</th> \
                            <th>1</th>\
                            <th>2</th>\
                            <th>3</th>\
                            <th>4</th>\
                            <th>5</th>\
                            <th>6</th>\
                            <th>7</th>\
                            <th>8</th>\
                            <th>9</th>\
                            <th>10</th>\
                            <th>11</th>\
                            <th>12pm</th>\
                            <th>1</th>\
                            <th>2</th>\
                            <th>3</th>\
                            <th>4</th>\
                            <th>5</th>\
                            <th>6</th>\
                            <th>7</th>\
                            <th>8</th>\
                            <th>9</th>\
                            <th>10</th>\
                            <th>11</th>\
                        </tr>"
        Weekdays =['Mon','Tue','Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        W_DAY = "<tbody><tr><th scope=\"row\">{0}</th>"
        FOOT ="</table><div id=\"chart\"></div>"
        
        html_str = HEAD;
        d = 0;
        for r_day in results:
            html_str+=W_DAY.format(Weekdays[wdays[d]])
            d += 1;
            activity_l =[("<td>"+"{:2.2f}".format(i)+"</td>") for i in r_day]
            act_str="".join(activity_l)
            act_str =act_str.replace("d>0.00</t","d></t")
            html_str+= act_str
            html_str+= "</tr>"
        html_str +=FOOT
        return html_str
    
    
    def generate_battery_vis(self):
        BATTERY_PROBE = 'edu.mit.media.funf.probe.builtin.BatteryProbe'
        
        battery_data = []
        self.batteryScans = 0
        self.battery_html = ""
        
        temperature_data = []
        self.temperature_html = ""
        
        #Battery Data
        c = self.conn.cursor()
        t = (BATTERY_PROBE,)
        c.execute('select * from data where probe = ? ORDER BY timestamp', t)
        for row in c:
            data = row[4]
            data = data.replace("true", "True")
            data = data.replace("false", "False")
            data_dict = ast.literal_eval(data.rstrip())
            battery_data.append([float(data_dict['timestamp']), data_dict['level']]) #, data_dict['temperature'], data_dict['plugged']
            temperature_data.append([float(data_dict['timestamp']), data_dict['temperature']])
        self.batteryScans = len(battery_data)
        
        self.battery_html = str(battery_data)
        self.battery_html = self.battery_html.replace('[[', "[")
        self.battery_html = self.battery_html.replace(']]', "]")
        
        self.temperature_html = str(temperature_data)
        self.temperature_html = self.temperature_html.replace('[[', "[")
        self.temperature_html = self.temperature_html.replace(']]', "]")
        
        print "Done with battery"
        
        
    def generate_screen_vis(self):
        SCREEN_PROBE = 'edu.mit.media.funf.probe.builtin.ScreenProbe'
        
        screen_data = [] #not presently using
        self.screenScans = 0
        
        #Screen Data
        c = self.conn.cursor()
        t = (SCREEN_PROBE,)
        c.execute('select * from data where probe = ? ORDER BY timestamp', t)
        for row in c:
            data = row[4]
            data = data.replace("true", "True")
            data = data.replace("false", "False")
            data_dict = ast.literal_eval(data.rstrip())
            if data_dict['screenOn'] == True:
                screen_data.append([float(data_dict['timestamp']) - 1, 0])
                screen_data.append([float(data_dict['timestamp']), 1])
            else:
                screen_data.append([float(data_dict['timestamp']) - 1, 1])
                screen_data.append([float(data_dict['timestamp']), 0])
                
            self.screenScans += 1
            
            
        self.screen_html = str(screen_data)
        self.screen_html = self.screen_html.replace('[[', "[")
        self.screen_html = self.screen_html.replace(']]', "]")
            
            
    def initTemplate(self):
        global TemplateHTML
    
        f = open('resources/fitnesstemplate.html', 'r')
        self.TemplateHTML = f.read()
        
        
    def saveReport(self, name, content):
        #Write file
        f = open(name, 'w')
        f.write(content)
        f.close()
        print "Done"
        
        
    def getPageCode(self, valueDict):
        customHTML = self.TemplateHTML
        
        #RegEx input
        customHTML = customHTML.replace('{{ GeneratedDate }}', valueDict['genDate'])
        customHTML = customHTML.replace('{{ StartDate }}', valueDict['startDate'])
        customHTML = customHTML.replace('{{ EndDate }}', valueDict['endDate'])
        customHTML = customHTML.replace('{{ LocationScans }}', valueDict['locationScans'])
        customHTML = customHTML.replace('{{ BatteryScans }}', valueDict['batteryScans'])
        customHTML = customHTML.replace('{{ ActivityScans }}', valueDict['activityScans'])
        customHTML = customHTML.replace('{{ ScreenScans }}', valueDict['screenScans'])
        customHTML = customHTML.replace('{{ TotalScans }}', valueDict['totalScans'])
        customHTML = customHTML.replace('{{ ActivityGraph }}', valueDict['activityGraph'])
        customHTML = customHTML.replace('{{ BatteryData }}', self.battery_html)
        customHTML = customHTML.replace('{{ ScreenData }}', self.screen_html)
        customHTML = customHTML.replace('{{ TemperatureData }}', self.temperature_html)
        customHTML = customHTML.replace('{{ LastLocCords }}', valueDict['lastLocCords'])
        
        return customHTML
    
    
    def output_page(self):
        self.initTemplate()
        
        today = datetime.today()
        
        fordDict = {'genDate': today.strftime("%B %d, %Y %I:%M%p"), #'sleepRanges': self.sleep_ranges,
                    'startDate': self.startDate.strftime("%b %d, %Y"), 'endDate': self.endDate.strftime("%b %d, %Y"),
                    'locationScans': str(self.locationScans), 'batteryScans': str(self.batteryScans), 'activityScans': str(self.activityScans),
                    'screenScans': str(self.screenScans), 'totalScans': str(self.locationScans + self.batteryScans + self.activityScans + (2 * self.screenScans)),
                    'activityGraph': self.activity_html, 'lastLocCords': str(self.last_loc_lat) + "," + str(self.last_loc_long)}
        
        self.saveReport('data_visualization.html', self.getPageCode(fordDict))
        
    
def main():
    usage = "%prog [sqlite_file1.db]"
    description = "Takes one sqlite file and generates example visualizations of data."
    parser = OptionParser(usage="%s\n\n%s" % (usage, description))
    (args) = parser.parse_args()
    path = os.path.abspath(os.path.join(sys.argv[0], os.path.pardir))
    os.chdir(path)
    try:
        viz = VizGen(args[1][0])
        viz.generate()
    except Exception as e:
        for infile in glob.glob( os.path.join(path, '*.db') ):
            print infile
            if infile.count("merged"):
                viz = VizGen(infile)
                viz.generate()
                break
            else:
                viz = VizGen(infile)
                viz.generate()
        
    
if __name__ == "__main__":
    main()