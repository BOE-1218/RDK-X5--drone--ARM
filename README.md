# 🚁 无人机自主除冰清障系统

第九届嵌入式大赛项目 🏆，RDK X5 极致易用的机器人开发平台赛道。

## 📖 项目简介

本项目是一套面向高压输电线路的无人机自主除冰清障系统，以 RDK X5 边缘计算平台为大脑 🧠，将四旋翼无人机与六轴轻量化机械臂集成到同一空中平台。

❄️ 冬季覆冰与异物悬挂是输电线路面临的两大顽疾。覆冰会改变导线张力分布，严重时诱发断线、倒塔；而飘挂的塑料膜、风筝、鸟巢等异物又可能引发短路跳闸。传统处置依赖人工登塔，作业窗口短、高处坠落风险高，一次出动往往耗费数小时。本系统尝试把这部分工作交给无人机，从发现问题到处理问题，都在空中完成 ✈️。

## 🏗️ 技术架构

系统基于 OpenClaw 多智能体架构，由大语言模型负责任务解析，ROS 2 DDS 实现飞行控制与机械臂控制的实时协同 🤖。

### 👁️ 感知层

感知端采用 YOLOv8 完成覆冰与异物识别，DehazeFormer 去雾网络保障雾雪天气下的图像质量，点云视觉建图则为机械臂提供三维空间基准 📷。

### 🔧 执行层

末端执行器支持链锯式除冰机构与柔性随形夹爪的快换，可在三秒内切换作业模式 ⚡。

### 🔋 续航方案

系统引入线路感应取能方案。由机械臂辅助安装分裂式磁芯取能模块，经 MPPT 电路与谐振式无线传输向机载电池补能，在 250 A 输电条件下可实现 22 W 充电功率，缓解无人机续航焦虑 🔌。

### 💬 交互层

运维人员通过飞书频道以自然语言直接下达任务，系统解析后自主规划航线、抵近目标、执行操作，全过程保留遥控器人工接管通道，以双保险机制确保近电作业安全 🛡️。

## 📁 仓库结构

```
.
├── config/         ⚙️ 配置文件与 RViz 配置
├── launch/         🚀 各模块启动脚本
│   ├── start_camera.sh          📷 摄像头启动
│   ├── start_depth_odom.sh      📏 深度视觉里程计
│   ├── start_octomap.sh         🗺️ OctoMap 建图
│   ├── start_fusion.sh          🌈 RGB-D 融合
│   ├── start_ego.sh             🧭 EgoPlanner 路径规划
│   └── start_all_pipeline.sh    ▶️ 完整管线一键启动
├── odometry/       📍 里程计模块
│   ├── depth_odom.py            📏 深度图视觉里程计
│   ├── scan_odom.py             📡 激光扫描里程计（2D ICP）
│   ├── keyboard_odom.py         ⌨️ 键盘遥控里程计
│   ├── remote_odom.py           📡 远程控制里程计
│   └── monitor_odom.py          📊 里程计监控
├── perception/     👁️ 感知模块
│   ├── rgb_depth_fusion.py      🌈 RGB + Depth 彩色点云融合
│   ├── check_depth.py           ✅ 深度图质量检查
│   └── check_sync.py            🔄 多传感器同步检查
├── mapping/        🗺️ 建图模块
│   ├── save_map.py              💾 occupancy grid 地图保存
│   ├── save_octomap.py          💾 OctoMap 保存
│   ├── viz_map.py               📊 地图可视化
│   └── map_controller.py        🎮 建图遥控控制器
├── planning/       🧭 规划模块（EgoPlanner）
│   ├── start_ego.sh             🚀 EgoPlanner 启动
│   ├── debug_ego.sh             🐛 调试脚本
│   └── build_ego.sh             🔨 编译脚本
├── tools/          🛠️ 工具脚本
│   ├── check_ros.sh             ✅ ROS 2 环境检查
│   ├── check_topics.sh          📋 话题检查
│   ├── kill_all.sh              💀 一键清理进程
│   └── probe_px4.sh             🔍 PX4 飞控探测
├── test_debug/     🧪 测试与调试
│   ├── test_remote.sh           🔗 远程连接测试
│   ├── restart_pipeline.sh      🔄 管线重启
│   └── debug_sync.sh            🐛 同步调试
├── utils/          🧰 通用工具
│   ├── gen_checkerboard.py      📐 标定板生成
│   └── screenshot.py            📸 截图工具
└── src/            📦 ROS 2 源码包（保持 colcon 工作空间结构）
    ├── aerial_control/          ✈️ 飞控节点
    ├── niryo_bot/               🤖 机械臂描述与可视化
    ├── niryo_bot_control/       🎮 机械臂控制
    └── niryo_moveit_config/     🦾 MoveIt 配置
```

## 🚀 快速开始

### 📋 环境要求

* RDK X5 开发板
* ROS 2 Humble
* RealSense D430 深度相机
* YDLIDAR X2 激光雷达

### ▶️ 启动完整管线

```bash
bash launch/start_all_pipeline.sh
```

### 🔧 单独启动各模块

```bash
# 1. 📷 摄像头
bash launch/start_camera.sh

# 2. 📏 深度视觉里程计
bash launch/start_depth_odom.sh

# 3. 🌈 RGB-D 点云融合
bash launch/start_fusion.sh

# 4. 🗺️ OctoMap 建图
bash launch/start_octomap.sh

# 5. 🧭 EgoPlanner 路径规划
bash launch/start_ego.sh
```

## 🌍 应用场景

除核心输电线路场景外，该平台的空中作业能力还可向以下方向延伸：

* 🌬️ 风机叶片除冰
* 🚄 铁路接触网运维
* 🏗️ 市政高空设施维护

为低空经济时代的电力基础设施智能运维提供一套可参考的端到端方案 💡。

## 👥 团队

第九届嵌入式大赛参赛项目 🏆
