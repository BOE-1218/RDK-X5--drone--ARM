#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/sunrise/ros2_ws/install/setup.bash

echo '--- test 1: offboard false (退回 HOLD) ---'
ros2 service call /px4_control_node/offboard std_srvs/srv/SetBool "{data: false}"

echo
echo '--- test 2: arm false (disarm) ---'
ros2 service call /px4_control_node/arm std_srvs/srv/SetBool "{data: false}"

echo
echo '--- test 3: topic list ---'
ros2 topic list

