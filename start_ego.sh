#!/bin/bash
# 启动 EgoPlanner 与 OctoMap 管线集成
# 输入话题 (来自 depth_odom.py):
#   /odom                          - 视觉里程计 (nav_msgs/Odometry)
#   /camera/camera/depth/image_rect_raw - 深度图 (16UC1, mm)
#   /camera/depth/points           - 点云 (sensor_msgs/PointCloud2)
. /opt/ros/humble/setup.bash
. /root/ego_ws/install/setup.bash
export ROS_LOCALHOST=1

# 相机内参 (来自 RealSense D430 depth camera_info)
FX=382.08209228515625
FY=382.08209228515625
CX=322.40570068359375
CY=234.64114379882812

# 地图大小 (与 octomap 一致)
MAP_X=10.0
MAP_Y=10.0
MAP_Z=3.0

ros2 run ego_planner ego_planner_node \
    --ros-args \
    -r grid_map/odom:=/odom \
    -r grid_map/depth:=/camera/camera/depth/image_rect_raw \
    -r grid_map/cloud:=/camera/depth/points \
    -r odom_world:=/odom \
    -p grid_map/frame_id:=odom \
    -p grid_map/resolution:=0.1 \
    -p grid_map/map_size_x:=$MAP_X \
    -p grid_map/map_size_y:=$MAP_Y \
    -p grid_map/map_size_z:=$MAP_Z \
    -p grid_map/local_update_range_x:=5.0 \
    -p grid_map/local_update_range_y:=5.0 \
    -p grid_map/local_update_range_z:=3.0 \
    -p grid_map/obstacles_inflation:=0.199 \
    -p grid_map/local_map_margin:=5 \
    -p grid_map/ground_height:=-1.5 \
    -p grid_map/cx:=$CX \
    -p grid_map/cy:=$CY \
    -p grid_map/fx:=$FX \
    -p grid_map/fy:=$FY \
    -p grid_map/use_depth_filter:=true \
    -p grid_map/depth_filter_tolerance:=0.15 \
    -p grid_map/depth_filter_maxdist:=5.0 \
    -p grid_map/depth_filter_mindist:=0.5 \
    -p grid_map/depth_filter_margin:=2 \
    -p grid_map/k_depth_scaling_factor:=1000.0 \
    -p grid_map/skip_pixel:=2 \
    -p grid_map/p_hit:=0.65 \
    -p grid_map/p_miss:=0.35 \
    -p grid_map/p_min:=0.12 \
    -p grid_map/p_max:=0.90 \
    -p grid_map/p_occ:=0.80 \
    -p grid_map/min_ray_length:=0.1 \
    -p grid_map/max_ray_length:=4.5 \
    -p grid_map/virtual_ceil_height:=2.9 \
    -p grid_map/visualization_truncate_height:=2.0 \
    -p grid_map/show_occ_time:=false \
    -p grid_map/pose_type:=2 \
    -p fsm/flight_type:=1 \
    -p fsm/thresh_replan_time:=1.0 \
    -p fsm/thresh_no_replan_meter:=1.0 \
    -p fsm/planning_horizon:=7.5 \
    -p fsm/planning_horizen_time:=3.0 \
    -p fsm/emergency_time:=1.0 \
    -p fsm/realworld_experiment:=true \
    -p fsm/fail_safe:=true \
    -p fsm/waypoint_num:=1 \
    -p fsm/waypoint0_x:=2.0 \
    -p fsm/waypoint0_y:=0.0 \
    -p fsm/waypoint0_z:=1.0 \
    -p manager/max_vel:=1.0 \
    -p manager/max_acc:=2.0 \
    -p manager/max_jerk:=4.0 \
    -p manager/control_points_distance:=0.4 \
    -p manager/feasibility_tolerance:=0.05 \
    -p manager/planning_horizon:=7.5 \
    -p manager/use_distinctive_trajs:=true \
    -p manager/drone_id:=0 \
    -p optimization/lambda_smooth:=1.0 \
    -p optimization/lambda_collision:=0.5 \
    -p optimization/lambda_feasibility:=0.1 \
    -p optimization/lambda_fitness:=1.0 \
    -p optimization/dist0:=0.5 \
    -p optimization/swarm_clearance:=0.5 \
    -p optimization/max_vel:=1.0 \
    -p optimization/max_acc:=2.0 \
    -p bspline/limit_vel:=1.0 \
    -p bspline/limit_acc:=2.0 \
    -p bspline/limit_ratio:=1.1 \
    -p prediction/obj_num:=0 \
    -p prediction/lambda:=1.0 \
    -p prediction/predict_rate:=1.0
