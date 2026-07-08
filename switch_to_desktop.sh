#!/bin/bash
# 关闭之前在虚拟显示 :99 上启动的 x11vnc/Xvfb/rviz2
# 改为在地瓜派真实桌面 :0 上启动 rviz2

# 杀掉我之前启动的 x11vnc (绑定 :99 的那个)
for pid in $(pgrep -x x11vnc); do
  kill -9 "$pid" 2>/dev/null
done

# 杀掉 Xvfb 虚拟显示
for pid in $(pgrep -x Xvfb); do
  kill -9 "$pid" 2>/dev/null
done

# 杀掉旧 rviz2 (在 :99 上运行的)
for pid in $(pgrep -x rviz2); do
  kill -9 "$pid" 2>/dev/null
done

sleep 1

echo "=== Cleaned up my virtual display services ==="
echo "Remaining VNC (yours, on :0):"
pgrep -af 'vnc|Xorg' | head -10
echo ""
echo "=== Port 5900 (should be free now) ==="
ss -tlnp 2>/dev/null | grep 5900 || echo "5900 is free"

