#!/usr/bin/env python3
"""
本地建图控制器.
通过 SSH 向远程发送 odom_cmd 命令, 控制虚拟位姿移动.

操作说明:
  W: 前进 0.2m
  S: 后退 0.2m
  A: 左转 15度
  D: 右转 15度
  Q: 左平移 0.2m
  E: 右平移 0.2m
  R: 重置位姿 (重启 remote_odom)
  M: 保存地图
  V: 刷新 rviz 截图
  H: 显示帮助
  ESC: 退出
"""
import subprocess
import sys
import time
import msvcrt

REMOTE = "root@192.168.51.252"
ROS_ENV = "source /opt/ros/humble/setup.bash; export ROS_DOMAIN_ID=0; export ROS_IP=192.168.51.252"


def get_key():
    """使用 msvcrt 读取键盘 (Windows)."""
    if msvcrt.kbhit():
        ch = msvcrt.getch()
        try:
            return ch.decode('utf-8', errors='ignore')
        except Exception:
            return ''
    return None


def send_cmd(linear_x=0.0, linear_y=0.0, angular_z=0.0):
    """发送 odom_cmd 命令到远程."""
    cmd = (f'ssh {REMOTE} "{ROS_ENV}; '
           f'ros2 topic pub --once /odom_cmd geometry_msgs/Twist '
           f"'{{linear: {{x: {linear_x}, y: {linear_y}}}, "
           f"angular: {{z: {angular_z}}}}}'\"")
    subprocess.run(cmd, shell=True, capture_output=True, timeout=5)


def save_map():
    """保存地图."""
    print("Saving map...")
    cmd = f'ssh {REMOTE} "{ROS_ENV}; python3 /tmp/save_map.py /tmp/slam_map_final"'
    subprocess.run(cmd, shell=True, capture_output=True, timeout=15)
    # 下载到本地
    subprocess.run(f'scp {REMOTE}:/tmp/slam_map_final.pgm e:/ros2_working_place/slam_map_final.pgm',
                   shell=True, capture_output=True)
    subprocess.run(f'scp {REMOTE}:/tmp/slam_map_final.yaml e:/ros2_working_place/slam_map_final.yaml',
                   shell=True, capture_output=True)
    # 生成 PNG
    cmd = f'ssh {REMOTE} "python3 /tmp/viz_map.py /tmp/slam_map_final.pgm"'
    subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
    subprocess.run(f'scp {REMOTE}:/tmp/slam_map_final.png e:/ros2_working_place/slam_map_final.png',
                   shell=True, capture_output=True)
    print("Map saved to e:/ros2_working_place/slam_map_final.png")
    subprocess.run('start e:/ros2_working_place/slam_map_final.png', shell=True)


def refresh_rviz():
    """刷新 rviz 截图."""
    print("Refreshing rviz screenshot...")
    cmd = f'ssh {REMOTE} "export DISPLAY=:99; import -window root /tmp/rviz_screenshot.png"'
    subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
    subprocess.run(f'scp {REMOTE}:/tmp/rviz_screenshot.png e:/ros2_working_place/rviz_screenshot.png',
                   shell=True, capture_output=True)
    subprocess.run('start e:/ros2_working_place/rviz_screenshot.png', shell=True)


def reset_pose():
    """重置位姿."""
    print("Resetting pose...")
    subprocess.run(f'ssh {REMOTE} "systemctl restart remote_odom"', shell=True, capture_output=True)
    subprocess.run(f'ssh {REMOTE} "systemctl restart slam_toolbox"', shell=True, capture_output=True)
    time.sleep(3)
    print("Pose and SLAM reset.")


def show_help():
    """显示帮助."""
    print("""
=== 建图控制器 ===
  W: 前进 0.2m
  S: 后退 0.2m
  A: 左转 15度
  D: 右转 15度
  Q: 左平移 0.2m
  E: 右平移 0.2m
  R: 重置位姿和地图
  M: 保存地图
  V: 刷新 rviz 截图
  H: 显示帮助
  ESC: 退出
=================
""")


def main():
    print("=" * 50)
    print("建图控制器已启动")
    print("按 H 显示帮助, 按 ESC 退出")
    print("=" * 50)

    while True:
        try:
            key = get_key()
            if key is None:
                time.sleep(0.05)
                continue

            if key == '\x1b':  # ESC
                print("退出")
                break
            key_lower = key.lower()

            if key_lower == 'w':
                print("前进 0.2m")
                send_cmd(linear_x=0.2)
            elif key_lower == 's':
                print("后退 0.2m")
                send_cmd(linear_x=-0.2)
            elif key_lower == 'a':
                print("左转 15度")
                send_cmd(angular_z=0.2618)
            elif key_lower == 'd':
                print("右转 15度")
                send_cmd(angular_z=-0.2618)
            elif key_lower == 'q':
                print("左平移 0.2m")
                send_cmd(linear_y=0.2)
            elif key_lower == 'e':
                print("右平移 0.2m")
                send_cmd(linear_y=-0.2)
            elif key_lower == 'r':
                reset_pose()
            elif key_lower == 'm':
                save_map()
            elif key_lower == 'v':
                refresh_rviz()
            elif key_lower == 'h':
                show_help()

        except KeyboardInterrupt:
            print("\n退出")
            break
        except Exception as e:
            print(f"错误: {e}")


if __name__ == '__main__':
    main()
