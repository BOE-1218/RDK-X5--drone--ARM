#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/sunrise/ros2_ws/install/setup.bash

echo '--- 当前 state ---'
timeout 3 ros2 topic echo /px4_control_node/state --once

echo
echo '--- 调用 arm false (disarm, 应该已经 disarm 了, 但飞控应回 ACK) ---'
ros2 service call /px4_control_node/arm std_srvs/srv/SetBool "{data: false}"

echo
echo '--- 调用 offboard false (切 HOLD) ---'
ros2 service call /px4_control_node/offboard std_srvs/srv/SetBool "{data: false}"

echo
echo '--- 调用 offboard true (切 OFFBOARD) ---'
ros2 service call /px4_control_node/offboard std_srvs/srv/SetBool "{data: true}"

echo
echo '--- 调用 arm true (arm) ---'
ros2 service call /px4_control_node/arm std_srvs/srv/SetBool "{data: true}"

echo
echo '--- 最终 state ---'
timeout 3 ros2 topic echo /px4_control_node/state --once

echo
echo '--- 节点日志最后 20 行 ---'
# 查看节点日志看实际 arm/offboard 调用结果
LOG_DIR=$(ls -td /home/sunrise/.ros/log/*/ 2>/dev/null | head -1)
echo "log dir: $LOG_DIR"
ls $LOG_DIR 2>/dev/null

