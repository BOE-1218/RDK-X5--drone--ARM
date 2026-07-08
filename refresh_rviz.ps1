$ip = "192.168.51.252"
ssh "root@$ip" "export DISPLAY=:99; import -window root /tmp/rviz_screenshot.png"
scp "root@${ip}:/tmp/rviz_screenshot.png" "e:\ros2_working_place\rviz_screenshot.png"
Invoke-Item "e:\ros2_working_place\rviz_screenshot.png"
