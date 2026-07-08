"""PX4 控制节点 launch 文件

用法：
    ros2 launch aerial_control px4_node.launch.py
    ros2 launch aerial_control px4_node.launch.py port:=/dev/ttyUSB1 baudrate:=57600
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    port_arg = DeclareLaunchArgument(
        'port', default_value='/dev/ttyUSB0',
        description='USB 转串口设备路径，例如 /dev/ttyUSB0')
    baud_arg = DeclareLaunchArgument(
        'baudrate', default_value='921600',
        description='MAVLink 串口波特率，PX4 TELEM2 默认 921600')
    cmd_rate_arg = DeclareLaunchArgument(
        'cmd_rate', default_value='10.0',
        description='OFFBOARD 设定点发送频率 Hz，需 >= 2Hz 才能维持 OFFBOARD')

    px4_node = Node(
        package='aerial_control',
        executable='px4_node',
        name='px4_control_node',
        output='screen',
        parameters=[{
            'port': LaunchConfiguration('port'),
            'baudrate': LaunchConfiguration('baudrate'),
            'cmd_rate': LaunchConfiguration('cmd_rate'),
            'target_system': 1,
            'target_component': 1,
            'cmd_vel_timeout': 1.0,
            'reconnect_period': 3.0,
        }],
    )

    return LaunchDescription([port_arg, baud_arg, cmd_rate_arg, px4_node])

