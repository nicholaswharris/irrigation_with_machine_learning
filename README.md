# A reinforcement learning model used to intelligently irrigate plants.

## Files in this project 
main directory files:</br>
     1. app.py is the main program. This should be launched from a Flask environment.</br>
     2. build_model.py is used to create a reinforcement learning model.</br>
     3. loadModel.py is used to simplify loading the model and making predictions.</br>
     4. updateModel.py is used for updating the model's weight after deployment.
     5. senors.ino is the Arduino file that reads data from the sensors.</br>
     6. testArduino.py is to test reading the Arduino from the Raspberry Pi.</br>
     7. testRelay.py is to test controlling the relay/water-pump from the Raspberry Pi.</br>

plant_ML contains python and h5 files:</br>
      1. DQNTest9.h5 is the file of weights from the most recently trained model (already stored in model-file; not-needed).</br>
      2. modelTest9.h5 is the most recently trained model (with no retraining).</br>
      3. Gardener.py reads data from the Arduino via serial communication.</br>
      4. loadModel.py is used to simplify loading the model and making predictions.</br>
      5. weather.py is used to call the weather API [OpenWeather](https://openweathermap.org/api) </br>

static contains css/js/img files:</br>
      1. css - style sheet.</br>
      2. scripts - js files to create webpage background.</br>
      3. images - images on About page.</br>

templates contains http files:</br>
      1. index.html is the main webpage where weather information, model information, etc. is posted.</br>
      2. about.html is the about page giving background info.</br>


The bulk of project was built on PC in PyCharm. Afterwards, it was all migrated to a Raspberry Pi 4.

# Markov Decision Process
The first part of the project was setting up the Markov Decision Process and the environment train the model in.
![image](https://user-images.githubusercontent.com/60274317/151409344-62fe66c3-4a09-40a2-be67-6d5b821cad6a.png)

More about the Markov Decision Process here: [Toward Data Science](https://towardsdatascience.com/understanding-the-markov-decision-process-mdp-8f838510f150) & [Wikipedia](https://en.wikipedia.org/wiki/Markov_decision_process)

For this particular project, here is a better representation of how the environment looks:

![image](https://user-images.githubusercontent.com/60274317/151409454-a7e78090-edff-446a-8464-cd373730b065.png)

The model (or agent) takes the Chance of Rain from a weather API. It also gather the soil moisture from the plants. Based on it's previous training, the model makes a decision on whether or not to water the plants. This action comes with a confidence rating. The higher this number, the better. At the appropriate time of day, the action will commit: plants will be watered according to soil moisure or not at all. After a period of time, the soil moisture will be sampled again. The results, the actions, and the information that prompted the actions, are fed back to the agent for relearning. In short, if the agent constantly waters plants, but they are not watered enough, the agent will start to apply water more heavily. If the plants are often too wet after watering, the agent will start to apply water less heavily.


# Testing
After preparing a model, the model is tested. This is done by running several hundred test predictions and creating a heat map from the results:

![image](https://user-images.githubusercontent.com/60274317/151407536-24a9c99e-704f-4d4f-85de-466a53c4616a.png)

In this chart, Red is heavy watering, Yellow is regular wateriing, Purple is light watering, and Black is no watering.
Based on this image, the model that created this prefers to water heavily when the soil is very dry, lightly if the soil is already moist, and not at all if the soil is wet.
The results appear to be good. This model can be placed in a live environment.


# The Environment
The live environment is modeled here:

![image](https://user-images.githubusercontent.com/60274317/151407643-e70addc1-59d4-400e-82d3-f680c4d0a30d.png)

A Raspberry Pi hosts the model. It receives data from the Arduino while at the same time powering it. The Pi also hosts a Website where information about the irrigation system, the model's prediction, and weather information can be found.

The Arduino is connected to 3 capacitive soil-moisture sensors placed at the base of 3 plants. It feed this information via serial communication to the Raspberry Pi for further processing.

Also connected to the Raspberry Pi is a Relay Switch Module. This relay switch is powered and controlled by the Pi. The switch controls the power source for the irrigation pump. Whenever the model decides that plants need watered, the relay switch will be activated for some amount of time (in seconds) to dispense water.

The water pump is driven with AC power that is controlled by the relay switch. When the switch is turned on, water is dispensed from the pump through vinyl tubing leading to and placed at the base of the plant. The tubing is placed around the base of the plant in a circular manner.

