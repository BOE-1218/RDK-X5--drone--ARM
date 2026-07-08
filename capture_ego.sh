#!/bin/bash
# 捕获 EgoPlanner 崩溃输出和 core dump
LOG=/tmp/ego_capture.log
EXEC=/root/ego_ws/install/ego_planner/lib/ego_planner/ego_planner_node

. /opt/ros/humble/setup.bash
. /root/ego_ws/install/setup.bash
export ROS_LOCALHOST=1
export DISPLAY=:99

# 启用 core dump
ulimit -c unlimited
echo "|/bin/bash -c 'cat > /tmp/core.\$1.\$2.%e'" > /proc/sys/kernel/core_pattern 2>/dev/null || true
rm -f /tmp/core.* 2>/dev/null

echo "=== Starting EgoPlanner at $(date) ===" > $LOG
echo "PID=$$" >> $LOG

# 运行 EgoPlanner
$EXEC --ros-args \
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
    -p fsm/flight_type:=1 \
    -p fsm/realworld_experiment:=true >> $LOG 2>&1

EXIT_CODE=$?
echo "EXIT_CODE=$EXIT_CODE" >> $LOG
echo "=== Finished at $(date) ===" >> $LOG
echo "---core files---" >> $LOG
ls -la /tmp/core.* 2>/dev/null >> $LOG

# 如果有 core 文件，用 gdb 分析
CORE_FILE=$(ls /tmp/core.* 2>/dev/null | head -1)
if [ -n "$CORE_FILE" ]; then
    echo "=== GDB Backtrace ===" >> $LOG
    gdb -batch -ex "bt" -ex "info threads" --args $EXEC $CORE_FILE >> $LOG 2>&1
fi
