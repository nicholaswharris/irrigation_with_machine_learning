# This program is used to updated the model's weights.
# It also parses the data logs and renames the models/logs as needed.
# Log files are automatically regenerated from app.py
# This program also creates two images, one before and one after the model is updated.
# All files are timestamped when they are renamed or created.

import sys
from tensorflow.keras import models
import numpy as np
from rl.agents import DQNAgent
from rl.memory import SequentialMemory
from rl.policy import EpsGreedyQPolicy
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt
import random
import os
from datetime import date

modelPath = './model.h5'
logPath = 'logs/trainingLog.csv'
env = None
step = None
trainingdata = []


def logParse():
    log = open(logPath, 'r')
    lines = log.readlines()
    for line in lines:
        # Cleaning/converting data from file
        line = line.strip()
        line = line.replace('[', "")
        line = line.replace(']', "")
        values = line.split(',')
        # Line should contain 9 total values, otherwise skip
        if len(values) is 9:
            values[0] = int(values[0])
            values[1] = int(values[1])
            values[2] = float(values[2])
            values[3] = float(values[3])
            values[4] = float(values[4])
            values[5] = float(values[5])
            values[6] = float(values[6])
            values[7] = int(values[7])
            values[8] = int(values[8])
            trainingdata.append(values)
    # Shuffle data and count number of entries/steps in data
    random.shuffle(trainingdata)
    step = len(trainingdata)
    log.close()


class updateModel:
    def __init__(self):
        self.dqn = None
        self.loadedModel = models.load_model(modelPath)
        self.dqn = self.build_agent()
        self.dqn = self.build_qn()

        if logPath:
            # Print Before & After photos of prediction map
            self.print_action_map('before')
            self.train_and_save()
            self.print_action_map('after')
            print('Model update: Successful')

    # Build Agent
    def build_agent(self):
        policy = EpsGreedyQPolicy()
        memory = SequentialMemory(limit=10000, window_length=1)
        self.dqn = DQNAgent(model=self.loadedModel, memory=memory, policy=policy, nb_actions=5, target_model_update=1)
        return self.dqn

    # Build Deep-Q-Network
    def build_qn(self):
        self.dqn.compile(Adam(learning_rate=1), metrics=['mae', 'accuracy'])
        return self.dqn

    # Retrain and save agent
    def train_and_save(self):
        steps = len(trainingdata)
        totalsteps = steps
        for state in trainingdata:
            input_state = np.array([[[state[0], state[1]]]])
            output_pred = np.array([[[state[2], state[3], state[4], state[5], state[6]]]])
            reward = 0
            best_action = np.argmax(output_pred)
            output_targ = np.array([[[0, 0, 0, 0, 0]]])

            # Check state-prime moisture
            # If moisture is "perfect":
            if 45 <= state[7] <= 65:
                reward = 3
            # If moisture is too wet
            elif 65 < state[7] <= 85:
                reward = -1
            # If moisture is too dry
            elif 20 <= state[7] < 45:
                reward = -1
            # If moisture is really wet
            elif 85 < state[7]:
                reward = -3
            # If moisture is really dry
            elif state[7] < 20:
                reward = -3

            # Calculate reward multiplied by discount factor
            # Train on batch
            output_targ[0][0][best_action] = reward * (steps/totalsteps)
            steps -= 1
            self.dqn.model.train_on_batch((input_state, output_targ))

        # Today's date for renaming old files: month_day_year.
        # Example: Sept_13_2009
        today = date.today()
        today = today.strftime("%b_%d_%Y")

        # Save Model
        tempPath = 'modelNew.h5'
        self.loadedModel.save(tempPath, overwrite=True)
        # Save old model under current date
        oldModelPath = f'model_{today}.h5'
        os.rename(modelPath, oldModelPath)
        os.rename(tempPath, modelPath)

        # Save data log under current date
        # New log will auto-generate
        oldLogPath = f'logs/data_{today}.csv'
        os.rename(logPath, oldLogPath)

    # Print a simple "heat-map" of actions
    def print_action_map(self, time):
        # action = [0, 1, 2, 3, 4]
        colors = ['lime', 'black', 'purple', 'gold', 'red']
        for mois in range(0, 100, 2):
            for cofr in range(0, 100, 2):
                pred = self.dqn.model.predict(np.array([[[mois, cofr]]]))
                best_action = np.argmax(pred[0])
                plt.scatter(mois, cofr, s=3, color=colors[best_action])
        plt.xlabel("Soil Moisture (%)")
        plt.ylabel("Chance of Rain (%)")
        plt.grid(True)

        today = date.today()
        today = today.strftime("%b_%d_%Y")
        plt.savefig(f'img/action_map_{time}_{today}.png')

        plt.clf()


if __name__ == "__main__":
    # The log is parsed and the model is updated then saved
    # If no log is found, print error message
    if os.path.isfile(logPath):
        logParse()
        updateModel()
    else:
        print("Error: No training log found.")
