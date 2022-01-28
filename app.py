import sys
import time
import numpy as np
from flask import Flask, render_template, request
import jyserver.Flask as jsf
from numpy import float32
from plant_ML import weather, Gardener
from datetime import datetime, timedelta
from plant_ML.Gardener import SensorStream, WaterPump
import subprocess

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
UPLOAD_FOLDER = './static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

last_time_watered = '11/14/2021 11:00AM'
nextchancetowater = '11/15/2021  1:00PM'
last_update = datetime.now()

# Initial API Call
api_data = weather.hourlyForecast()
if api_data:
    last_update = datetime.now()

sensor1 = 0
sensor2 = 0
sensor3 = 0
sensors = SensorStream()
avgMoisture = 0
cor = 0
last_state = None
best_action = None
confidence = None

# Watering Times
# watering_times = ['9:00AM', '10:00AM', '11:00AM', '12:00AM']
watering_times = '9:00'


# ChanceRain, AvgSoilMoist, Plant1, Plant2, Plant3, Action, Confidence, Time
lastDecision = [0, 67, 67, 71, 62, 0, '100%', '11/14/2021 11:00AM']
nextDecision = []
count = 0


@jsf.use(app)
class App:

    # Start Soil Moisture Sensor Stream
    # Loaded once
    def __init__(self):
        self.startReader()
        self.readReader()
        self.makePrediction()
        self.loadPrediction()
        self.get_API()

    # Main task for calling/loading API and agent data
    # Loaded every refresh
    @jsf.task
    def main(self):
        global api_data, last_update
        while True:
            try:
                self.dashboard_data()
                # Wait before refreshing
                time.sleep(5)
            except TimeoutError:
                return
            except TypeError:
                return

    # Task for loading API and Agent data onto webpage
    @jsf.task
    def dashboard_data(self):
        global api_data, sensor1, sensor2, sensor3, sensors
        global last_update
        try:
            # If there is an alert, add it to the DOM
            if 'alerts' in api_data:
                alerts = api_data['alerts']
                alert_description = api_data['alerts'][0]['description']
                event = api_data['alerts'][0]['event']
                self.js.dom.alert.innerHTML = "<div class=\"card-med\">ALERT IN EFFECT: {}<br><p>{}</p></div>".format(
                    event,
                    alert_description)

            # Get time to show last update
            self.js.dom.time.innerHTML = last_update.strftime("%A, %H:%M:%S, %m/%d/%Y")

            # Previous Decision
            global lastDecision
            if lastDecision:
                self.js.dom.preCOR.innerHTML = "{:.0f}%".format(lastDecision[0])
                self.js.dom.preASM.innerHTML = "{}%".format(lastDecision[1])
                self.js.dom.preSM1.innerHTML = "{}%".format(lastDecision[2])
                self.js.dom.preSM2.innerHTML = "{}%".format(lastDecision[3])
                self.js.dom.preSM3.innerHTML = "{}%".format(lastDecision[4])
                self.js.dom.preDEC.innerHTML = "Action {}".format(lastDecision[5])
                self.js.dom.preCON.innerHTML = lastDecision[6]
                self.js.dom.preTIM.innerHTML = lastDecision[7]

            # Current Decision Info (not the prediction)
            self.js.dom.curCOR.innerHTML = "{:.0f}%".format(api_data['daily'][0]['pop'] * 100)
            self.js.dom.curASM.innerHTML = '{}%'.format(avgMoisture)
            self.js.dom.curSM1.innerHTML = '{}%'.format(sensor1)
            self.js.dom.curSM2.innerHTML = '{}%'.format(sensor2)
            self.js.dom.curSM3.innerHTML = '{}%'.format(sensor3)
            self.js.dom.curCHA.innerHTML = nextchancetowater

            # Current Weather
            self.js.dom.nowTEMP.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['current']['temp'])
            self.js.dom.nowCOR.innerHTML = "{:.0f}%".format(api_data['daily'][0]['pop'] * 100)
            self.js.dom.nowHUM.innerHTML = "{:.0f}%".format(api_data['current']['humidity'])
            nowURL = "<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{}.png\">"
            nowURL = nowURL.format(api_data['current']['weather'][0]['icon'])
            nowURL = "{}<br>{}".format(nowURL, api_data['current']['weather'][0]['description'].title())
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
            img1 = "<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{}.png\">".format(
                api_data['daily'][0]['weather'][0]['icon'])
            img1 = "{}<br>{}".format(img1, api_data['daily'][0]['weather'][0]['description'].title())
            self.js.dom.wea1.innerHTML = img1

            img2 = "<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{}.png\">".format(
                api_data['daily'][1]['weather'][0]['icon'])
            img2 = "{}<br>{}".format(img2, api_data['daily'][1]['weather'][0]['description'].title())
            self.js.dom.wea2.innerHTML = img2

            img3 = "<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{}.png\">".format(
                api_data['daily'][2]['weather'][0]['icon'])
            img3 = "{}<br>{}".format(img3, api_data['daily'][2]['weather'][0]['description'].title())
            self.js.dom.wea3.innerHTML = img3

            img4 = "<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{}.png\">".format(
                api_data['daily'][3]['weather'][0]['icon'])
            img4 = "{}<br>{}".format(img4, api_data['daily'][3]['weather'][0]['description'].title())
            self.js.dom.wea4.innerHTML = img4

            img5 = "<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{}.png\">".format(
                api_data['daily'][4]['weather'][0]['icon'])
            img5 = "{}<br>{}".format(img5, api_data['daily'][4]['weather'][0]['description'].title())
            self.js.dom.wea5.innerHTML = img5

            img6 = "<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{}.png\">".format(
                api_data['daily'][5]['weather'][0]['icon'])
            img6 = "{}<br>{}".format(img6, api_data['daily'][5]['weather'][0]['description'].title())
            self.js.dom.wea6.innerHTML = img6

            img7 = "<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{}.png\">".format(
                api_data['daily'][6]['weather'][0]['icon'])
            img7 = "{}<br>{}".format(img7, api_data['daily'][6]['weather'][0]['description'].title())
            self.js.dom.wea7.innerHTML = img7

            img8 = "<img class=\"icon\" src=\"http://openweathermap.org/img/wn/{}.png\">".format(
                api_data['daily'][7]['weather'][0]['icon'])
            img8 = "{}<br>{}".format(img8, api_data['daily'][7]['weather'][0]['description'].title())
            self.js.dom.wea8.innerHTML = img8

            # Chance of Precipitation
            self.js.dom.cop1.innerHTML = "{:.0f}%".format(api_data['daily'][0]['pop'] * 100)
            self.js.dom.cop2.innerHTML = "{:.0f}%".format(api_data['daily'][1]['pop'] * 100)
            self.js.dom.cop3.innerHTML = "{:.0f}%".format(api_data['daily'][2]['pop'] * 100)
            self.js.dom.cop4.innerHTML = "{:.0f}%".format(api_data['daily'][3]['pop'] * 100)
            self.js.dom.cop5.innerHTML = "{:.0f}%".format(api_data['daily'][4]['pop'] * 100)
            self.js.dom.cop6.innerHTML = "{:.0f}%".format(api_data['daily'][5]['pop'] * 100)
            self.js.dom.cop7.innerHTML = "{:.0f}%".format(api_data['daily'][6]['pop'] * 100)
            self.js.dom.cop8.innerHTML = "{:.0f}%".format(api_data['daily'][7]['pop'] * 100)

            # Max temp
            self.js.dom.htem1.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][0]['temp']['max'])
            self.js.dom.htem2.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][1]['temp']['max'])
            self.js.dom.htem3.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][2]['temp']['max'])
            self.js.dom.htem4.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][3]['temp']['max'])
            self.js.dom.htem5.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][4]['temp']['max'])
            self.js.dom.htem6.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][5]['temp']['max'])
            self.js.dom.htem7.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][6]['temp']['max'])
            self.js.dom.htem8.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][7]['temp']['max'])

            # Min temp
            self.js.dom.ltem1.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][0]['temp']['min'])
            self.js.dom.ltem2.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][1]['temp']['min'])
            self.js.dom.ltem3.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][2]['temp']['min'])
            self.js.dom.ltem4.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][3]['temp']['min'])
            self.js.dom.ltem5.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][4]['temp']['min'])
            self.js.dom.ltem6.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][5]['temp']['min'])
            self.js.dom.ltem7.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][6]['temp']['min'])
            self.js.dom.ltem8.innerHTML = "{:.0f}\N{DEGREE SIGN}F".format(api_data['daily'][7]['temp']['min'])

            # Humidity
            self.js.dom.hum1.innerHTML = "{}%".format(api_data['daily'][0]['humidity'])
            self.js.dom.hum2.innerHTML = "{}%".format(api_data['daily'][1]['humidity'])
            self.js.dom.hum3.innerHTML = "{}%".format(api_data['daily'][2]['humidity'])
            self.js.dom.hum4.innerHTML = "{}%".format(api_data['daily'][3]['humidity'])
            self.js.dom.hum5.innerHTML = "{}%".format(api_data['daily'][4]['humidity'])
            self.js.dom.hum6.innerHTML = "{}%".format(api_data['daily'][5]['humidity'])
            self.js.dom.hum7.innerHTML = "{}%".format(api_data['daily'][6]['humidity'])
            self.js.dom.hum8.innerHTML = "{}%".format(api_data['daily'][7]['humidity'])

        except TimeoutError:
            time.sleep(1)
        except TypeError:
            time.sleep(1)

    # Fetch API Data
    @jsf.task
    def get_API(self):
        global last_update, api_data
        calls = 1
        while True:
            time.sleep(60)
            # Load API data to temp variable
            new_data = weather.hourlyForecast()
            calls = calls + 1
            print("Calls made: {}".format(calls))
            # If forecast returns empty set, do not update global from temp
            if new_data:
                # Get time to show last update
                last_update = datetime.now()
                api_data = new_data

    # Send manual "water" command to system
    @jsf.task
    def water(self):
        global watering_times

    # Send manual "stop water" command to system
    @jsf.task
    def no_water(self):
        pass

    # Send manual "emergency stop" command to system
    @jsf.task
    def disable(self):
        pass

    # Send manual "emergency stop" command to system
    @jsf.task
    def startReader(self):
        global sensors
        sensors.readSensors()
        time.sleep(15)

    @jsf.task
    def readReader(self):
        global sensor1, sensor2, sensor3, sensors, avgMoisture, cor
        while True:
            sensor1 = sensors.s0
            sensor2 = sensors.s1
            sensor3 = sensors.s2
            avgMoisture = sensors.am
            time.sleep(1)

    # Start agent predictions
    @jsf.task
    def makePrediction(self):
        global avgMoisture, cor, last_state, best_action, confidence
        while True:
            if last_state is None or last_state[0] != avgMoisture or last_state[1] != cor:
                cor = (api_data['daily'][0]['pop'] * 100)
                pred = subprocess.run(['python3', 'loadModel.py', str(avgMoisture), str(cor)], capture_output=True)
                last_state = [avgMoisture, cor]
                pred = pred.stdout.decode(sys.stdout.encoding).strip()
                pred = pred[2:-2]
                actions = pred.split()
                act_map = map(float32, actions)
                list_act = list(act_map)
                best_action = np.argmax(list_act)
                confidence = np.amax(list_act) * 100
                confidence = '{:.0f}%'.format(confidence)
            time.sleep(60)

    # Start agent predictions
    @jsf.task
    def loadPrediction(self):
        global best_action, confidence
        while True:
            try:
                if confidence:
                    self.js.dom.curCON.innerHTML = confidence
                if best_action:
                    self.js.dom.curDEC.innerHTML = 'Action {}'.format(best_action)
                time.sleep(5)
            except TimeoutError:
                time.sleep(1)
            except TypeError:
                time.sleep(1)


# Main page for project
@app.route('/')
def main_page():
    global api_data
    App.main()
    return App.render(render_template('index.html'))


# About page for project
@app.route('/about')
def about_page():
    return App.render(render_template('about.html'))


if __name__ == '__main__':
    # For RPi
    # Replace the two strings with a port number and IP address, respectively.
    app.run(port=PORT_NUMBER_HERE, host='IP ADDRESS HERE')
    # For PC
    # app.run()
