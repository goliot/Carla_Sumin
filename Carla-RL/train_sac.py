import gym
import numpy as np
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.sac import CnnPolicy
from stable_baselines3.sac import MultiInputPolicy
from stable_baselines3.common.noise import NormalActionNoise
from carla_env import CarlaEnv
import sys
import argparse

import gym
from gym import spaces
import numpy as np


def main(model_name, load_model, town, fps, im_width, im_height, repeat_action, start_transform_type, sensors, 
         enable_preview, steps_per_episode, seed=7, action_type='continuous'):

    env = CarlaEnv(town, fps, im_width, im_height, repeat_action, start_transform_type, sensors,
                   action_type, enable_preview, steps_per_episode, playing=False)
    test_env = CarlaEnv(town, fps, im_width, im_height, repeat_action, start_transform_type, sensors,
                   action_type, enable_preview=False, steps_per_episode=steps_per_episode, playing=True)
    
    checkpoint_callback = CheckpointCallback(save_freq=10000, save_path='./logs/', name_prefix='sac_model')
    
    try:
        if load_model:
            model = SAC.load(
                model_name, 
                env, 
                action_noise=NormalActionNoise(mean=np.array([0.3, 0.0]), sigma=np.array([0.5, 0.1])))
        else:
            model = SAC(
                #CnnPolicy,
                MultiInputPolicy, 
                env,
                verbose=2,
                buffer_size=10000,
                seed=seed, 
                device='cuda', 
                tensorboard_log='./sem_sac',
                action_noise=NormalActionNoise(mean=np.array([0.3, 0]), sigma=np.array([0.5, 0.1]))
                )
            print(model.__dict__)
            model.learn(    
                total_timesteps=20000000, 
                log_interval=4,
                tb_log_name=model_name,
                callback=checkpoint_callback
                )
            model.save(model_name)
        
        if load_model:
            test_episode_length = 10
            for test_episode in range(test_episode_length):
                obs = test_env.reset()
                done = False
                while not done:
                    action, _states = model.predict(obs)
                    obs, reward, done, info = test_env.step(action)
                    test_env.render()
                    print(f"Reward: {reward}, Info: {info}")
                
    finally:
        env.close()
        test_env.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-name', help='name of model when saving')
    parser.add_argument('--load', type=bool, help='whether to load existing model')
    parser.add_argument('--map', type=str, default='Town04', help='name of carla map')
    parser.add_argument('--fps', type=int, default=10, help='fps of carla env')
    parser.add_argument('--width', type=int, default=160, help='width of camera observations')
    parser.add_argument('--height', type=int, default=80, help='height of camera observations')
    parser.add_argument('--repeat-action', type=int, help='number of steps to repeat each action')
    parser.add_argument('--start-location', type=str, help='start location type: [random, highway] for Town04')
    parser.add_argument('--sensor', action='append', type=str, help='type of sensor (can be multiple): [rgb, semantic]')
    parser.add_argument('--preview', action='store_true', help='whether to enable preview camera')
    parser.add_argument('--episode-length', type=int, help='maximum number of steps per episode')
    parser.add_argument('--seed', type=int, default=7, help='random seed for initialization')
    
    args = parser.parse_args()
    model_name = args.model_name
    load_model = args.load
    town = args.map
    fps = args.fps
    im_width = args.width
    im_height = args.height
    repeat_action = args.repeat_action
    start_transform_type = args.start_location
    sensors = args.sensor
    enable_preview = args.preview
    steps_per_episode = args.episode_length
    seed = args.seed

    main(model_name, load_model, town, fps, im_width, im_height, repeat_action, start_transform_type, sensors, 
         enable_preview, steps_per_episode, seed)