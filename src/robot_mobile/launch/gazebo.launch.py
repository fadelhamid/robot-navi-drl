import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, RegisterEventHandler
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit

def generate_launch_description():
    # Arguments
    model_arg = DeclareLaunchArgument(name='model', description='Absolute path to robot urdf file')
    use_sim_time = LaunchConfiguration('use_sim_time')
    package_name = 'robot_mobile'
    pkg_share = FindPackageShare(package=package_name).find(package_name)

    # World file path
    world_file_path = 'world.world'
    world = LaunchConfiguration('world')
    world_path = os.path.join(pkg_share, 'worlds', world_file_path)

    # Debug: Print the world path
    print(f"World path: {world_path}")

    # Declare use_sim_time argument
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    # Robot name in model
    robot_name_in_model = 'tree_mobile'

    # Get URDF via xacro
    urdf_file_name = 'tree_mobile.urdf'
    urdf = os.path.join(
        get_package_share_directory('robot_mobile'),
        'urdf',
        urdf_file_name
    )
    with open(urdf, 'r') as infp:
        robot_desc = infp.read()

    robot_description = {"robot_description": robot_desc}

    # Debug: Print the URDF path
    print(f"URDF path: {urdf}")

    # Rviz2
    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='log',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # Robot state publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'use_sim_time': use_sim_time, 'robot_description': robot_desc}],
    )

    # Joint state publisher
    start_joint_state_publisher_cmd = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        parameters=[{'use_sim_time': use_sim_time}],
        name='joint_state_publisher',
    )

    # Declare world argument
    declare_world_cmd = DeclareLaunchArgument(
        name='world',
        default_value=world_path,
        description='Full path to the world model file to load'
    )

    # Spawn the robot
    spawn = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=["-file", urdf,
                   "-entity", robot_name_in_model,
                   "-x", '0.0',
                   "-y", '0.0',
                   "-z", '0.05',
                   "-Y", '0.0']
    )

    # Gazebo
    gazebo = ExecuteProcess(
        cmd=['gazebo', '--verbose', '-s', 'libgazebo_ros_factory.so',
             '-s', 'libgazebo_ros_init.so', world_path], output='screen',
    )#

    # Register event handler to spawn the robot after Gazebo starts
    spawn_robot = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=gazebo,
            on_exit=[spawn],
        )
    )

    return LaunchDescription([
        declare_use_sim_time_cmd,
        declare_world_cmd,
        gazebo,
        spawn_robot,
        rviz2,
        start_joint_state_publisher_cmd,
        robot_state_publisher_node,
    ])

