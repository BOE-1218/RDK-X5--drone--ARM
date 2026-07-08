import rclpy
from rclpy.node import Node
from moveit_msgs.srv import GetPositionIK
from moveit_msgs.msg import PositionIKRequest
from geometry_msgs.msg import PoseStamped

rclpy.init()
node = Node("ik_test")
cli = node.create_client(GetPositionIK, "/compute_ik")
cli.wait_for_service(timeout_sec=5.0)

req = GetPositionIK.Request()
ik = PositionIKRequest()
ik.group_name = "manipulator"
ik.ik_link_name = "tool_link"

p = PoseStamped()
p.header.frame_id = "base_link"
p.pose.position.x = 0.20
p.pose.position.y = 0.20
p.pose.position.z = 0.15

# 末端 Z 轴指向 -Z（从上向下接触圆柱）
# R: X=axis=[0,-1,0], Z=-normal=[0,0,1], Y=cross(Z,X)
# R = [[0, 1, 0], [1, 0, 0], [0, 0, 1]] -> quat
p.pose.orientation.x = 0.7071
p.pose.orientation.y = 0.0
p.pose.orientation.z = 0.0
p.pose.orientation.w = 0.7071
ik.pose_stamped = p
req.ik_request = ik

future = cli.call_async(req)
rclpy.spin_until_future_complete(node, future)
resp = future.result()
if resp and resp.solution:
    print("IK SUCCESS", list(resp.solution.joint_state.position))
else:
    print("IK FAILED", resp.error_code.val if resp else "no response")
rclpy.shutdown()
