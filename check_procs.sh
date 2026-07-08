#!/bin/bash
ps aux | grep -E "rgb_depth|rtabmap|realsense|v4l2" | grep -v grep
