#!/bin/bash
. /opt/ros/humble/setup.bash
. /root/ego_ws/install/setup.bash
export ROS_LOCALHOST=1
export DISPLAY=:99

LOG=/tmp/ego_test.log
EXEC=/root/ego_ws/install/ego_planner/lib/ego_planner/ego_planner_node

echo "=== START $(date) ===" > $LOG
echo "use_depth_filter:=false test" >> $LOG

timeout 12 $EXEC --ros-args \
    -r grid_map/odom:=/odom \
    -r grid_map/depth:=/camera/camera/depth/image_rect_raw \
    -r odom_world:=/odom \
    -p grid_map/frame_id:=odom \
    -p grid_map/resolution:=0.1 \
    -p grid_map/map_size_x:=10.0 \
    -p grid_map/map_size_y:=10.0 \
    -p grid_map/map_size_z:=3.0 \
    -p grid_map/cx:=322.40570068359375 \
    -p grid_map/cy:=234.64114379882812 \
    -p grid_map/fx:=382.08209228515625 \
    -p grid_map/fy:=382.08209228515625 \
    -p grid_map/pose_type:=2 \
    -p grid_map/k_depth_scaling_factor:=1000.0 \
    -p grid_map/use_depth_filter:=false \
    -p fsm/flight_type:=1 \
    -p fsm/realworld_experiment:=true >> $LOG 2>&1

echo "EXIT=$?" >> $LOG
echo "=== END $(date) ===" >> $LOG
