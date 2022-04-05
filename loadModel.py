# This file is used for quickly loading the model to run tests or to make a prediction.

import sys
from tensorflow.keras import models
import numpy as np
from rl.agents import DQNAgent
from rl.memory import SequentialMemory
from rl.policy import EpsGreedyQPolicy
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt


class Agent:
    def __init__(self):
        modelPath = './model.h5'
        # modelPath = './modelTest9.h5'
        # weightPath = './DQNtest9.h5'
        self.dqn = None
        self.loadedModel = models.load_model(modelPath)
        self.dqn = self.build_agent()
        self.dqn = self.build_qn()
        # loadedModel.summary()
        # self.loadedAgent = self.dqn.load_weights(filepath=weightPath)
        
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
    def build_agent(self):
        policy = EpsGreedyQPolicy()
        memory = SequentialMemory(limit=10000, window_length=1)
        self.dqn = DQNAgent(model=self.loadedModel, memory=memory, policy=policy, nb_actions=5,
                       nb_steps_warmup=50000, target_model_update=1e-3)
        return self.dqn

    # Build Deep-Q-Network
    def build_qn(self):
        self.dqn.compile(Adam(learning_rate=1e-3), metrics=['mae', 'accuracy'])
        return self.dqn

    # Run edge case test run to see where model makes certain guesses
    def edge_case_test_run(self):
        # Test print prediction
        print("DQN Prediction (100, 0)   = {} ".format(self.dqn.model.predict(np.array([[[100, 0]]]))))
        print("DQN Prediction (0, 100)   = {} ".format(self.dqn.model.predict(np.array([[[0, 100]]]))))
        print("DQN Prediction (0, 0)     = {} ".format(self.dqn.model.predict(np.array([[[0, 0]]]))))
        print("DQN Prediction (100, 100) = {} ".format(self.dqn.model.predict(np.array([[[100, 100]]]))))
        print("DQN Prediction (25, 75)   = {} ".format(self.dqn.model.predict(np.array([[[25, 75]]]))))
        print("DQN Prediction (75, 25)   = {} ".format(self.dqn.model.predict(np.array([[[75, 25]]]))))
        print("DQN Prediction (50, 0)    = {} ".format(self.dqn.model.predict(np.array([[[50, 0]]]))))
        print("DQN Prediction (0, 50)    = {} ".format(self.dqn.model.predict(np.array([[[0, 50]]]))))
        print("DQN Prediction (50, 50)   = {} ".format(self.dqn.model.predict(np.array([[[50, 50]]]))))


if __name__ == "__main__":
    agent = Agent()
    if sys.argv[1] == 'test':
        agent.edge_case_test_run()
        exit()
    print(agent.predict(sys.argv[1], sys.argv[2]))
