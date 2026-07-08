#!/usr/bin/env python3
"""通过 rtabmap/octomap_binary 服务获取并保存八叉树地图."""
import rclpy
from rclpy.node import Node
from octomap_msgs.srv import GetOctomap
import sys


def main():
    rclpy.init()
    node = Node("octomap_saver")
    cli = node.create_client(GetOctomap, "/rtabmap/octomap_binary")

    fname = sys.argv[1] if len(sys.argv) > 1 else "octomap.ot"

    node.get_logger().info("等待 /rtabmap/octomap_binary 服务...")
    if not cli.wait_for_service(timeout_sec=10.0):
        node.get_logger().error("服务不可用")
        rclpy.shutdown()
        return

    node.get_logger().info("请求 octomap 数据...")
    future = cli.call_async(GetOctomap.Request())
    rclpy.spin_until_future_complete(node, future)

    if future.result() is None:
        node.get_logger().error(f"服务调用失败: {future.exception()}")
        rclpy.shutdown()
        return

    resp = future.result()
    msg = resp.map
    node.get_logger().info(
        f"收到 octomap: id={msg.id}, res={msg.resolution:.3f}m, "
        f"binary={msg.binary}, frame={msg.header.frame_id}, "
        f"data={len(msg.data)} bytes"
    )

    try:
        with open(fname, "wb") as f:
            f.write(msg.data)
        node.get_logger().info(f"已保存: {fname}")
    except Exception as e:
        node.get_logger().error(f"保存失败: {e}")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
