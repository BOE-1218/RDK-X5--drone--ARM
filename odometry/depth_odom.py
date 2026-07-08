#!/usr/bin/env python3
"""
深度图视觉里程计 + 点云发布.
使用深度图的灰度化版本进行 ORB 特征匹配 + SVD 运动估计.
不需要 RGB 或红外图, 只需要深度图.

输入: /camera/camera/depth/image_rect_raw (16UC1, 单位 mm)
      /camera/camera/depth/camera_info
输出: odom -> base_link 动态 TF (body 坐标系: x前, y左, z上)
      base_link -> camera_depth_optical_frame 静态 TF
      /odom 话题 (body 坐标系位姿, 供 EgoPlanner 使用)
      /camera/depth/points (PointCloud2, XYZ 点云, optical 坐标系)

说明: EgoPlanner 的 grid_map.cpp 中 cam2body_ 矩阵将 optical 转为 body,
其 depthOdomCallback 执行 cam_T = body2world * cam2body_.
因此 /odom 必须是 body 坐标系位姿, 否则 cam2body_ 会被错误地双重应用.
内部 T_accum 仍为 optical 坐标系位姿 (深度点天然在 optical 坐标系),
发布时通过 T_body = T_accum @ inv(cam2body_) 转换为 body 坐标系.
"""
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
from sensor_msgs.msg import Image, CameraInfo, PointCloud2, PointField
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from cv_bridge import CvBridge
import cv2
import numpy as np
import math
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

# cam2body_ 矩阵 (与 EgoPlanner grid_map.cpp 一致)
# 作用: 将 optical 坐标系点转换为 body 坐标系点
# optical (x右, y下, z前) -> body (x前, y左, z上)
# body_x = optical_z, body_y = -optical_x, body_z = -optical_y
CAM2BODY = np.array([
    [0.0, 0.0, 1.0, 0.0],
    [-1.0, 0.0, 0.0, 0.0],
    [0.0, -1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]
], dtype=np.float64)
# inv(CAM2BODY): body 坐标系位姿 -> optical 坐标系位姿
# 由于是纯旋转, 逆等于转置
CAM2BODY_INV = np.linalg.inv(CAM2BODY)


class DepthVisualOdom(Node):
    def __init__(self):
        super().__init__('depth_visual_odom')

        self.bridge = CvBridge()
        self.depth_msg = None
        self.last_depth_stamp = None
        self.prev_gray = None
        self.prev_depth = None
        self.prev_kp = None
        self.prev_desc = None

        # 用 4x4 齐次变换矩阵累积位姿 (optical 坐标系)
        # T_world_camera: 相机在 odom 坐标系下的位姿
        self.T_accum = np.eye(4, dtype=np.float64)

        # 相机内参
        self.fx = 0.0
        self.fy = 0.0
        self.cx = 0.0
        self.cy = 0.0

        # QoS: 匹配 RealSense 的 TRANSIENT_LOCAL
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )

        self.depth_sub = self.create_subscription(
            Image, '/camera/camera/depth/image_rect_raw', self.depth_callback, qos)
        self.info_sub = self.create_subscription(
            CameraInfo, '/camera/camera/depth/camera_info', self.info_callback, 10)

        # /odom 用普通 QoS 发布 (body 坐标系位姿, 供 EgoPlanner 使用)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        # 点云发布 (BEST_EFFORT, VOLATILE 兼容 octomap_server)
        self.pc_pub = self.create_publisher(PointCloud2, '/camera/depth/points', 10)
        self.tf_broadcaster = None
        self.static_tf_broadcaster = None
        try:
            from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster
            self.tf_broadcaster = TransformBroadcaster(self)
            self.static_tf_broadcaster = StaticTransformBroadcaster(self)
            self.publish_static_tf()
        except ImportError:
            self.get_logger().error('tf2_ros not available')

        # 回调组: 里程计计算 (耗时) 和发布 (快速) 分开
        self.odom_cb_group = MutuallyExclusiveCallbackGroup()
        self.pub_cb_group = MutuallyExclusiveCallbackGroup()

        # 里程计计算定时器 (5 Hz, 处理时间长, 用低频避免阻塞)
        self.odom_timer = self.create_timer(0.2, self.process_odom, callback_group=self.odom_cb_group)
        # TF 发布定时器 (10 Hz, 独立于里程计计算, 确保稳定发布)
        self.tf_timer = self.create_timer(0.1, self.publish_tf, callback_group=self.pub_cb_group)
        # 点云发布定时器 (2 Hz, 降低 octomap 负载)
        self.pc_timer = self.create_timer(0.5, self.publish_pc, callback_group=self.pub_cb_group)
        self.frame_count = 0
        self.latest_depth_m = None  # 最新深度图 (numpy 数组)
        self.get_logger().info('DepthVisualOdom started. Waiting for depth data...')

    def info_callback(self, msg):
        if self.fx == 0.0:
            k = np.array(msg.k).reshape(3, 3)
            self.fx = k[0, 0]
            self.fy = k[1, 1]
            self.cx = k[0, 2]
            self.cy = k[1, 2]
            self.get_logger().info(
                f'Camera intrinsics: fx={self.fx}, fy={self.fy}, cx={self.cx}, cy={self.cy}')

    def depth_callback(self, msg):
        self.depth_msg = msg
        # 缓存最新深度图 (转 numpy, 供 publish_all 使用)
        if self.fx > 0.0:
            try:
                depth_cv = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
                self.latest_depth_m = depth_cv.astype(np.float32) * 0.001  # mm -> m
            except Exception:
                pass

    def publish_tf(self):
        """TF 发布定时器: 稳定发布 odom TF (10 Hz)
        使用最新深度图的时间戳, 确保 odom 与 depth 时间戳一致 (message_filters 同步)
        """
        if self.depth_msg is None or self.fx == 0.0:
            return
        self.publish_odom(self.depth_msg.header.stamp)

    def publish_pc(self):
        """点云发布定时器 (2 Hz, 降低 octomap 负载)
        用深度图时间戳发布 TF 和点云, 确保与 depth 完全同步
        """
        if self.depth_msg is None or self.fx == 0.0 or self.latest_depth_m is None:
            return
        # 用深度图时间戳, 与 /camera/camera/depth/image_rect_raw 时间戳一致
        stamp = self.depth_msg.header.stamp
        self.publish_odom(stamp)
        self.publish_pointcloud(self.latest_depth_m, stamp)

    def process_odom(self):
        """里程计计算 (5 Hz, 处理时间长)"""
        if self.depth_msg is None or self.fx == 0.0:
            return

        # 避免重复处理同一帧
        stamp = self.depth_msg.header.stamp
        if self.last_depth_stamp is not None and stamp == self.last_depth_stamp:
            return
        self.last_depth_stamp = stamp

        try:
            depth_cv = self.bridge.imgmsg_to_cv2(self.depth_msg, desired_encoding='passthrough')
        except Exception as e:
            self.get_logger().error(f'CVBridge error: {e}')
            return

        # 深度图转灰度图 (归一化到 0-255 + 直方图均衡化增强纹理)
        depth_m = depth_cv.astype(np.float32) * 0.001  # mm -> m
        valid = (depth_m > 0.1) & (depth_m < 5.0)
        gray = np.zeros_like(depth_m, dtype=np.uint8)
        if valid.any():
            dmin = depth_m[valid].min()
            dmax = depth_m[valid].max()
            if dmax > dmin:
                gray[valid] = ((depth_m[valid] - dmin) / (dmax - dmin) * 255).astype(np.uint8)
                # 直方图均衡化增强纹理 (只在有效区域)
                eq = cv2.equalizeHist(gray)
                gray = np.where(valid, eq, 0)

        # ORB 特征 (增加数量以支持旋转场景)
        orb = cv2.ORB_create(nfeatures=500)
        kp, desc = orb.detectAndCompute(gray, None)

        if desc is None or len(kp) < 5:
            self.prev_gray = gray
            self.prev_depth = depth_m
            self.prev_kp = kp
            self.prev_desc = desc
            return

        if self.prev_desc is not None and len(self.prev_kp) >= 5:
            # BFMatcher 匹配
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(self.prev_desc, desc)
            matches = sorted(matches, key=lambda m: m.distance)[:80]

            if len(matches) >= 5:
                prev_pts3d = []
                curr_pts3d = []
                for m in matches:
                    pt_prev = self.prev_kp[m.queryIdx].pt
                    pt_curr = kp[m.trainIdx].pt

                    d_prev = self.prev_depth[int(pt_prev[1]), int(pt_prev[0])]
                    d_curr = depth_m[int(pt_curr[1]), int(pt_curr[0])]

                    if 0.1 < d_prev < 5.0 and 0.1 < d_curr < 5.0:
                        # 反投影到 3D (optical 坐标系: x右, y下, z前)
                        x_prev = (pt_prev[0] - self.cx) * d_prev / self.fx
                        y_prev = (pt_prev[1] - self.cy) * d_prev / self.fy
                        z_prev = d_prev

                        x_curr = (pt_curr[0] - self.cx) * d_curr / self.fx
                        y_curr = (pt_curr[1] - self.cy) * d_curr / self.fy
                        z_curr = d_curr

                        prev_pts3d.append([x_prev, y_prev, z_prev])
                        curr_pts3d.append([x_curr, y_curr, z_curr])

                if len(prev_pts3d) >= 5:
                    prev_pts3d = np.array(prev_pts3d, dtype=np.float64)
                    curr_pts3d = np.array(curr_pts3d, dtype=np.float64)

                    # 用 cv2.estimateAffine3D (内置 RANSAC) 估计 R, t
                    # 比 SVD 更鲁棒, 能过滤外点
                    retval, M, inliers = cv2.estimateAffine3D(
                        prev_pts3d, curr_pts3d,
                        ransacThreshold=0.05,  # 5cm (旋转场景下放宽)
                        confidence=0.99
                    )

                    if retval and M is not None:
                        R = M[:3, :3]
                        t = M[:3, 3]

                        # 检查 R 是否为有效旋转矩阵
                        det_R = np.linalg.det(R)
                        if abs(det_R - 1.0) > 0.1:
                            # 无效旋转, 跳过
                            pass
                        else:
                            # 鲁棒性: 检查 R 和 t 是否合理
                            angle = math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2)))
                            trans_norm = np.linalg.norm(t)
                            n_inliers = int(inliers.sum()) if inliers is not None else 0

                            # 静止检测: 位移 < 0.02m 且旋转 < 1度, 认为静止
                            is_static = (trans_norm < 0.02 and angle < 0.017)

                            # 运动检测: 位移 < 0.5m 且旋转 < 0.7rad (40度) 且内点 >= 5
                            # 放宽阈值以支持快速转动相机
                            if is_static or (trans_norm < 0.5 and angle < 0.7 and n_inliers >= 5):
                                T_delta = np.eye(4, dtype=np.float64)
                                T_delta[:3, :3] = R
                                T_delta[:3, 3] = t

                                # M = T_prev->curr (cv2.estimateAffine3D(src=prev, dst=curr) returns M: dst = M @ src)
                                # 相机位姿累积: T_world_curr = T_world_prev @ inv(T_prev->curr)
                                self.T_accum = self.T_accum @ np.linalg.inv(T_delta)

                                # 重新正交化旋转矩阵, 防止数值漂移导致四元数非归一化
                                U, _, Vt = np.linalg.svd(self.T_accum[:3, :3])
                                R_ortho = U @ Vt
                                if np.linalg.det(R_ortho) < 0:
                                    R_ortho = U @ np.diag([1, 1, -1]) @ Vt
                                self.T_accum[:3, :3] = R_ortho

                                self.frame_count += 1
                                if self.frame_count % 10 == 0:
                                    pos = self.T_accum[:3, 3]
                                    self.get_logger().info(
                                        f'Odom: pos=({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}) '
                                        f'inliers={n_inliers}/{len(prev_pts3d)} '
                                        f'delta_t={trans_norm:.4f} delta_r={math.degrees(angle):.2f}deg')
                            else:
                                if self.frame_count % 30 == 0:
                                    self.get_logger().warn(
                                        f'Rejected motion: delta_t={trans_norm:.3f} '
                                        f'delta_r={math.degrees(angle):.2f}deg '
                                        f'inliers={n_inliers}/{len(prev_pts3d)}')

        self.prev_gray = gray
        self.prev_depth = depth_m
        self.prev_kp = kp
        self.prev_desc = desc

    def publish_pointcloud(self, depth_m, stamp=None):
        """将深度图转为 PointCloud2 并发布 (降采样: 每隔 4 像素)"""
        if stamp is None:
            stamp = self.get_clock().now().to_msg()

        h, w = depth_m.shape
        # 降采样: 每隔 4 个像素
        step = 4
        sub_depth = depth_m[::step, ::step]
        sub_h, sub_w = sub_depth.shape

        # 生成像素坐标网格
        u = (np.arange(sub_w) * step).astype(np.float32)
        v = (np.arange(sub_h) * step).astype(np.float32)
        uu, vv = np.meshgrid(u, v)

        valid = (sub_depth > 0.1) & (sub_depth < 5.0)
        if not valid.any():
            return

        z = sub_depth[valid].astype(np.float32)
        x = ((uu[valid] - self.cx) * z / self.fx).astype(np.float32)
        y = ((vv[valid] - self.cy) * z / self.fy).astype(np.float32)

        points = np.stack([x, y, z], axis=-1)

        # 构建 PointCloud2
        pc2 = PointCloud2()
        pc2.header.stamp = stamp
        pc2.header.frame_id = 'camera_depth_optical_frame'
        pc2.height = 1
        pc2.width = len(points)
        pc2.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        pc2.is_bigendian = False
        pc2.point_step = 12
        pc2.row_step = 12 * len(points)
        pc2.data = points.tobytes()
        pc2.is_dense = True
        self.pc_pub.publish(pc2)

    def publish_static_tf(self):
        """发布静态 TF: base_link -> camera_depth_optical_frame
        base_link (body: x前, y左, z上) 与 camera_depth_optical_frame (optical: x右, y下, z前) 的关系
        由 CAM2BODY 矩阵定义 (旋转, 无平移)
        """
        if self.static_tf_broadcaster is None:
            return
        tf = TransformStamped()
        tf.header.stamp = self.get_clock().now().to_msg()
        tf.header.frame_id = 'base_link'
        tf.child_frame_id = 'camera_depth_optical_frame'
        # CAM2BODY 的旋转部分: optical -> body
        # 静态 TF 需要 body -> optical, 即 CAM2BODY 的逆
        R = CAM2BODY_INV[:3, :3]
        tf.transform.translation.x = 0.0
        tf.transform.translation.y = 0.0
        tf.transform.translation.z = 0.0
        # 旋转矩阵 -> 四元数
        qw, qx, qy, qz = self.rotation_to_quaternion(R)
        tf.transform.rotation.w = qw
        tf.transform.rotation.x = qx
        tf.transform.rotation.y = qy
        tf.transform.rotation.z = qz
        self.static_tf_broadcaster.sendTransform(tf)

    @staticmethod
    def rotation_to_quaternion(R):
        """旋转矩阵 -> 四元数 (w, x, y, z)"""
        trace = np.trace(R)
        if trace > 0:
            S = math.sqrt(trace + 1.0) * 2
            qw = 0.25 * S
            qx = (R[2, 1] - R[1, 2]) / S
            qy = (R[0, 2] - R[2, 0]) / S
            qz = (R[1, 0] - R[0, 1]) / S
        elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            S = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
            qw = (R[2, 1] - R[1, 2]) / S
            qx = 0.25 * S
            qy = (R[0, 1] + R[1, 0]) / S
            qz = (R[0, 2] + R[2, 0]) / S
        elif R[1, 1] > R[2, 2]:
            S = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
            qw = (R[0, 2] - R[2, 0]) / S
            qx = (R[0, 1] + R[1, 0]) / S
            qy = 0.25 * S
            qz = (R[1, 2] + R[2, 1]) / S
        else:
            S = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
            qw = (R[1, 0] - R[0, 1]) / S
            qx = (R[0, 2] + R[2, 0]) / S
            qy = (R[1, 2] + R[2, 1]) / S
            qz = 0.25 * S
        return float(qw), float(qx), float(qy), float(qz)

    def publish_odom(self, stamp=None):
        # 用当前时间, 确保 TF 和 odom 时间戳一致
        if stamp is None:
            stamp = self.get_clock().now().to_msg()

        # 内部 T_accum 是 optical 坐标系位姿
        # 转换为 body 坐标系位姿: T_body = T_optical @ inv(CAM2BODY)
        T_body = self.T_accum @ CAM2BODY_INV

        # 从 4x4 矩阵提取位姿
        R = T_body[:3, :3]
        t = T_body[:3, 3]

        qw, qx, qy, qz = self.rotation_to_quaternion(R)

        # 发布动态 TF: odom -> base_link (body 坐标系)
        if self.tf_broadcaster:
            tf = TransformStamped()
            tf.header.stamp = stamp
            tf.header.frame_id = 'odom'
            tf.child_frame_id = 'base_link'
            tf.transform.translation.x = float(t[0])
            tf.transform.translation.y = float(t[1])
            tf.transform.translation.z = float(t[2])
            tf.transform.rotation.w = qw
            tf.transform.rotation.x = qx
            tf.transform.rotation.y = qy
            tf.transform.rotation.z = qz
            self.tf_broadcaster.sendTransform(tf)

        # 发布 Odometry 话题 (body 坐标系位姿, 供 EgoPlanner 使用)
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = float(t[0])
        odom.pose.pose.position.y = float(t[1])
        odom.pose.pose.position.z = float(t[2])
        odom.pose.pose.orientation.w = qw
        odom.pose.pose.orientation.x = qx
        odom.pose.pose.orientation.y = qy
        odom.pose.pose.orientation.z = qz
        self.odom_pub.publish(odom)


def main():
    rclpy.init()
    node = DepthVisualOdom()
    # 用多线程 executor, 确保里程计计算不会阻塞 TF/点云发布
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
