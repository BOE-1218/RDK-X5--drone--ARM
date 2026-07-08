#!/usr/bin/env python3
"""
Scan matching odometry using 2D ICP with motion consistency check.
通过运动一致性检测区分真实运动和噪声漂移.

原理:
- 噪声导致的位移方向随机, 累积位移小
- 真实运动方向一致, 累积位移大
- 维护最近 N 帧的位移向量, 计算累积位移
- 只有累积位移超过阈值且方向一致时才更新位姿
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
import numpy as np
from scipy.spatial import cKDTree
import math
from collections import deque


def scan_to_points(scan, range_min=0.3, range_max=2.5):
    """Convert LaserScan to 2D point array (x, y)."""
    angles = np.arange(scan.angle_min, scan.angle_max + scan.angle_increment * 0.5,
                       scan.angle_increment)
    ranges = np.array(scan.ranges)
    mask = np.isfinite(ranges) & (ranges > range_min) & (ranges < range_max)
    if not np.any(mask):
        return np.empty((0, 2))
    r = ranges[mask]
    a = angles[mask]
    x = r * np.cos(a)
    y = r * np.sin(a)
    return np.column_stack([x, y])


def icp_2d(source, target, max_iter=20, tol=1e-3, dist_threshold=0.2):
    """
    2D ICP: find transform (dx, dy, dtheta) that aligns source to target.
    Returns: (dx, dy, dtheta, match_ratio, mean_error)
    """
    if len(source) < 10 or len(target) < 10:
        return 0.0, 0.0, 0.0, 0.0, float('inf')

    src = source.copy()
    tree = cKDTree(target)

    dx, dy, dtheta = 0.0, 0.0, 0.0
    prev_error = float('inf')
    n_valid = 0

    for _ in range(max_iter):
        cos_t = math.cos(dtheta)
        sin_t = math.sin(dtheta)
        transformed = src.copy()
        transformed[:, 0] = src[:, 0] * cos_t - src[:, 1] * sin_t + dx
        transformed[:, 1] = src[:, 0] * sin_t + src[:, 1] * cos_t + dy

        dists, indices = tree.query(transformed, k=1)
        valid = dists < dist_threshold
        n_valid = np.sum(valid)
        if n_valid < 5:
            break

        matched_src = transformed[valid]
        matched_tgt = target[indices[valid]]

        src_centroid = matched_src.mean(axis=0)
        tgt_centroid = matched_tgt.mean(axis=0)

        src_centered = matched_src - src_centroid
        tgt_centered = matched_tgt - tgt_centroid

        H = src_centered.T @ tgt_centered
        U, _, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T

        dtheta_new = math.atan2(R[1, 0], R[0, 0])

        dx_new = tgt_centroid[0] - (src_centroid[0] * math.cos(dtheta_new) -
                                     src_centroid[1] * math.sin(dtheta_new))
        dy_new = tgt_centroid[1] - (src_centroid[0] * math.sin(dtheta_new) +
                                     src_centroid[1] * math.cos(dtheta_new))

        new_dx = dx * math.cos(dtheta_new) - dy * math.sin(dtheta_new) + dx_new
        new_dy = dx * math.sin(dtheta_new) + dy * math.cos(dtheta_new) + dy_new
        dx, dy = new_dx, new_dy
        dtheta += dtheta_new

        mean_error = dists[valid].mean()
        if abs(prev_error - mean_error) < tol:
            break
        prev_error = mean_error

    match_ratio = n_valid / len(source) if len(source) > 0 else 0.0
    return dx, dy, dtheta, match_ratio, prev_error


class ScanOdomNode(Node):
    def __init__(self):
        super().__init__('scan_odom_node')

        # Parameters
        self.declare_parameter('scan_topic', '/scan')
        self.declare_parameter('frame_id', 'camera_link')
        self.declare_parameter('odom_frame_id', 'odom')
        self.declare_parameter('range_min', 0.3)
        self.declare_parameter('range_max', 2.5)
        self.declare_parameter('dist_threshold', 0.2)
        self.declare_parameter('publish_tf', True)
        self.declare_parameter('min_points', 30)
        # 运动一致性检测参数
        self.declare_parameter('motion_window', 10)  # 检测窗口大小
        self.declare_parameter('min_accumulated_translation', 0.1)  # 累积位移阈值
        self.declare_parameter('min_direction_consistency', 0.5)  # 方向一致性阈值
        self.declare_parameter('max_single_translation', 0.1)  # 单帧最大位移
        self.declare_parameter('max_single_rotation', 0.3)  # 单帧最大旋转
        # 双阈值: 噪声阈值 (低于此值肯定是噪声) 和 运动阈值 (高于此值肯定是运动)
        self.declare_parameter('noise_threshold', 0.015)  # 噪声阈值
        self.declare_parameter('motion_threshold', 0.05)  # 运动阈值

        scan_topic = self.get_parameter('scan_topic').value
        self.frame_id = self.get_parameter('frame_id').value
        self.odom_frame_id = self.get_parameter('odom_frame_id').value
        self.range_min = self.get_parameter('range_min').value
        self.range_max = self.get_parameter('range_max').value
        self.dist_threshold = self.get_parameter('dist_threshold').value
        self.publish_tf = self.get_parameter('publish_tf').value
        self.min_points = self.get_parameter('min_points').value
        self.motion_window = self.get_parameter('motion_window').value
        self.min_accum_trans = self.get_parameter('min_accumulated_translation').value
        self.min_consistency = self.get_parameter('min_direction_consistency').value
        self.max_single_trans = self.get_parameter('max_single_translation').value
        self.max_single_rot = self.get_parameter('max_single_rotation').value
        self.noise_threshold = self.get_parameter('noise_threshold').value
        self.motion_threshold = self.get_parameter('motion_threshold').value

        # State
        self.ref_points = None
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.frame_count = 0
        self.last_log_time = 0.0

        # 运动历史记录 (用于一致性检测)
        self.motion_history = deque(maxlen=self.motion_window)
        # 待确认的位移累积
        self.pending_dx = 0.0
        self.pending_dy = 0.0
        self.pending_dtheta = 0.0

        # Publishers
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # Subscriber
        self.scan_sub = self.create_subscription(
            LaserScan, scan_topic, self.scan_callback, 10)

        self.get_logger().info(
            f'ScanOdomNode started: scan={scan_topic}, '
            f'window={self.motion_window}, '
            f'min_accum={self.min_accum_trans}, '
            f'consistency={self.min_consistency}')

    def scan_callback(self, msg):
        curr_points = scan_to_points(msg, self.range_min, self.range_max)

        if len(curr_points) < self.min_points:
            return

        if self.ref_points is None:
            self.ref_points = curr_points.copy()
            self.get_logger().info('First scan received, initializing')
            return

        # ICP matching
        dx, dy, dtheta, match_ratio, mean_err = icp_2d(
            curr_points, self.ref_points,
            max_iter=20, dist_threshold=self.dist_threshold)

        translation = math.sqrt(dx * dx + dy * dy)

        # 双阈值策略
        # 1. 单帧位移过大, 直接丢弃 (匹配失败)
        if translation > self.max_single_trans or abs(dtheta) > self.max_single_rot:
            self.motion_history.clear()
            self.pending_dx = 0.0
            self.pending_dy = 0.0
            self.pending_dtheta = 0.0
            self.ref_points = curr_points.copy()
            self.publish_odom(msg.header.stamp)
            return

        # 2. 单帧位移小于噪声阈值, 认为是噪声, 丢弃但不重置 pending
        if translation < self.noise_threshold and abs(dtheta) < (self.noise_threshold / 5):
            # 噪声, 不累积
            self.publish_odom(msg.header.stamp)
            return

        # 3. 单帧位移大于运动阈值, 直接认为是运动
        if translation > self.motion_threshold:
            cos_t = math.cos(self.theta)
            sin_t = math.sin(self.theta)
            self.x += dx * cos_t - dy * sin_t
            self.y += dx * sin_t + dy * cos_t
            self.theta += dtheta
            self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
            self.motion_history.clear()
            self.pending_dx = 0.0
            self.pending_dy = 0.0
            self.pending_dtheta = 0.0
            self.ref_points = curr_points.copy()
            self.publish_odom(msg.header.stamp)
            return

        # 4. 中间值, 累积判断
        # 记录运动向量
        self.motion_history.append((dx, dy, dtheta))

        # 累积 pending 位移
        self.pending_dx += dx
        self.pending_dy += dy
        self.pending_dtheta += dtheta

        # 运动一致性检测
        should_update = False
        if len(self.motion_history) >= self.motion_window:
            accum_dx = sum(m[0] for m in self.motion_history)
            accum_dy = sum(m[1] for m in self.motion_history)
            accum_trans = math.sqrt(accum_dx ** 2 + accum_dy ** 2)

            if accum_trans > self.min_accum_trans:
                if accum_trans > 1e-6:
                    unit_x = accum_dx / accum_trans
                    unit_y = accum_dy / accum_trans
                    consistent_count = 0
                    for mx, my, _ in self.motion_history:
                        m_trans = math.sqrt(mx * mx + my * my)
                        if m_trans > 1e-6:
                            dot = (mx * unit_x + my * unit_y) / m_trans
                            if dot > 0:
                                consistent_count += 1
                    consistency = consistent_count / len(self.motion_history)

                    if consistency > self.min_consistency:
                        should_update = True

        if should_update:
            # 确认是真实运动, 更新位姿
            cos_t = math.cos(self.theta)
            sin_t = math.sin(self.theta)
            self.x += self.pending_dx * cos_t - self.pending_dy * sin_t
            self.y += self.pending_dx * sin_t + self.pending_dy * cos_t
            self.theta += self.pending_dtheta
            self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

            # 重置 pending 和 history
            self.motion_history.clear()
            self.pending_dx = 0.0
            self.pending_dy = 0.0
            self.pending_dtheta = 0.0

            # 更新参考点云
            self.ref_points = curr_points.copy()
        else:
            # 未确认运动, 但更新参考点云 (避免参考过旧)
            # 只在 pending 位移较小时更新参考
            pending_trans = math.sqrt(self.pending_dx ** 2 + self.pending_dy ** 2)
            if pending_trans < self.min_accum_trans * 0.5:
                self.ref_points = curr_points.copy()

        # 发布 odom
        self.publish_odom(msg.header.stamp)

        # 周期性日志
        self.frame_count += 1
        now_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if now_sec - self.last_log_time > 5.0:
            self.last_log_time = now_sec
            status = 'MOVING' if should_update else 'STATIC'
            self.get_logger().info(
                f'frame={self.frame_count}, status={status}, '
                f'match_ratio={match_ratio:.2f}, '
                f'single_trans={translation:.3f}m, '
                f'pending_trans={math.sqrt(self.pending_dx**2+self.pending_dy**2):.3f}m, '
                f'pose=({self.x:.2f},{self.y:.2f},{math.degrees(self.theta):.1f}deg)')

    def publish_odom(self, stamp):
        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = stamp
            t.header.frame_id = self.odom_frame_id
            t.child_frame_id = self.frame_id
            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation.z = math.sin(self.theta / 2.0)
            t.transform.rotation.w = math.cos(self.theta / 2.0)
            self.tf_broadcaster.sendTransform(t)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame_id
        odom.child_frame_id = self.frame_id
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.z = math.sin(self.theta / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.theta / 2.0)
        odom.pose.covariance[0] = 0.01
        odom.pose.covariance[7] = 0.01
        odom.pose.covariance[35] = 0.05
        self.odom_pub.publish(odom)


def main():
    rclpy.init()
    node = ScanOdomNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
