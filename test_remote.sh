#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/sunrise/ros2_ws/install/setup.bash

echo "=== 1. 当前状态 ==="
timeout 3 ros2 topic echo /px4_control_node/state --once --no-arr 2>&1 | head -5

echo ""
echo "=== 2. 切 OFFBOARD 模式 (true) ==="
timeout 5 ros2 service call /px4_control_node/offboard std_srvs/srv/SetBool "{data: true}" 2>&1 | head -10

sleep 2
echo ""
echo "=== 3. 切换后状态 ==="
timeout 3 ros2 topic echo /px4_control_node/state --once --no-arr 2>&1 | head -5

echo ""
echo "=== 4. 退回 HOLD 模式 (false) ==="
timeout 5 ros2 service call /px4_control_node/offboard std_srvs/srv/SetBool "{data: false}" 2>&1 | head -10

sleep 2
echo ""
echo "=== 5. 最终状态 ==="
timeout 3 ros2 topic echo /px4_control_node/state --once --no-arr 2>&1 | head -5

echo ""
echo "=== 6. odom 话题 (如有) ==="
timeout 3 ros2 topic echo /px4_control_node/odom --once --no-arr 2>&1 | head -20
