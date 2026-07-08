#!/bin/bash
# 完整建图与路径规划管线启动脚本
# 启动顺序: RealSense -> TF -> depth_odom -> OctoMap -> EgoPlanner
. /opt/ros/humble/setup.bash
. /root/ego_ws/install/setup.bash
export ROS_LOCALHOST=1

LOG=/tmp/pipeline_start.log
echo "=== Pipeline Start $(date) ===" > $LOG

# 1. 启动 RealSense 相机
echo "[1/6] Starting RealSense D430..." | tee -a $LOG
nohup bash /tmp/start_cameras3.sh > /tmp/camera.log 2>&1 &
sleep 8

# 检查相机是否发布深度图
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
if timeout 3 ros2 topic echo /camera/camera/depth/image_rect_raw --once > /dev/null 2>&1; then
    echo "  Camera OK" | tee -a $LOG
else
    echo "  Camera FAILED - check /tmp/camera.log" | tee -a $LOG
fi

# 2. 启动 TF (map->odom)
echo "[2/6] Starting TF publisher..." | tee -a $LOG
nohup bash /tmp/start_tf.sh > /tmp/tf.log 2>&1 &
sleep 2

# 3. 启动 depth_odom.py
echo "[3/6] Starting depth_odom.py..." | tee -a $LOG
chmod +x /tmp/depth_odom.py
nohup python3 /tmp/depth_odom.py > /tmp/depth_odom.log 2>&1 &
sleep 6

# 检查 odom
if timeout 3 ros2 topic echo /odom --once > /dev/null 2>&1; then
    echo "  depth_odom OK" | tee -a $LOG
else
    echo "  depth_odom FAILED - check /tmp/depth_odom.log" | tee -a $LOG
fi

# 4. 启动 OctoMap
echo "[4/6] Starting OctoMap..." | tee -a $LOG
nohup bash /tmp/start_octomap.sh > /tmp/octomap.log 2>&1 &
sleep 4

# 检查点云
if timeout 3 ros2 topic echo /camera/depth/points --once > /dev/null 2>&1; then
    echo "  PointCloud OK" | tee -a $LOG
else
    echo "  PointCloud FAILED" | tee -a $LOG
fi

# 5. 启动 EgoPlanner
echo "[5/6] Starting EgoPlanner..." | tee -a $LOG
nohup bash /tmp/start_ego.sh > /tmp/ego_planner.log 2>&1 &
sleep 8

# 检查 occupancy
OCC=$(timeout 3 ros2 topic echo /grid_map/occupancy --once 2>/dev/null | grep -c 'width:')
if [ "$OCC" -gt 0 ]; then
    echo "  EgoPlanner OK (occupancy received)" | tee -a $LOG
else
    echo "  EgoPlanner started, waiting for occupancy..." | tee -a $LOG
fi

# 6. 启动 rviz2 (在真实桌面 :0)
echo "[6/6] Starting rviz2 on desktop..." | tee -a $LOG
export DISPLAY=:0
export XAUTHORITY=/home/sunrise/.Xauthority
for pid in $(pgrep -x rviz2); do kill -9 "$pid" 2>/dev/null; done
sleep 1
nohup rviz2 -d /tmp/pointcloud.rviz > /tmp/rviz2.log 2>&1 &
sleep 4

echo "" | tee -a $LOG
echo "=== All services started ===" | tee -a $LOG
echo "Processes:" | tee -a $LOG
pgrep -af 'realsense|depth_odom|octomap|ego_planner|rviz2|static_transform' | grep -v grep | tee -a $LOG
echo "" | tee -a $LOG
echo "Topics:" | tee -a $LOG
ros2 topic list | grep -E 'depth|points|occupancy|odom|octomap' | sort | tee -a $LOG

