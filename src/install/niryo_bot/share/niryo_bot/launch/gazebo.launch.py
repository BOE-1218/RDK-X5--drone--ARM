
# File: launch/gazebo.launch.py
 
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
import xacro
 
def generate_launch_description():
    # 获取当前包路径
    robot_package_dir = get_package_share_directory('niryo_bot')
    urdf_dir = os.path.join(robot_package_dir, 'urdf')
    urdf_file = os.path.join(urdf_dir, 'niryo_one.urdf.xacro')
    
    # 生成 URDF 文件
    urdf_output_path = os.path.join(urdf_dir, 'niryo_bot.urdf')
    
    # 读取 xacro 文件并生成 URDF
    doc = xacro.parse(open(urdf_file))
    xacro.process_doc(doc)
    with open(urdf_output_path, 'w') as f:
        f.write(doc.toxml())

    # 启动 Gazebo 空世界
    gazebo_ros_package_dir = get_package_share_directory('gazebo_ros')
    empty_world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_package_dir, 'launch', 'empty_world.launch.py')
        ),
        launch_arguments={'world': 'worlds/empty.world'}.items()
    )

    # 启动 Gazebo 模型生成器节点
    spawn_entity_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_model',
        arguments=[
            '-entity', 'niryo_bot',
            '-file', urdf_output_path,
            '-topic', 'robot_description'
        ],
        output='screen'
    )

    # 静态 TF 发布器：base_link -> base_footprint
    tf_footprint_base_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_footprint_base',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'base_footprint']
    )

    # 启动 robot_state_publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        arguments=[urdf_output_path],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        empty_world_launch,
        spawn_entity_node,
        tf_footprint_base_node,
        robot_state_publisher_node
    ])