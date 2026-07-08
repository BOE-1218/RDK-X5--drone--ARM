from setuptools import setup

package_name = 'aerial_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/px4_node.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ros2_working_place',
    maintainer_email='dev@example.com',
    description='PX4 飞控 ROS2 控制节点，通过 MAVLink 协议连接 PX4 飞控。',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'px4_node = aerial_control.px4_node:main',
        ],
    },
)

