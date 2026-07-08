from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    moveit_config_pkg = get_package_share_directory('niryo_moveit_config')

    # robot_state_publisher
    rsp_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(moveit_config_pkg, 'launch', 'rsp.launch.py')
        )
    )

    # ros2_control + controllers
    spawn_controllers_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(moveit_config_pkg, 'launch', 'spawn_controllers.launch.py')
        )
    )

    # MoveIt move_group
    move_group_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(moveit_config_pkg, 'launch', 'move_group.launch.py')
        )
    )

    return LaunchDescription([
        rsp_launch,
        spawn_controllers_launch,
        move_group_launch,
    ])
