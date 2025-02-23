from pathlib import Path
from SAC.SAC import SAC
from TD3.TD3 import TD3
from ros_python import ROS_env
from utils import record_eval_positions
import torch

def load_model(model_path, state_dim, action_dim, max_action, device):
    """Charge un modèle entraîné"""
    model = SAC(
        state_dim=state_dim,
        action_dim=action_dim,
        max_action=max_action,
        device=device,
        save_every=0,
        load_model=True,
    )
    directory = "src/drl_navigation_ros2/models/SAC"
    model.load(model_path, directory)  # Charge les poids du modèle
    return model

def test_model(model, env, scenarios, max_steps):
    """Fonction pour tester le modèle sur des scénarios donnés"""
    print("Début du test...")
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
            action = model.get_action(state, False)  # Pas d'exploration pendant le test
            a_in = [(action[0] + 1) / 2, action[1]]
            latest_scan, distance, cos, sin, collision, goal, a, reward = env.step(
                lin_velocity=a_in[0], ang_velocity=a_in[1]
            )
            avg_reward += reward
            count += 1
            col += collision
            gl += goal
    avg_reward /= len(scenarios)
    avg_col = col / len(scenarios)
    avg_goal = gl / len(scenarios)
    print(f"Récompense moyenne : {avg_reward}")
    print(f"Taux de collision moyen : {avg_col}")
    print(f"Taux de réussite moyen : {avg_goal}")
    print("Test terminé.")

def main():
    """Fonction principale pour tester le modèle"""
    action_dim = 2  # Nombre d'actions produites par le modèle
    max_action = 1  # Valeur absolue maximale des actions de sortie
    state_dim = 25  # Nombre de valeurs d'entrée dans le réseau de neurones
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # Utiliser CUDA si disponible
    max_steps = 300  # Nombre maximal d'étapes par épisode
    nr_eval_episodes = 10  # Nombre de scénarios à tester

    # Chemin vers le modèle entraîné (sans suffixe)
    model_path = "SAC"  # Nom de base du modèle

    # Charger le modèle
    model = load_model(model_path, state_dim, action_dim, max_action, device)

    # Initialiser l'environnement ROS
    ros = ROS_env()

    # Générer des scénarios de test
    eval_scenarios = record_eval_positions(n_eval_scenarios=nr_eval_episodes)

    # Tester le modèle
    test_model(model, ros, eval_scenarios, max_steps)

if __name__ == "__main__":
    main()
