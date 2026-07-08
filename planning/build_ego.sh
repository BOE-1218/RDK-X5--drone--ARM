#!/bin/bash
# 编译 EgoPlanner ROS 2 版本
# 来源: ZJU-FAST-Lab/ego-planner-swarm (ros2_version 分支)
. /opt/ros/humble/setup.bash

# 安装依赖
sudo apt update
sudo apt install -y libarmadillo-dev ros-humble-rmw-cyclonedds-cpp

# 克隆仓库
mkdir -p /root/ego_ws/src
cd /root/ego_ws/src
if [ ! -d ego-planner-swarm ]; then
    git clone -b ros2_version https://github.com/ZJU-FAST-Lab/ego-planner-swarm.git
fi

# 编译
cd /root/ego_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --parallel-workers 2

echo "=== EgoPlanner build complete ==="
source /root/ego_ws/install/setup.bash
ros2 pkg list | grep ego
