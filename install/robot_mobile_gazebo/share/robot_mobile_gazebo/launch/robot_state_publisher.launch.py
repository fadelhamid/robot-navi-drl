import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Déclaration de l'argument 'use_sim_time'
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')  # Définir sur 'true' pour Gazebo
    
    # Nom du fichier URDF
    urdf_file_name = 'tree_mobile.urdf'
    print(f"urdf_file_name : {urdf_file_name}")
    
    # Chemin vers le fichier URDF
    urdf_path = os.path.join(
        get_package_share_directory('robot_mobile'),
        'urdf',
        urdf_file_name
    )
    
    # Vérification de l'existence du fichier URDF
    if not os.path.exists(urdf_path):
        raise FileNotFoundError(f"URDF file not found: {urdf_path}")
    
    # Lecture du contenu URDF
    with open(urdf_path, 'r') as infp:
        robot_desc = infp.read()
    
    # Création de la description de lancement
    return LaunchDescription([
        # Argument de lancement pour le temps simulé
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',  # Définir sur 'true' pour Gazebo
            description='Use simulation (Gazebo) clock if true'
        ),
        # Nœud robot_state_publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'robot_description': robot_desc,
            }]
        ),
        # Nœud joint_state_publisher (optionnel)
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}]
        )
    ])
