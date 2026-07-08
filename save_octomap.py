#!/usr/bin/env python3
"""订阅 /octomap_binary 话题并保存为 .ot 文件."""
import rclpy
from rclpy.node import Node
from octomap_msgs.msg import Octomap
import struct


class OctomapSaver(Node):
    def __init__(self, filename="octomap.ot"):
        super().__init__("octomap_saver")
        self.filename = filename
        self.sub = self.create_subscription(Octomap, "/octomap_binary", self.cb, 1)
        self.get_logger().info(f"等待 /octomap_binary 消息, 将保存到 {filename}")
        self.received = False

    def cb(self, msg):
        if self.received:
            return
        self.received = True
        self.get_logger().info(f"收到 octomap: id={msg.id}, res={msg.resolution:.3f}m, "
                               f"data_len={len(msg.data)} bytes, frame={msg.header.frame_id}")
        try:
            with open(self.filename, "wb") as f:
                f.write(msg.data)
            self.get_logger().info(f"已保存: {self.filename}")
        except Exception as e:
            self.get_logger().error(f"保存失败: {e}")
        rclpy.shutdown()


def main():
    rclpy.init()
    import sys
    fname = sys.argv[1] if len(sys.argv) > 1 else "octomap.ot"
    node = OctomapSaver(fname)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
