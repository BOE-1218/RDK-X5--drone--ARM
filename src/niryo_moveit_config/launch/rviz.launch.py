from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    moveit_config_pkg = get_package_share_directory('niryo_moveit_config')

    # RViz only
    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(moveit_config_pkg, 'launch', 'moveit_rviz.launch.py')
        )
    )

    return LaunchDescription([rviz_launch])
