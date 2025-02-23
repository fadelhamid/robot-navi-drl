import matplotlib.pyplot as plt
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
import threading
import time

# Classe pour gérer l'affichage Matplotlib en temps réel
class RobotVisualizer(Node):
    def __init__(self):
        super().__init__('robot_visualizer')
        self.robot_positions = []
        self.marker_position = (0, 0)  # Position initiale du marker (X)
        self.optimal_path = []  # Chemin optimal

        # Initialisation du graphique
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(-5, 5)
        self.ax.set_ylim(-5, 5)
        self.ax.set_title("Trajectoire du Robot")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")

        # Mode interactif activé
        plt.ion()

    def update_plot(self, robot_position, optimal_path=None):
        # Enregistre la position du robot
        self.robot_positions.append(robot_position)
        
        # Efface les anciens graphiques
        self.ax.clear()
        
        # Redéfinit les limites et titres du graphique
        self.ax.set_xlim(-5, 5)
        self.ax.set_ylim(-5, 5)
        self.ax.set_title("Trajectoire du Robot")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        
        # Trace la trajectoire du robot en bleu
        robot_x, robot_y = zip(*self.robot_positions)  # Sépare les coordonnées X et Y
        self.ax.plot(robot_x, robot_y, 'b-', label="Trajectoire réelle du robot")
        
        # Trace le marker en rouge (X)
        self.ax.plot(self.marker_position[0], self.marker_position[1], 'rx', label="Marker (X)")

        # Trace le chemin optimal en rouge (pointillés)
        if optimal_path is not None:
            optimal_x, optimal_y = zip(*optimal_path)
            self.ax.plot(optimal_x, optimal_y, 'r--', label="Chemin optimal")
        
        # Affiche la légende
        self.ax.legend()

        # Met à jour le graphique
        plt.draw()
        plt.pause(0.1)  # Pause pour 0.1 secondes pour mettre à jour le graphique

    def close(self):
        plt.ioff()  # Désactive le mode interactif
        plt.show()  # Affiche la figure finale

# Classe pour gérer la logique du mouvement du robot et la récupération des données
class RobotMovement(Node):
    def __init__(self, visualizer):
        super().__init__('robot_movement')
        self.visualizer = visualizer

        # Abonnissements aux topics
        self.create_subscription(Odometry, 'odom', self.odom_callback, 10)
        self.create_subscription(LaserScan, 'scan', self.laser_callback, 10)

        self.robot_position = (0, 0)  # Position du robot
        self.laser_data = None  # Données du LaserScan (si nécessaires pour la logique)

        # Exemple de chemin optimal (à ajuster selon tes besoins)
        self.optimal_path = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]  # Exemple simple

    def odom_callback(self, msg):
        # Récupération de la position du robot
        self.robot_position = (msg.pose.pose.position.x, msg.pose.pose.position.y)

        # Mise à jour de l'affichage
        self.visualizer.update_plot(self.robot_position, self.optimal_path)

    def laser_callback(self, msg):
        # Récupération des données du LaserScan si nécessaires
        self.laser_data = msg.ranges

# Fonction principale pour faire tourner ROS et Matplotlib en parallèle
def run_ros_node():
    rclpy.init()

    # Création du visualiseur pour la mise à jour graphique
    visualizer = RobotVisualizer()

    # Création du nœud pour le mouvement du robot
    robot_movement = RobotMovement(visualizer)

    # Utilisation d'un thread pour exécuter ROS et la visualisation en parallèle
    ros_thread = threading.Thread(target=rclpy.spin, args=(robot_movement,))
    ros_thread.start()

    try:
        # Affiche le graphique et met à jour la visualisation en temps réel
        while rclpy.ok():
            time.sleep(0.1)  # Ajoute un léger délai pour ne pas saturer la CPU
    except KeyboardInterrupt:
        pass
    finally:
        visualizer.close()  # Ferme le graphique lorsqu'on arrête
        robot_movement.destroy_node()  # Détruit le nœud ROS
        rclpy.shutdown()  # Arrête ROS
        ros_thread.join()  # Attend la fin du thread ROS

if __name__ == '__main__':
    run_ros_node()

