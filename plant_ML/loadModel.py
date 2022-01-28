"""
This file is used to simplify loading/testing of model
"""

from tensorflow.keras import models
import numpy as np
from rl.agents import DQNAgent
from rl.memory import SequentialMemory
from rl.policy import EpsGreedyQPolicy
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt

# Paths to model/weights
modelPath = './plant_ML/modelTest9.h5'
weightPath = './plant_ML/DQNtest9.h5'

class Agent:
    def __init__(self):
        # Load model and weights
        self.dqn = None
        self.loadedModel = models.load_model(modelPath)
        self.dqn = build_agent(self.loadedModel)
        self.dqn = build_qn(self.dqn)
        # loadedModel.summary()
        self.loadedAgent = self.dqn.load_weights(filepath=weightPath)
        
    # Take inputs and call model to make a prediction for action
    def predict(self, moisture, chanceofrain):
        prediction = self.dqn.model.predict(np.array([[[moisture, chanceofrain]]]))
        return prediction
    
    # Print a simple "heat-map" of actions
    def print_action_map(self):
        # action = [0, 1, 2, 3, 4]
        colors = ['black', 'lime', 'purple', 'gold', 'red']
        for mois in range(0, 100):
            for cofr in range(0, 100):
                pred = self.dqn.model.predict(np.array([[[mois, cofr]]]))
                best_action = np.argmax(pred[0])
                plt.scatter(mois, cofr, color=colors[best_action])
        plt.xlabel("Soil Moisture (%)")
        plt.ylabel("Chance of Rain (%)")
        plt.grid(True)
        plt.savefig('action_map.png')

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
    return dqn

