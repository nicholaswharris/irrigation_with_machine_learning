import sys, time, webbrowser, os.path, os
import RPi.GPIO as GPIO
import numpy as np
from flask import Flask, render_template, request, session
import jyserver.Flask as jsf
from numpy import float32
from plant_ML import weather, Gardener
from datetime import datetime, timedelta
from plant_ML.Gardener import SensorStream, WaterPump
import subprocess
import logging
from waitress import serve
import flask_login

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
UPLOAD_FOLDER = './static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(24)
log = logging.getLogger('werkzeug')
log.disabled = True
needsUpdate = False

# First API Call
last_update = datetime.now()
api_data = weather.hourlyForecast()
if api_data:
    last_update = datetime.now()

# Stores weather alerts
alert = [None, None]
if 'alerts' in api_data:
    alert[0] = api_data['alerts'][0]['description']
    alert[1] = api_data['alerts'][0]['event']
    
# Create log files with headers
# If files don't exist, next log is first log
first_log = False
if os.path.exists('logs/moistureLog.csv') is False:
    log = open("logs/moistureLog.csv", "a")
    log.write("Date, Time, AvgSoilMoisture, Sensor1, Sensor2, Sensor3\n")
    log.close()

if os.path.exists('logs/waterLog.csv') is False:
    first_log = True
    log = open("logs/waterLog.csv", "a")
    log.write("Date, Time, ChanceRain, AvgMoist, Action, Confidence, ResultingMoisture, Note\n")
    log.close()

if os.path.exists('logs/actionLog.csv') is False:
    log = open("logs/actionLog.csv", "a")
    log.write("Date, Time, ChanceRain, AvgMoist, Action, Confidence, Note\n")
    log.close()
    
if os.path.exists('logs/trainingLog.csv') is False:
    log = open("logs/trainingLog.csv", "a")
    log.write("state[], PredOutput[], statePrime[]\n")
    log.close()

# Sensor variables
sensor1 = 0
sensor2 = 0
sensor3 = 0

# Irrigation functions
sensors = SensorStream()
pump = WaterPump()

# Prediction variables
avgMoisture = 0
cor = 0
last_state = None
best_action = None
confidence = None
list_act = None

# Plants are watered at 10AM
# Soil moisture is recorded at 10PM same day
checked_today = False
watered_today = False

# ChanceRain, AvgSoilMoist, Sensor1, Sensor2, Sensor3, Action, Confidence, Time
lastDecision = [0, 0, 0, 0, 0, 0, '100%', '1/1/2000 10:00AM']
nextDecision = [None, None, None, None, None, None, None, None]
override = False
emergency = False

# Track last state with log file
if os.path.exists('logs/lastDecision.csv') is True:
    log = open('logs/lastDecision.csv', "r")
    state = log.readline()
    state = state.split(',')
    for i in range(8):
        lastDecision[i] = state[i]
    log.close()

starttime = datetime.now()
nextchancetowater = starttime.date()
if starttime.hour >= 10:
    nextchancetowater = nextchancetowater + timedelta(days=1)
    watered_today = True
nextDecision[7] = nextchancetowater.strftime('%m/%d/%Y 10:00AM')
now = None


@jsf.use(app)
class App:
    # Main task for calling the starting functions
    def __init__(self):
        self.startSensors()
        self.startReading()
        self.startPrediction()
        self.startAPI()
        self.startLogger()
        
    # Main task for calling the loading functions
    @jsf.task
    def main(self):
        while True:           
            try:
                self.loadAPI()
                time.sleep(3)
            except Exception as e:
                print(f'Page Error {datetime.now()}: {e}')
                break   

    # LOAD: Webpage data
    @jsf.task
    def loadAPI(self):
        try:           
            # Previous Decision
            self.js.dom.preCOR.innerHTML = f"{lastDecision[0]}%"
            self.js.dom.preASM.innerHTML = f"{lastDecision[1]}%"
            self.js.dom.preSM1.innerHTML = f"{lastDecision[2]}%"
            self.js.dom.preSM2.innerHTML = f"{lastDecision[3]}%"
            self.js.dom.preSM3.innerHTML = f"{lastDecision[4]}%"
            self.js.dom.preDEC.innerHTML = f"Action {lastDecision[5]}"
            self.js.dom.preCON.innerHTML = lastDecision[6]
            self.js.dom.preTIM.innerHTML = lastDecision[7]

            # Current Decision
            self.js.dom.curCOR.innerHTML = f"{nextDecision[0]}%"
            self.js.dom.curASM.innerHTML = f'{nextDecision[1]}%'
            self.js.dom.curSM1.innerHTML = f'{nextDecision[2]}%'
            self.js.dom.curSM2.innerHTML = f'{nextDecision[3]}%'
            self.js.dom.curSM3.innerHTML = f'{nextDecision[4]}%'
            self.js.dom.curDEC.innerHTML = f'Action {nextDecision[5]}'
            self.js.dom.curCON.innerHTML = nextDecision[6]
            self.js.dom.curCHA.innerHTML = nextDecision[7]

            # Current Weather
            self.js.dom.nowTEMP.innerHTML = f"{api_data['current']['temp']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.nowCOR.innerHTML = f"{(api_data['daily'][0]['pop'] * 100):.0f}%"
            self.js.dom.nowHUM.innerHTML = f"{api_data['current']['humidity']:.0f}%"
            nowURL = f"<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{api_data['current']['weather'][0]['icon']}.png\">"
            nowURL = f"{nowURL}<br>{api_data['current']['weather'][0]['description'].title()}"
            self.js.dom.nowDESC.innerHTML = nowURL

            # # Weather Forecast Table
            # Days
            self.js.dom.day1.innerHTML = "Today"
            self.js.dom.day2.innerHTML = (last_update + timedelta(1)).strftime("%a")
            self.js.dom.day3.innerHTML = (last_update + timedelta(2)).strftime("%a")
            self.js.dom.day4.innerHTML = (last_update + timedelta(3)).strftime("%a")
            self.js.dom.day5.innerHTML = (last_update + timedelta(4)).strftime("%a")
            self.js.dom.day6.innerHTML = (last_update + timedelta(5)).strftime("%a")
            self.js.dom.day7.innerHTML = (last_update + timedelta(6)).strftime("%a")
            self.js.dom.day8.innerHTML = (last_update + timedelta(7)).strftime("%a")

            # Icons with Condition
            img1 = f"<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{api_data['daily'][0]['weather'][0]['icon']}.png\">"
            img1 = f"{img1}<br>{api_data['daily'][0]['weather'][0]['description'].title()}"
            self.js.dom.wea1.innerHTML = img1

            img2 = f"<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{api_data['daily'][1]['weather'][0]['icon']}.png\">"
            img2 = f"{img2}<br>{api_data['daily'][1]['weather'][0]['description'].title()}"
            self.js.dom.wea2.innerHTML = img2

            img3 = f"<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{api_data['daily'][2]['weather'][0]['icon']}.png\">"
            img3 = f"{img3}<br>{api_data['daily'][2]['weather'][0]['description'].title()}"
            self.js.dom.wea3.innerHTML = img3

            img4 = f"<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{api_data['daily'][3]['weather'][0]['icon']}.png\">"
            img4 = f"{img4}<br>{api_data['daily'][3]['weather'][0]['description'].title()}"
            self.js.dom.wea4.innerHTML = img4

            img5 = f"<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{api_data['daily'][4]['weather'][0]['icon']}.png\">"
            img5 = f"{img5}<br>{api_data['daily'][4]['weather'][0]['description'].title()}"
            self.js.dom.wea5.innerHTML = img5

            img6 = f"<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{api_data['daily'][5]['weather'][0]['icon']}.png\">"
            img6 = f"{img6}<br>{api_data['daily'][5]['weather'][0]['description'].title()}"
            self.js.dom.wea6.innerHTML = img6

            img7 = f"<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{api_data['daily'][6]['weather'][0]['icon']}.png\">"
            img7 = f"{img7}<br>{api_data['daily'][6]['weather'][0]['description'].title()}"
            self.js.dom.wea7.innerHTML = img7

            img8 = f"<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{api_data['daily'][7]['weather'][0]['icon']}.png\">"
            img8 = f"{img8}<br>{api_data['daily'][7]['weather'][0]['description'].title()}"
            self.js.dom.wea8.innerHTML = img8

            # Chance of Precipitation
            self.js.dom.cop1.innerHTML = f"{(api_data['daily'][0]['pop'] * 100):.0f}%"
            self.js.dom.cop2.innerHTML = f"{(api_data['daily'][1]['pop'] * 100):.0f}%"
            self.js.dom.cop3.innerHTML = f"{(api_data['daily'][2]['pop'] * 100):.0f}%"
            self.js.dom.cop4.innerHTML = f"{(api_data['daily'][3]['pop'] * 100):.0f}%"
            self.js.dom.cop5.innerHTML = f"{(api_data['daily'][4]['pop'] * 100):.0f}%"
            self.js.dom.cop6.innerHTML = f"{(api_data['daily'][5]['pop'] * 100):.0f}%"
            self.js.dom.cop7.innerHTML = f"{(api_data['daily'][6]['pop'] * 100):.0f}%"
            self.js.dom.cop8.innerHTML = f"{(api_data['daily'][7]['pop'] * 100):.0f}%"

            # Max temp
            self.js.dom.htem1.innerHTML = f"{api_data['daily'][0]['temp']['max']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.htem2.innerHTML = f"{api_data['daily'][1]['temp']['max']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.htem3.innerHTML = f"{api_data['daily'][2]['temp']['max']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.htem4.innerHTML = f"{api_data['daily'][3]['temp']['max']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.htem5.innerHTML = f"{api_data['daily'][4]['temp']['max']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.htem6.innerHTML = f"{api_data['daily'][5]['temp']['max']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.htem7.innerHTML = f"{api_data['daily'][6]['temp']['max']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.htem8.innerHTML = f"{api_data['daily'][7]['temp']['max']:.0f}\N{DEGREE SIGN}F"

            # Min temp
            self.js.dom.ltem1.innerHTML = f"{api_data['daily'][0]['temp']['min']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.ltem2.innerHTML = f"{api_data['daily'][1]['temp']['min']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.ltem3.innerHTML = f"{api_data['daily'][2]['temp']['min']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.ltem4.innerHTML = f"{api_data['daily'][3]['temp']['min']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.ltem5.innerHTML = f"{api_data['daily'][4]['temp']['min']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.ltem6.innerHTML = f"{api_data['daily'][5]['temp']['min']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.ltem7.innerHTML = f"{api_data['daily'][6]['temp']['min']:.0f}\N{DEGREE SIGN}F"
            self.js.dom.ltem8.innerHTML = f"{api_data['daily'][7]['temp']['min']:.0f}\N{DEGREE SIGN}F"

            # Humidity
            self.js.dom.hum1.innerHTML = f"{api_data['daily'][0]['humidity']}%"
            self.js.dom.hum2.innerHTML = f"{api_data['daily'][1]['humidity']}%"
            self.js.dom.hum3.innerHTML = f"{api_data['daily'][2]['humidity']}%"
            self.js.dom.hum4.innerHTML = f"{api_data['daily'][3]['humidity']}%"
            self.js.dom.hum5.innerHTML = f"{api_data['daily'][4]['humidity']}%"
            self.js.dom.hum6.innerHTML = f"{api_data['daily'][5]['humidity']}%"
            self.js.dom.hum7.innerHTML = f"{api_data['daily'][6]['humidity']}%"
            self.js.dom.hum8.innerHTML = f"{api_data['daily'][7]['humidity']}%"
            
            # Weather Alerts
            if alert[0]:
                self.js.dom.alert.innerHTML = "<b>ALERT IN EFFECT:</b> {}<br><p>{}</p>".format(alert[0], alert[1])
            
            # Get time of last update
            self.js.dom.updatetime.innerHTML = last_update.strftime("%a., %m/%d/%Y, %I:%M%p")
            
        except:
            time.sleep(2) 
                
    # START: Logger
    @jsf.task
    def startLogger(self):
        logNow = True
        while True:
            global checked_today, watered_today, lastDecision, nextDecision, first_log, override, emergency, special
            now = datetime.now()
            date = now.date()
            hour = now.hour
            minute = now.minute
            
            # Re-creates trainingLog if not present
            # This log is renamed everytime training is ran
            if os.path.exists('logs/trainingLog.csv') is False:
                log = open("logs/trainingLog.csv", "a")
                log.write("state[], PredOutput[], statePrime[]\n")
                log.close()
            
            # Record "Date, Time, AvgSoil, Sensor1, Sensor2, Sensor3"
            # Logs every 5 minutes
            if (minute % 5 == 0 and logNow == True):
                log = open("logs/moistureLog.csv", "a")
                log.write('{}, {}:{:02d}, {}, {}, {}, {}\n'.format(date, hour, minute, nextDecision[1], nextDecision[2], nextDecision[3], nextDecision[4]))
                log.close()
                logNow = False
            else:
                logNow = True
            
            # Water plants (if necessary) at 10AM
            # Record "Date, Time, ChanceRain, SoilMoisture, Action, Confidence,"
            # Soil moisture resulting from action is recorded 12 hours later, below
            if (hour == 10 and minute == 0 and watered_today is False):
                log = open("logs/waterLog.csv", "a")
                log.write('{}, {}:{:02d}, {}, {}, {}, {}, '.format(date, hour, minute, int(nextDecision[0]), nextDecision[1], nextDecision[5], nextDecision[6]))
                log.close()
                
                # Copy current decision to last decision
                for i in range(0, len(nextDecision)):    
                    lastDecision[i] = nextDecision[i]
                
                # Store Last Decision
                log = open('logs/lastDecision.csv', "w")
                for i in range(7):
                    log.write(f'{lastDecision[i]}, ')
                log.write(f'{lastDecision[7]}')
                log.close()
                
                # Store data for training
                log = open("logs/trainingLog.csv", "a")
                log.write(f'{last_state}, {list_act}, ')
                log.close()
                
                # Water the plant
                if override is False:
                    pump.runPump(nextDecision[5] * 5)
                    
                nextchancetowater = date + timedelta(days=1)
                nextDecision[7] = nextchancetowater.strftime('%m/%d/%Y 10:00AM')
                watered_today = True
                first_log = False

            # Record soil moisture (resulting from action at 10am) at 10PM
            # Append to associated decision
            # If plants have never been watered by system, don't log this
            if (hour == 22 and minute == 0 and checked_today == False and first_log == False):
                log = open("logs/waterLog.csv", "a")
                if override:
                    log.write('{}, OVERRIDE\n'.format(nextDecision[1]))
                    override = False
                elif emergency:
                    log.write('{}, EMERGENCY\n'.format(nextDecision[1]))
                    emergency = False
                else:
                    log.write('{}, STABLE\n'.format(nextDecision[1]))
                log.close()
                checked_today = True
                
                log = open("logs/trainingLog.csv", "a")
                log.write(f'{last_state}\n')
                log.close()
                today = now.strftime("%A")
                
                # If it's Sunday, then update the model with the current data log
                if today == 'Sunday':
                    needsUpdate = True
                
            # At end of day, reset log checks to continue recording logs
            if (now.hour == 23 and now.minute == 59):
                checked_today = False
                watered_today = False
                
            time.sleep(30)
    
    # START: Sensor stream
    @jsf.task
    def startSensors(self):
        global sensors
        sensors.readSensors()
        
    # START: Reading sensor stream
    @jsf.task
    def startReading(self):
        global sensor1, sensor2, sensor3, sensors, avgMoisture
        while True:
            sensor1 = sensors.s0
            sensor2 = sensors.s1
            sensor3 = sensors.s2
            avgMoisture = sensors.am
            # Save data for next decision
            nextDecision[2] = sensor1
            nextDecision[3] = sensor2
            nextDecision[4] = sensor3
            nextDecision[1] = avgMoisture
            time.sleep(30)

    # START: Agent predictions and the weekly model update
    # Runs every 5 minutes
    @jsf.task
    def startPrediction(self):
        global last_state, nextDecision, list_act, needsUpdate
        while True:
            # This is only triggered once a week.
            if needsUpdate:
                subprocess.run((['python3', 'updateModel.py']), capture_output=False)
                needsUpdate = False
            try:
                if last_state is None or last_state[0] != avgMoisture or last_state[1] != nextDecision[0]:
                    nextDecision[0] = int(api_data['daily'][0]['pop'] * 100)
                    pred = subprocess.run(['python3', 'loadModel.py', str(avgMoisture), str(nextDecision[0])], capture_output=True)
                    pred = pred.stdout.decode(sys.stdout.encoding).strip()
                    pred = pred[2:-2]
                    last_state = [avgMoisture, nextDecision[0]]
                    actions = pred.split()
                    act_map = map(float32, actions)
                    list_act = list(act_map)
                    nextDecision[5] = np.argmax(list_act)
                    nextDecision[6] = np.amax(list_act) * 100
                    nextDecision[6] = f'{nextDecision[6]:.0f}%'
            except Exception as e:
                print(f'Prediction Error {datetime.now()}: {e}')
            finally:
                time.sleep(300)

    # START: API Data calls
    # Loops every 30sec, but updates every 5 minutes.
    @jsf.task
    def startAPI(self):
        global last_update, api_data, alert
        minute = time.localtime().tm_min
        hour = time.localtime().tm_hour
        nextCall = minute + 1
        if nextCall >= 60:
            nextCall = 0
        count = 1
        print('Starting API calls')
        while True:
            if minute is nextCall:
                try:
                    # Load API data to temp variable
                    count += 1
                    print(f"Calling API - Count:{count} {datetime.now()}")
                    new_data = weather.hourlyForecast()
                    # If forecast returns empty set, do not update global from temp
                    if new_data:
                        # Get time to show last update
                        last_update = datetime.now()
                        api_data = new_data
                        if 'alerts' in api_data:
                            alert[0] = api_data['alerts'][0]['description']
                            alert[1] = api_data['alerts'][0]['event']
                        else:
                            alert = [None, None]
                    else:
                        print(f'No API data returned. {datetime.now()}')
                    # Update every five minutes
                    nextCall = nextCall + 5
                    # Reset minute counter at end of hour
                    if nextCall >= 60:
                        nextCall = 0
                    # Reset API call count at end of day
                    if hour is 0 and minute is 0:
                        count = 0    
                except Exception as e:
                    print(f'API Error {datetime.now()}: {e}')
                    time.sleep(30)
                    
            time.sleep(15)
            minute = time.localtime().tm_min
            hour = time.localtime().tm_hour

    # BUTTON: Manual "water" command
    @jsf.task
    def manual_water(self):
        now = datetime.now()
        date = now.date()
        hour = now.hour
        minute = now.minute
        log = open("logs/actionLog.csv", "a")
        
        # Record "Date, Time, ChanceRain, SoilMoisture, Action, Confidence, MANUAL"
        log.write('{}, {}:{:02d}, {:d}, {}, {}, {}, MANUAL\n'.format(date, hour, minute, nextDecision[0], nextDecision[1], nextDecision[5], nextDecision[6]))
        log.close()
        
        # Change last decision
        for i in range(0, 5):
            lastDecision[i] = nextDecision[i]
        lastDecision[5] = 'Quick Water (5s)'
        lastDecision[6] = 'N/A'
        lastDecision[7] = now.strftime('%m/%d/%Y %I:%M%p')
        
        # Store last decision
        log = open('logs/lastDecision.csv', "w")
        for i in range(7):
            log.write(f'{lastDecision[i]}, ')
        log.write(f'{lastDecision[7]}')
        log.close()
        
        # Run pump
        pump.quickPump()

    # BUTTON: Emergency Stop
    @jsf.task
    def emergency(self):
        global emergency
        pump.killPump()
        emergency = True
        now = datetime.now()
        date = now.date()
        hour = now.hour
        minute = now.minute
        log = open("logs/actionLog.csv", "a")
        
        # Record "Date, Time, ChanceRain, SoilMoisture, Action, Confidence, EMERGENCY"
        log.write('{}, {}:{:02d}, {:d}, {}, {}, {}, EMERGENCY\n'.format(date, hour, minute, nextDecision[0], nextDecision[1], nextDecision[5], nextDecision[6]))
        log.close()
        
    # BUTTON: Cancel next water
    @jsf.task
    def override_next(self):
        global override
        override = True
        now = datetime.now()
        date = now.date()
        hour = now.hour
        minute = now.minute
        log = open("logs/actionLog.csv", "a")
        
        # Record "Date, Time, ChanceRain, SoilMoisture, Action, Confidence, OVERRIDE"
        log.write('{}, {}:{:02d}, {:d}, {}, {}, {}, OVERRIDE\n'.format(date, hour, minute, nextDecision[0], nextDecision[1], nextDecision[5], nextDecision[6]))
        log.close()


# Main page for project
@app.route('/')
def main_page():
    App.main()
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)
    return App.render(render_template('index.html'))


# About page for project
@app.route('/about')
def about_page():
    return App.render(render_template('about.html'))


if __name__ == '__main__':
    try:
        # Use when running waitress server
        serve(app, port=8080, host='0.0.0.0')
        # Use when running flask server
    except Exception as e:
        # If something happens, cleanup irrigation pump pin
        print(f'Program Error {datetime.now()}: {e}')
        GPIO.cleanup()
