from pathlib import Path
from TD3.TD3 import TD3
from SAC.SAC import SAC
from ros_python import ROS_env
from replay_buffer import ReplayBuffer
import torch
import numpy as np
from utils import record_eval_positions
from pretrain_utils import Pretraining

def main(args=None):
    """Main training function"""
    action_dim = 2
    max_action = 1
    state_dim = 25
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    nr_eval_episodes = 10
    max_epochs = 30
    epoch = 0
    episodes_per_epoch = 70
    episode = 0
    train_every_n = 2
    training_iterations = 500
    batch_size = 40
    max_steps = 5e6
    steps = 0
    load_saved_buffer = True
    pretrain = True
    pretraining_iterations = 40
    save_every = 100

    # Initialisation du modèle SAC avec le périphérique approprié
    model = SAC(
        state_dim=state_dim,
        action_dim=action_dim,
        max_action=max_action,
        device=device,  # Passer le périphérique ici
        save_every=save_every,
        load_model=False,
    )

    ros = ROS_env()
    eval_scenarios = record_eval_positions(n_eval_scenarios=nr_eval_episodes)

    if load_saved_buffer:
        pretraining = Pretraining(
            file_names=["src/drl_navigation_ros2/assets/data.yml"],
            model=model,
            replay_buffer=ReplayBuffer(buffer_size=2e6, random_seed=42),
            reward_function=ros.get_reward,
        )
        replay_buffer = pretraining.load_buffer()
        if pretrain:
            pretraining.train(
                pretraining_iterations=pretraining_iterations,
                replay_buffer=replay_buffer,
                iterations=training_iterations,
                batch_size=batch_size,
            )
    else:
        replay_buffer = ReplayBuffer(buffer_size=2e6, random_seed=42)

    latest_scan, distance, cos, sin, collision, goal, a, reward = ros.step(lin_velocity=0.0, ang_velocity=0.0)

    while epoch < max_epochs:
        state, terminal = model.prepare_state(latest_scan, distance, cos, sin, collision, goal, a)
        action = model.get_action(state, True)
        a_in = [(action[0] + 1) / 2, action[1]]

        latest_scan, distance, cos, sin, collision, goal, a, reward = ros.step(lin_velocity=a_in[0], ang_velocity=a_in[1])
        next_state, terminal = model.prepare_state(latest_scan, distance, cos, sin, collision, goal, a)
        replay_buffer.add(state, action, reward, terminal, next_state)

        if terminal or steps == max_steps:
            latest_scan, distance, cos, sin, collision, goal, a, reward = ros.reset()
            episode += 1
            if episode % train_every_n == 0:
                model.train(
                    replay_buffer=replay_buffer,
                    iterations=training_iterations,
                    batch_size=batch_size,
                )
            steps = 0
        else:
            steps += 1

        if (episode + 1) % episodes_per_epoch == 0:
            episode = 0
            epoch += 1
            eval(model=model, env=ros, scenarios=eval_scenarios, epoch=epoch, max_steps=max_steps)

def eval(model, env, scenarios, epoch, max_steps):
    """Function to run evaluation"""
    print("..............................................")
    print(f"Epoch {epoch}. Evaluating {len(scenarios)} scenarios")
    avg_reward = 0.0
    col = 0
    gl = 0
    for scenario in scenarios:
        count = 0
        latest_scan, distance, cos, sin, collision, goal, a, reward = env.eval(scenario=scenario)
        while count < max_steps:
            state, terminal = model.prepare_state(latest_scan, distance, cos, sin, collision, goal, a)
            if terminal:
                break
            action = model.get_action(state, False)
            a_in = [(action[0] + 1) / 2, action[1]]
            latest_scan, distance, cos, sin, collision, goal, a, reward = env.step(lin_velocity=a_in[0], ang_velocity=a_in[1])
            avg_reward += reward
            count += 1
            col += collision
            gl += goal
    avg_reward /= len(scenarios)
    avg_col = col / len(scenarios)
    avg_goal = gl / len(scenarios)
    print(f"Average Reward: {avg_reward}")
    print(f"Average Collision rate: {avg_col}")
    print(f"Average Goal rate: {avg_goal}")
    print("..............................................")
    model.writer.add_scalar("eval/avg_reward", avg_reward, epoch)
    model.writer.add_scalar("eval/avg_col", avg_col, epoch)
    model.writer.add_scalar("eval/avg_goal", avg_goal, epoch)

if __name__ == "__main__":
    main()
