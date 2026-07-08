#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import Pose
from moveit_msgs.srv import GetCartesianPath
from moveit_msgs.msg import RobotState
from control_msgs.action import FollowJointTrajectory
from sensor_msgs.msg import JointState
import numpy as np


class WipeActionNode(Node):
    def __init__(self):
        super().__init__('wipe_action_node')

        self.declare_parameter('cylinder_center', [0.20, 0.0, 0.15])
        self.declare_parameter('cylinder_axis', [0.0, 1.0, 0.0])
        self.declare_parameter('cylinder_radius', 0.03)
        self.declare_parameter('approach_offset', 0.02)
        self.declare_parameter('approach_direction', [0.0, 0.0, -1.0])
        self.declare_parameter('wipe_length', 0.15)
        self.declare_parameter('cycles', 1)
        self.declare_parameter('eef_step', 0.005)
        self.declare_parameter('group_name', 'manipulator')

        self.joint_names = [
            'joint_1', 'joint_2', 'joint_3',
            'joint_4', 'joint_5', 'joint_6'
        ]
        self.current_joint_positions = [0.0] * 6

        self.joint_state_sub = self.create_subscription(
            JointState, '/joint_states', self.joint_state_callback, 10
        )

        self.cartesian_cli = self.create_client(
            GetCartesianPath, '/compute_cartesian_path'
        )
        self.trajectory_client = ActionClient(
            self, FollowJointTrajectory,
            '/joint_trajectory_controller/follow_joint_trajectory'
        )

        self.get_logger().info('Waiting for /compute_cartesian_path service...')
        self.cartesian_cli.wait_for_service(timeout_sec=10.0)
        self.get_logger().info('Service available')

        self.get_logger().info('Waiting for FollowJointTrajectory action server...')
        self.trajectory_client.wait_for_server(timeout_sec=10.0)
        self.get_logger().info('Action server available')

        self.timer = self.create_timer(3.0, self.on_timer)

    def joint_state_callback(self, msg):
        for i, name in enumerate(self.joint_names):
            if name in msg.name:
                idx = msg.name.index(name)
                self.current_joint_positions[i] = msg.position[idx]

    def on_timer(self):
        self.timer.cancel()
        self.execute_wipe()

    def rot_matrix_to_quaternion(self, R):
        trace = np.trace(R)
        if trace > 0.0:
            s = 0.5 / np.sqrt(trace + 1.0)
            w = 0.25 / s
            x = (R[2, 1] - R[1, 2]) * s
            y = (R[0, 2] - R[2, 0]) * s
            z = (R[1, 0] - R[0, 1]) * s
        elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            w = (R[2, 1] - R[1, 2]) / s
            x = 0.25 * s
            y = (R[0, 1] + R[1, 0]) / s
            z = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            w = (R[0, 2] - R[2, 0]) / s
            x = (R[0, 1] + R[1, 0]) / s
            y = 0.25 * s
            z = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            w = (R[1, 0] - R[0, 1]) / s
            x = (R[0, 2] + R[2, 0]) / s
            y = (R[1, 2] + R[2, 1]) / s
            z = 0.25 * s
        return (x, y, z, w)

    def generate_waypoints(self):
        center = np.array(self.get_parameter('cylinder_center').value, dtype=float)
        axis = np.array(self.get_parameter('cylinder_axis').value, dtype=float)
        axis = axis / np.linalg.norm(axis)

        radius = float(self.get_parameter('cylinder_radius').value)
        offset = float(self.get_parameter('approach_offset').value)
        length = float(self.get_parameter('wipe_length').value)
        cycles = int(self.get_parameter('cycles').value)
        eef_step = float(self.get_parameter('eef_step').value)
        steps = max(2, int(length / eef_step))

        approach_dir = np.array(
            self.get_parameter('approach_direction').value, dtype=float
        )
        approach_dir = approach_dir / np.linalg.norm(approach_dir)

        normal = approach_dir - np.dot(approach_dir, axis) * axis
        norm_len = np.linalg.norm(normal)
        if norm_len < 1e-6:
            temp = np.array([0.0, 0.0, 1.0])
            if abs(np.dot(axis, temp)) > 0.99:
                temp = np.array([0.0, 1.0, 0.0])
            normal = np.cross(axis, temp)
            normal = normal / np.linalg.norm(normal)
        else:
            normal = normal / norm_len

        distance = radius + offset
        base_pos = center + normal * distance

        # 末端朝向：Z 轴指向 -normal（接触表面方向）
        # 用 approach_direction 作为末端 Z 轴方向
        end_z = -normal
        end_x = axis
        end_y = np.cross(end_z, end_x)
        end_y = end_y / np.linalg.norm(end_y)
        # 重新正交化 end_x
        end_x = np.cross(end_y, end_z)
        end_x = end_x / np.linalg.norm(end_x)

        rot_matrix = np.zeros((3, 3))
        rot_matrix[:, 0] = end_x
        rot_matrix[:, 1] = end_y
        rot_matrix[:, 2] = end_z

        qx, qy, qz, qw = self.rot_matrix_to_quaternion(rot_matrix)
        self.get_logger().info(
            f'base_pos={base_pos.tolist()}, quat=({qx:.4f},{qy:.4f},{qz:.4f},{qw:.4f})'
        )

        def make_pose(pos):
            p = Pose()
            p.position.x = float(pos[0])
            p.position.y = float(pos[1])
            p.position.z = float(pos[2])
            p.orientation.x = qx
            p.orientation.y = qy
            p.orientation.z = qz
            p.orientation.w = qw
            return p

        waypoints = []
        for c in range(cycles):
            # 起点：圆柱表面接触点
            waypoints.append(make_pose(base_pos))

            # 去程：沿轴线前进 length/2
            for i in range(1, steps + 1):
                t = i * (length / 2.0) / steps
                pos = base_pos + axis * t
                waypoints.append(make_pose(pos))

            # 回程：回到 base_pos
            for i in range(1, steps + 1):
                t = (length / 2.0) - i * (length / 2.0) / steps
                pos = base_pos + axis * t
                waypoints.append(make_pose(pos))
        return waypoints

    def execute_wipe(self):
        self.get_logger().info('Generating wipe waypoints...')
        waypoints = self.generate_waypoints()
        self.get_logger().info(f'Generated {len(waypoints)} waypoints')

        req = GetCartesianPath.Request()
        req.group_name = self.get_parameter('group_name').value

        robot_state = RobotState()
        robot_state.joint_state.name = self.joint_names
        robot_state.joint_state.position = self.current_joint_positions
        req.start_state = robot_state

        req.waypoints = waypoints
        req.max_step = float(self.get_parameter('eef_step').value)
        req.jump_threshold = 0.0
        req.avoid_collisions = True
        req.link_name = 'tool_link'

        self.get_logger().info('Calling /compute_cartesian_path...')
        future = self.cartesian_cli.call_async(req)
        future.add_done_callback(self.cartesian_path_callback)

    def cartesian_path_callback(self, future):
        try:
            resp = future.result()
        except Exception as e:
            self.get_logger().error(f'Service call failed: {e}')
            return

        if resp is None:
            self.get_logger().error('Service response is None')
            return

        if resp.fraction < 0.99:
            self.get_logger().error(
                f'Cartesian path planning failed: {resp.fraction * 100:.1f}%'
            )
            return

        self.get_logger().info(
            f'Cartesian path planned ({resp.fraction * 100:.1f}%), executing...'
        )

        traj = resp.solution.joint_trajectory
        goal = FollowJointTrajectory.Goal()
        goal.trajectory = traj

        self.get_logger().info('Sending trajectory goal...')
        send_goal_future = self.trajectory_client.send_goal_async(goal)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        try:
            goal_handle = future.result()
        except Exception as e:
            self.get_logger().error(f'Send goal failed: {e}')
            return

        if not goal_handle.accepted:
            self.get_logger().error('Trajectory goal rejected')
            return

        self.get_logger().info('Trajectory goal accepted, waiting for result...')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def result_callback(self, future):
        try:
            result = future.result()
        except Exception as e:
            self.get_logger().error(f'Get result failed: {e}')
            return

        if result.result.error_code == 0:
            self.get_logger().info('Wipe action completed successfully')
        else:
            self.get_logger().error(
                f'Trajectory execution failed with error code: {result.result.error_code}'
            )


def main(args=None):
    rclpy.init(args=args)
    node = WipeActionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
