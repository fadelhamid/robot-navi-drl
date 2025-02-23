import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Configuration des arguments de lancement
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    pause = LaunchConfiguration("pause", default="false")

    # Chemin vers le fichier monde
    world_file_name = "drl/world.world"  # Utilisez le fichier world.world
    world = os.path.join(
        get_package_share_directory("robot_mobile_gazebo"),
        "worlds",
        world_file_name
    )

    # Vérification de l'existence du fichier monde
    if not os.path.exists(world):
        raise FileNotFoundError(f"World file not found: {world}")

    # Chemin vers le répertoire des fichiers de lancement
    launch_file_dir = os.path.join(
        get_package_share_directory("robot_mobile_gazebo"),
        "launch"
    )

    # Chemin vers le package gazebo_ros
    pkg_gazebo_ros = get_package_share_directory("gazebo_ros")

    # Création de la description de lancement
    return LaunchDescription([
        # Lancement de gzserver avec le fichier monde spécifié
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo_ros, "launch", "gzserver.launch.py")
            ),
            launch_arguments={
                "world": world,
                "pause": pause
            }.items(),
        ),

        # Lancement de gzclient (interface graphique de Gazebo)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo_ros, "launch", "gzclient.launch.py")
            ),
        ),

        # Lancement du robot_state_publisher
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_file_dir, "robot_state_publisher.launch.py")
            ),
            launch_arguments={
                "use_sim_time": use_sim_time
            }.items(),
        ),
    ])
