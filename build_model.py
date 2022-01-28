#!/usr/bin/env python3

"""
This file is used to create and train the model that will be launched on the Raspberry Pi.
This program is meant to run on PC/MAC, not Raspberry Pi.
"""

import os
import random
from abc import ABC
from tensorflow.keras import models
import numpy as np
from gym import Env
from gym.spaces import Discrete, Box
from rl.agents import DQNAgent
from rl.memory import SequentialMemory
from rl.policy import BoltzmannQPolicy, EpsGreedyQPolicy, GreedyQPolicy
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Set to True to test environment without compiling any models/agents
testing = False
modelPath = './modelTest10.h5'
weightPath = 'DQNtest10.h5'

# Step per episode
steps = 1000
# Number of episodes
episodes = 10
# Score requirement per episode
score_requirement = 100
accepted_scores = []
scores = []


# Creates an environment that emulates a Markov Decision Process
# Finite process -> steps
# Rewards for watering well and punishes for watering bad
# Action -> Observation -> Reward
class PlantEnv(Env, ABC):
    def __init__(self):
        # Actions = water: 0=(none), 1=(3 seconds), 2=(4 seconds), 3=(5 seconds), 4=(6 seconds)
        self.action_space = Discrete(5)

        # Starting Moisture
        moisture = 20 + random.randint(-10, 10)
        # Starting Chance of Rain
        chance_of_rain = 50 + random.randint(-50, 50)

        # Observations
        self.observation_space = Box(low=np.array([0, 0]), high=np.array([100, 100]), dtype=np.int)
        self.state = moisture, chance_of_rain

        # Number of water steps left
        self.water_length = steps

    def step(self, action):
        # Retrieve previous state
        moisture, chance_of_rain = self.state

        # Force action override for plant protection
        if moisture >= 100:
            action = 0
        elif moisture <= 0 and action == 0:
            action = 4

        # Action section
        water = 0

        if action == 1:
            water = 2
        elif action == 2:
            water = 4
        elif action == 3:
            water = 6
        elif action == 4:
            water = 8

        # The lower/higher this is, greatly affects the scoring
        #  5 or 6 is the best with this setup
        moisture += (water * 6)
        self.water_length -= 1

        # Apply noise to test program
        # Simulate real-life conditions: evaporation, water loss, rain
        # Not used in final program
        moistureLoss = 5 + random.randint(5, 30)
        moisture -= moistureLoss

        # Simulate chance of rain
        if chance_of_rain > 95:
            moisture += (20 + random.randint(0, 15))
        elif chance_of_rain > 90:
            moisture += (10 + random.randint(0, 10))
        elif chance_of_rain > 80:
            moisture += (5 + random.randint(0, 5))

        chance_of_rain = 50 + random.randint(-50, 50)

        # Reward Section
        reward = 0
        if 40 <= moisture <= 60:
            reward = 3
        # If moisture is dry or wet
        elif 60 < moisture <= 80 or 20 <= moisture < 40:
            reward = -1
        # If moisture is really dry or really wet
        elif 80 < moisture <= 100 or 0 <= moisture < 20:
            reward = -2
        # If moisture is really dry or really wet
        elif 100 < moisture or moisture < 0:
            reward = -3

        # Check if shower is done
        if self.water_length <= 0:
            done = True
        else:
            done = False

        # Set placeholder for info
        info = {}

        # Save current state
        self.state = moisture, chance_of_rain

        # Return step information
        return self.state, reward, done, info

    def reset(self):
        # Reset test environment
        # Set starting moisture
        moisture = 20 + random.randint(-10, 10)
        # Set starting chance of rain array
        chance_of_rain = 50 + random.randint(-50, 50)
        self.state = moisture, chance_of_rain
        # Reset Test time
        self.water_length = steps
        return self.state


# Build Model
def build_model():
    model = Sequential()
    model.add(Flatten(input_shape=(1, 2)))
    model.add(Dense(100, activation='relu'))
    model.add(Dense(100, activation='sigmoid'))
    model.add(Dense(100, activation='relu'))
    model.add(Dense(5, activation='softmax'))
    return model


# Build Agent
def build_agent(model):
    policy = EpsGreedyQPolicy()
    memory = SequentialMemory(limit=100000, window_length=1)
    dqn = DQNAgent(model=model, memory=memory, policy=policy, nb_actions=5,
                   nb_steps_warmup=50000, target_model_update=1e-3)
    return dqn


# Build Deep-Q-Network
def build_qn(dqn):
    dqn.compile(Adam(learning_rate=1e-3), metrics=['mae', 'accuracy'])
    dqn.fit(env, nb_steps=200000, visualize=False, verbose=1)
    return dqn


# Run edge case test run to see where model makes certain guesses
def edge_case_test_run(dqn):
    # Test print prediction
    print("DQN Prediction (100, 0)   = {} ".format(dqn.model.predict(np.array([[[100, 0]]]))))
    print("DQN Prediction (0, 100)   = {} ".format(dqn.model.predict(np.array([[[0, 100]]]))))
    print("DQN Prediction (0, 0)     = {} ".format(dqn.model.predict(np.array([[[0, 0]]]))))
    print("DQN Prediction (100, 100) = {} ".format(dqn.model.predict(np.array([[[100, 100]]]))))
    print("DQN Prediction (25, 75)   = {} ".format(dqn.model.predict(np.array([[[25, 75]]]))))
    print("DQN Prediction (75, 25)   = {} ".format(dqn.model.predict(np.array([[[75, 25]]]))))
    print("DQN Prediction (50, 0)    = {} ".format(dqn.model.predict(np.array([[[50, 0]]]))))
    print("DQN Prediction (0, 50)    = {} ".format(dqn.model.predict(np.array([[[0, 50]]]))))
    print("DQN Prediction (50, 50)   = {} ".format(dqn.model.predict(np.array([[[50, 50]]]))))


# Test environment
def test_environment():
    good_episodes = 0
    # Create episodes and initiate simulation
    for episode in range(1, episodes + 1):
        observation = env.reset()
        done = False
        score = 0
        history = []
        prev_observation = []

        # Print starting moisture to compare to ending moisture
        # print("Start Moisture: {}%".format(observation[0]))
        while not done:
            action = env.action_space.sample()
            if observation[0] > 100:
                action = 0
            elif observation[0] < 0:
                action = 4
            observation, reward, done, info = env.step(action)
            score += reward
            if len(prev_observation) > 0:
                history.append([prev_observation, action])
            prev_observation = observation

        # Print ending moisture to compare to starting moisture
        # Then print Episode number and score
        print("End Moisture  : {}%".format(observation[0]))
        print('Episode: {}  Score:{}\n'.format(episode, score))

        # Gather scores for episodes scoring above requirement
        if score >= score_requirement:
            good_episodes += 1
            accepted_scores.append(score)
            for data in history:
                if data[1] == 1:
                    output = [1]
                else:
                    output = [0]

        scores.append(score)

    # Print number of episodes above score requirement
    if len(accepted_scores) > 0:
        print("Average accepted score: ", np.mean(accepted_scores))
        print("Median accepted score : ", np.median(accepted_scores))
    print("Episodes above accepted score of {}: {}/{}\n".format(score_requirement, good_episodes, episodes))

if __name__ == '__main__':
    # # Create environment
    env = PlantEnv()

    if testing:
        test_environment()
        exit()

    # Build Model and print summary
    model = build_model()
    # model.summary()

    # Build DQN & Agent
    print("Building and compiling agent.")
    dqn = build_agent(model)
    dqn = build_qn(dqn)
    print("Building and compiling complete.")

    # Save Model
    print("Saving model.")
    model.save(modelPath, overwrite=True)
    print("Model saved.")

    # Save Weights
    print("Saving weights.")
    dqn.save_weights(weightPath, overwrite=True)
    print("Weights saved.")

    # Do test run and print scores
    scores = dqn.test(env, nb_episodes=5, visualize=False)
    print(np.mean(scores.history['episode_reward']))

    # Test edge case predictions of environment
    edge_case_test_run(dqn)
