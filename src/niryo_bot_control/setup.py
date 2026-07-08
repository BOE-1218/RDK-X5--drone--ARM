from setuptools import setup

package_name = 'niryo_bot_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='cxy',
    maintainer_email='chen@126.com',
    description='Control nodes for Niryo One',
    license='BSD',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'wipe_action_node = niryo_bot_control.wipe_action_node:main',
        ],
    },
)
