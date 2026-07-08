#!/usr/bin/env python3
"""Save OccupancyGrid map to PGM + YAML."""
import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
import sys
import time

rclpy.init()
node = Node('map_saver_py')
msg_recv = [None]

def cb(msg):
    msg_recv[0] = msg

sub = node.create_subscription(OccupancyGrid, '/map', cb,
                               rclpy.qos.qos_profile_parameters)
start = time.time()
while msg_recv[0] is None and time.time() - start < 10:
    rclpy.spin_once(node, timeout_sec=0.1)

if msg_recv[0]:
    m = msg_recv[0]
    w, h = m.info.width, m.info.height
    out_path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/slam_map2'
    with open(out_path + '.pgm', 'wb') as f:
        f.write(f'P5\n{w} {h}\n255\n'.encode())
        for v in m.data:
            if v == 0:
                f.write(bytes([0]))
            elif v == 100:
                f.write(bytes([254]))
            else:
                f.write(bytes([205]))
    with open(out_path + '.yaml', 'w') as f:
        f.write(f'image: {out_path.split("/")[-1]}.pgm\n')
        f.write(f'resolution: {m.info.resolution}\n')
        ox = m.info.origin.position.x
        oy = m.info.origin.position.y
        oz = m.info.origin.position.z
        f.write(f'origin: [{ox}, {oy}, {oz}]\n')
        f.write('negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.25\n')
    print(f'Saved: {w}x{h}, origin=({ox:.2f},{oy:.2f})')
else:
    print('NO MAP RECEIVED')

node.destroy_node()
rclpy.shutdown()
