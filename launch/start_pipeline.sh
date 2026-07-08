#!/bin/bash
# 统一启动脚本: TF + 摄像头 + 里程计 + 彩色点云 + OctoMap
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1

echo "=== 1. TF ==="
bash /tmp/start_tf.sh &
sleep 2

echo "=== 2. Cameras ==="
bash /tmp/start_cameras.sh &
sleep 5

echo "=== 3. RGB-D Odometry ==="
bash /tmp/start_odom.sh &
sleep 3

echo "=== 4. Color PointCloud Fusion ==="
python3 /tmp/rgb_depth_fusion.py &
sleep 3

echo "=== 5. OctoMap ==="
bash /tmp/start_octomap.sh &
sleep 2

echo "=== All services started ==="
echo "Topics:"
ros2 topic list | grep -E "color_points|octomap|odom|image_raw|depth"
echo "TF:"
ros2 run tf2_ros tf2_echo map camera_link 2>&1 | head -5 &
sleep 2
kill %1 2>/dev/null
wait
