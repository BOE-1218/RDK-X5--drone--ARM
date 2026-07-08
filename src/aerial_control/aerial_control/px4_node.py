#!/usr/bin/env python3
"""PX4 飞控 ROS2 控制节点

通过 USB 转串口连接 PX4 飞控，基于 MAVLink 协议提供：
- 心跳维持与连接状态管理
- 状态发布：~/state (JSON 字符串)，~/battery (电压)，~/odom (本地 NED 位置)
- 服务：~/arm (arm/disarm)，~/offboard (切 OFFBOARD / 退回 HOLD)
- 订阅：~/cmd/vel (Twist，linear=NED 速度 m/s，angular.z=yaw rate rad/s)

坐标系说明：本地位置与速度均使用 PX4 默认的 NED (North-East-Down) 坐标系，
使用者在 ROS 端若需 ENU 需自行转换。
"""

import json
import math
import queue
import threading
import time
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy

from std_msgs.msg import String, Float32
from std_srvs.srv import SetBool
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

try:
    from pymavlink import mavutil
except ImportError:
    mavutil = None


# PX4 自定义模式编码：custom_mode 高 16 位为主模式
PX4_MAIN_MODE_MANUAL = 1
PX4_MAIN_MODE_ALTCTL = 2
PX4_MAIN_MODE_POSCTL = 3
PX4_MAIN_MODE_AUTO = 4
PX4_MAIN_MODE_ACRO = 5
PX4_MAIN_MODE_OFFBOARD = 6
PX4_MAIN_MODE_STABILIZED = 7
PX4_MAIN_MODE_RATTITUDE = 8

PX4_MAIN_MODE_NAMES = {
    PX4_MAIN_MODE_MANUAL: 'MANUAL',
    PX4_MAIN_MODE_ALTCTL: 'ALTCTL',
    PX4_MAIN_MODE_POSCTL: 'POSCTL',
    PX4_MAIN_MODE_AUTO: 'AUTO',
    PX4_MAIN_MODE_ACRO: 'ACRO',
    PX4_MAIN_MODE_OFFBOARD: 'OFFBOARD',
    PX4_MAIN_MODE_STABILIZED: 'STABILIZED',
    PX4_MAIN_MODE_RATTITUDE: 'RATTITUDE',
}

PX4_AUTO_SUB_MODE_HOLD = 3
PX4_AUTO_SUB_MODE_NAMES = {
    PX4_AUTO_SUB_MODE_HOLD: 'HOLD',
}


def px4_custom_mode(main_mode: int, sub_mode: int = 0) -> int:
    """构造 PX4 custom_mode 值：低 16 位 sub_mode，高 16 位 main_mode"""
    return (main_mode & 0xFFFF) << 16 | (sub_mode & 0xFFFF)


def decode_px4_mode(custom_mode: int) -> str:
    """从 custom_mode 解析出模式名"""
    main_mode = (custom_mode >> 16) & 0xFFFF
    sub_mode = custom_mode & 0xFFFF
    name = PX4_MAIN_MODE_NAMES.get(main_mode, f'MODE_{main_mode}')
    if main_mode == PX4_MAIN_MODE_AUTO:
        sub_name = PX4_AUTO_SUB_MODE_NAMES.get(sub_mode, f'SUB_{sub_mode}')
        return f'{name}.{sub_name}'
    return name


class PX4ControlNode(Node):
    """PX4 飞控控制节点，独立线程收发 MAVLink，主线程跑 ROS spin"""

    def __init__(self):
        super().__init__('px4_control_node')

        # 参数声明
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 921600)
        self.declare_parameter('target_system', 1)
        self.declare_parameter('target_component', 1)
        self.declare_parameter('cmd_rate', 10.0)
        self.declare_parameter('cmd_vel_timeout', 1.0)
        self.declare_parameter('reconnect_period', 3.0)

        self.port = self.get_parameter('port').value
        self.baudrate = self.get_parameter('baudrate').value
        self.target_system = self.get_parameter('target_system').value
        self.target_component = self.get_parameter('target_component').value
        self.cmd_rate = float(self.get_parameter('cmd_rate').value)
        self.cmd_vel_timeout = float(self.get_parameter('cmd_vel_timeout').value)
        self.reconnect_period = float(self.get_parameter('reconnect_period').value)

        # 运行时状态（受 _lock 保护）
        self._lock = threading.RLock()
        self._master = None
        self._connected = False
        self._armed = False
        self._custom_mode = 0
        self._mode_name = 'UNKNOWN'
        self._cmd_vel: Optional[Twist] = None
        self._cmd_vel_stamp = 0.0
        self._battery_voltage = float('nan')
        # ACK 等待队列: 接收线程把 COMMAND_ACK 放进来, 服务回调从这里取
        self._ack_queue: queue.Queue = queue.Queue(maxsize=8)

        # 话题发布者（odom/battery 用 BEST_EFFORT 适配飞控传感器流）
        sensor_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self._state_pub = self.create_publisher(String, '~/state', 10)
        self._odom_pub = self.create_publisher(Odometry, '~/odom', sensor_qos)
        self._battery_pub = self.create_publisher(Float32, '~/battery', sensor_qos)

        # 订阅与服务
        self.create_subscription(Twist, '~/cmd/vel', self._cmd_vel_cb, 10)
        self.create_service(SetBool, '~/arm', self._arm_cb)
        self.create_service(SetBool, '~/offboard', self._offboard_cb)

        # 启动收发线程
        self._running = True
        self._recv_thread = threading.Thread(
            target=self._recv_loop, name='mavlink-recv', daemon=True)
        self._cmd_thread = threading.Thread(
            target=self._cmd_loop, name='mavlink-cmd', daemon=True)
        self._recv_thread.start()
        self._cmd_thread.start()

        # 状态发布定时器（2 Hz）
        self.create_timer(0.5, self._publish_state)

        self.get_logger().info(
            f'PX4 节点启动 port={self.port} baud={self.baudrate} '
            f'cmd_rate={self.cmd_rate}Hz'
        )

    # ------------------------------------------------------------------ 连接
    def _connect(self) -> bool:
        if mavutil is None:
            self.get_logger().error(
                'pymavlink 未安装，请在地瓜派执行: pip install pymavlink')
            return False
        try:
            self._master = mavutil.mavlink_connection(
                self.port,
                baud=self.baudrate,
                dialect='common',
                autoreconnect=True,
            )
            self.get_logger().info('等待飞控心跳 (timeout=10s)...')
            hb = self._master.wait_heartbeat(timeout=10)
            if hb is None:
                self.get_logger().error('心跳超时，未收到飞控响应')
                self._connected = False
                return False
            with self._lock:
                self._connected = True
                # 用心跳包里的 sysid/compid 作为目标 (pymavlink 自动设的 target_component
                # 有时是 0, 会让飞控丢弃命令, 这里强制用 hb 里的 component)
                self.target_system = hb.get_srcSystem()
                self.target_component = hb.get_srcComponent()
                self._master.target_system = self.target_system
                self._master.target_component = self.target_component
            self.get_logger().info(
                f'已连接 PX4 sysid={self.target_system} '
                f'compid={self.target_component}')
            # 请求位置/姿态流（避免飞控默认不发送）
            self._request_streams()
            return True
        except Exception as e:
            self.get_logger().error(f'连接失败: {e}')
            with self._lock:
                self._connected = False
            return False

    def _request_streams(self):
        """请求飞控以一定频率发送常用消息"""
        if not self._master:
            return
        # PX4 默认会以配置好的频率发送常用消息, 这里补充请求 SYS_STATUS 与
        # BATTERY_STATUS (TELEM2 默认不发, 电池电压需要这个流)
        for msg_id in (
            mavutil.mavlink.MAVLINK_MSG_ID_SYS_STATUS,
            mavutil.mavlink.MAVLINK_MSG_ID_BATTERY_STATUS,
            mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED,
        ):
            try:
                self._master.mav.request_data_stream_send(
                    self.target_system, self.target_component,
                    msg_id, int(self.cmd_rate), 1)
            except Exception as e:
                self.get_logger().warning(f'请求流 {msg_id} 失败: {e}')

    # ------------------------------------------------------------------ 接收
    def _recv_loop(self):
        last_heartbeat = 0.0
        while self._running:
            with self._lock:
                connected = self._connected
            if not connected:
                if not self._connect():
                    time.sleep(self.reconnect_period)
                    continue
                last_heartbeat = time.time()
            try:
                msg = self._master.recv_match(blocking=True, timeout=1.0)
                if msg is None:
                    # 1 秒没消息, 检查心跳是否超时 (默认 5 秒)
                    if time.time() - last_heartbeat > 5.0:
                        self.get_logger().warning('心跳超时 5s, 标记为断线')
                        with self._lock:
                            self._connected = False
                    continue
                if msg.get_type() == 'HEARTBEAT':
                    last_heartbeat = time.time()
                # COMMAND_ACK 单独走队列给服务回调消费
                if msg.get_type() == 'COMMAND_ACK':
                    try:
                        self._ack_queue.put_nowait(msg)
                    except queue.Full:
                        # 队列满, 丢弃旧的 ACK
                        try:
                            self._ack_queue.get_nowait()
                            self._ack_queue.put_nowait(msg)
                        except queue.Empty:
                            pass
                    continue
                self._handle_msg(msg)
            except Exception as e:
                self.get_logger().error(f'接收异常: {e}')
                with self._lock:
                    self._connected = False
                time.sleep(self.reconnect_period)

    def _handle_msg(self, msg):
        mtype = msg.get_type()
        if mtype == 'HEARTBEAT':
            with self._lock:
                self._armed = bool(
                    msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                self._custom_mode = msg.custom_mode
                # PX4 1.14+ 心跳里 custom_mode 编码不再可靠, 改用 base_mode 位推断
                # 关键位: CUSTOM(1) + AUTO(4) + GUIDED(8) + STABILIZE(16) + ARMED(128)
                if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_AUTO_ENABLED:
                    if self._armed:
                        self._mode_name = 'AUTO.ARMED'
                    else:
                        self._mode_name = 'HOLD' if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_GUIDED_ENABLED else 'AUTO'
                elif msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_GUIDED_ENABLED:
                    self._mode_name = 'OFFBOARD' if self._armed else 'GUIDED'
                elif msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_STABILIZE_ENABLED:
                    self._mode_name = 'STABILIZED'
                else:
                    self._mode_name = 'MANUAL'
        elif mtype == 'SYS_STATUS':
            # SYS_STATUS 优先, 但 TELEM2 默认不发, 兜底走 HIGHRES_IMU
            v = msg.voltage_battery / 1000.0
            if v < 60.0:  # 过滤默认值 65535
                with self._lock:
                    self._battery_voltage = v
                self._battery_pub.publish(Float32(data=v))
        elif mtype == 'BATTERY_STATUS':
            # BATTERY_STATUS.voltages[0] 单位 mV, 0xFFFF 表示未用
            try:
                mv = msg.voltages[0]
            except Exception:
                mv = 0
            if 0 < mv < 60000:
                v = mv / 1000.0
                with self._lock:
                    self._battery_voltage = v
                self._battery_pub.publish(Float32(data=v))
        elif mtype == 'LOCAL_POSITION_NED':
            self._publish_odom(msg)
        elif mtype == 'ATTITUDE':
            # 当前 odom 不带姿态，可扩展补充；这里仅占位
            pass

    # ------------------------------------------------------------------ 发送
    def _cmd_loop(self):
        period = 1.0 / max(self.cmd_rate, 1.0)
        while self._running:
            with self._lock:
                connected = self._connected
                cmd = self._cmd_vel
                age = time.time() - self._cmd_vel_stamp
            if not connected:
                time.sleep(period)
                continue
            if cmd is not None and age < self.cmd_vel_timeout:
                self._send_velocity_setpoint(cmd)
            else:
                # 没有新命令时发送零速度悬停设定点，维持 OFFBOARD 活跃
                self._send_velocity_setpoint(Twist())
            time.sleep(period)

    def _send_velocity_setpoint(self, cmd: Twist):
        """发送 NED 速度 + yaw rate 设定点，body frame offset"""
        if not self._master:
            return
        # type_mask: 忽略位置/加速度/力/yaw，只发速度与 yaw_rate
        ignore = (
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_X_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_Y_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_Z_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_AX_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_AY_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_AZ_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_FORCE_SET |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_IGNORE
        )
        # 坐标系：BODY_OFFSET_NED (9) 适合机体速度控制
        frame = mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED
        try:
            self._master.mav.set_position_target_local_ned_send(
                0,  # time_boot_ms 由飞控自行处理
                self.target_system,
                self.target_component,
                frame,
                ignore,
                0.0, 0.0, 0.0,                                  # x, y, z
                float(cmd.linear.x), float(cmd.linear.y), float(cmd.linear.z),
                0.0, 0.0, 0.0,                                  # afx, afy, afz
                0.0,                                             # yaw
                float(cmd.angular.z),                            # yaw_rate
            )
        except Exception as e:
            self.get_logger().warning(f'发送速度设定点失败: {e}')

    # ------------------------------------------------------------------ 话题
    def _publish_odom(self, msg):
        """将 LOCAL_POSITION_NED 转为 nav_msgs/Odometry 发布"""
        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = 'odom_ned'
        odom.child_frame_id = 'base_link_ned'
        odom.pose.pose.position.x = float(msg.x)
        odom.pose.pose.position.y = float(msg.y)
        odom.pose.pose.position.z = float(msg.z)
        # 注意：本消息不含姿态，姿态信息走 ATTITUDE 消息，留空（quaternion identity）
        odom.pose.pose.orientation.w = 1.0
        odom.twist.twist.linear.x = float(msg.vx)
        odom.twist.twist.linear.y = float(msg.vy)
        odom.twist.twist.linear.z = float(msg.vz)
        self._odom_pub.publish(odom)

    def _publish_state(self):
        with self._lock:
            state = {
                'connected': self._connected,
                'armed': self._armed,
                'mode': self._mode_name,
                'custom_mode': self._custom_mode,
                'battery_v': self._battery_voltage,
            }
        self._state_pub.publish(String(data=json.dumps(state)))

    # ------------------------------------------------------------------ 回调
    def _cmd_vel_cb(self, msg: Twist):
        with self._lock:
            self._cmd_vel = msg
            self._cmd_vel_stamp = time.time()

    def _arm_cb(self, req, resp):
        if not self._master:
            resp.success = False
            resp.message = '未连接飞控'
            return resp
        try:
            cmd_id = (mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM
                      if req.data else
                      mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM)
            self._master.mav.command_long_send(
                self.target_system, self.target_component,
                cmd_id, 0,
                1.0 if req.data else 0.0,
                0, 0, 0, 0, 0, 0
            )
            # 同步等待结果: 从队列取 ACK (接收线程会放入)
            try:
                ack = self._ack_queue.get(timeout=3.0)
            except queue.Empty:
                ack = None
            if ack is None:
                resp.success = False
                resp.message = 'arm/disarm 超时无应答'
            elif ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                resp.success = True
                resp.message = 'arm' if req.data else 'disarm'
            else:
                resp.success = False
                resp.message = f'飞控拒绝 result={ack.result}'
        except Exception as e:
            resp.success = False
            resp.message = f'异常: {e}'
        self.get_logger().info(
            f'arm({req.data}) -> success={resp.success} msg={resp.message}')
        return resp

    def _offboard_cb(self, req, resp):
        if not self._master:
            resp.success = False
            resp.message = '未连接飞控'
            return resp
        # 进入 OFFBOARD 前必须先有持续的位置/速度设定点（_cmd_loop 已在发）
        target_main = PX4_MAIN_MODE_OFFBOARD if req.data else PX4_MAIN_MODE_AUTO
        target_sub = 0 if req.data else PX4_AUTO_SUB_MODE_HOLD
        custom_mode = px4_custom_mode(target_main, target_sub)
        try:
            self._master.mav.command_long_send(
                self.target_system, self.target_component,
                mavutil.mavlink.MAV_CMD_DO_SET_MODE,
                0,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                custom_mode,
                0, 0, 0, 0, 0
            )
            ack = None
            try:
                ack = self._ack_queue.get(timeout=3.0)
            except queue.Empty:
                pass
            if ack is None:
                resp.success = False
                resp.message = 'set_mode 超时无应答'
            elif ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                resp.success = True
                resp.message = 'OFFBOARD' if req.data else 'HOLD'
            else:
                resp.success = False
                resp.message = f'飞控拒绝 result={ack.result}'
        except Exception as e:
            resp.success = False
            resp.message = f'异常: {e}'
        self.get_logger().info(
            f'offboard({req.data}) -> success={resp.success} msg={resp.message}')
        return resp

    # ------------------------------------------------------------------ 关闭
    def destroy_node(self):
        self._running = False
        for t in (self._recv_thread, self._cmd_thread):
            if t.is_alive():
                t.join(timeout=2.0)
        if self._master:
            try:
                # 退出前 disarm 防止失控，但不强制（保留给上层决策）
                pass
            except Exception:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PX4ControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

