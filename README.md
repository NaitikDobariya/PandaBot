# PandaBot: Open-Source Modular Mobile Robot Platform

PandaBot is a 3D-printable, ROS 2-based differential drive mobile robot developed for robotics education, academic research, and algorithm benchmarking. It serves as an open-source alternative to commercial research platforms like the TurtleBot 3 Waffle and TurtleBot 4. By utilizing common off-the-shelf electronics and an FDM-printable chassis, the platform delivers comparable mapping and navigation capabilities at approximately 1/5th the hardware cost of its commercial equivalents.

The software stack runs natively on ROS 2 Humble and includes a fully configured Nav2 deployment, automated wheel PID tuning, and an exact-dimension Gazebo simulation environment for testing code before physical deployment.

<table style="width: 100%; border-collapse: collapse; border: none;">
  <tr>
    <td colspan="2" style="text-align: center; padding-bottom: 15px; border: none;">
      <video src="https://raw.githubusercontent.com/NaitikDobariya/Images/main/pandabot.mp4" autoplay loop muted playsinline style="width: 100%; max-width: 750px; height: auto; border-radius: 6px; box-shadow: 0 4px 8px rgba(0,0,0,0.15);"></video>
      <p style="margin-top: 6px; font-size: 0.85em; color: #666;"><i>PandaBot</i></p>
    </td>
  </tr>
  
  <tr>
    <td style="text-align: right; padding-right: 10px; border: none;">
      <img src="https://github.com/user-attachments/assets/c0ee372c-1c3c-460c-b902-d7ceb7ae9234" alt="PandaBot Mesh Model" style="height: 350px; width: auto; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
      <p style="margin-top: 8px; font-weight: bold; text-align: center;">PandaBot Mesh Model</p>
    </td>
    <td style="text-align: left; padding-left: 10px; border: none;">
      <img src="https://github.com/user-attachments/assets/f9faa77e-8a82-4ac8-b19b-063143543254" alt="PandaBot Hardware" style="height: 350px; width: auto; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
      <p style="margin-top: 8px; font-weight: bold; text-align: center;">PandaBot Hardware</p>
    </td>
  </tr>
</table>

---

## Salient Features

* **3D Printable & Open Source:** All structural decks, spacer columns, and sensor mounts are designed for standard FDM 3D printing. The design files are open-source, allowing full reproducibility and modification.
* **Modular Multi-Tier Architecture:** The chassis uses a stackable deck configuration with generic mounting grids. This design allows users to swap or add payloads, such as adding an Intel RealSense D455 depth camera or changing the LiDAR placement, without structural redesigns.
* **Dual-Compute Control Strategy:** High-level processing (ROS 2 Navigation stack, SLAM, and sensor drivers) runs on a Raspberry Pi 5. Deterministic low-level execution (encoder interrupt handling and closed-loop PID wheel velocity control) is handled by an Arduino Uno R3.
* **Plug-and-Play IMU Subsystem:** Integrates natively with the [VibeChecker](https://github.com/NaitikDobariya/VibeChecker) module, which pairs an external Raspberry Pi Pico with a BNO085 IMU to offload sensor fusion computations and stream stable 9-DOF telemetry over USB.
* **Sim-to-Real Consistency:** The included Gazebo simulation package replicates the physical robot's geometry, mass distribution, wheel kinematics, and sensor positions, ensuring that navigation behaviors match between simulation and reality.

## Repository Structure

```text
src/
├── robo_bringup      # Launch files for real hardware initialization and sensor nodes
├── robo_control      # ros2_control configuration and hardware interface bridges
├── robo_description  # URDF/Xacro kinematic profiles, physical mesh files, and STLs
├── robo_drivetrain   # Arduino firmware for PID wheel control and encoder reading
├── robo_gazebo       # Gazebo world files, launch setups, and physics configurations
├── robo_navigation   # Nav2 costmap configurations, planners, and SLAM parameters
├── sllidar_ros2      # Hardware driver for the SLAMTEC RPLIDAR A1M8
└── VibeChecker       # Firmware and ROS 2 driver nodes for the BNO085 IMU subsystem

```

## Docker Environment Setup

The development environment is containerized using Docker to abstract dependency installations. This setup includes configuration support for both the host system (PC/Laptop) environment and the embedded deployment stack.

### Prerequisites

* Ubuntu (Tested on 24.04 / 22.04)
* Docker Engine installed
* VSCode or Cursor with the **Dev Containers** extension installed

```bash
# Install Docker via convenience script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh

# Configure non-root user permissions
sudo usermod -aG docker $USER

```

> [!IMPORTANT]
> **Log out and log back into your system to apply the new Docker group permissions before proceeding.**

If running the Gazebo simulation on a machine with dedicated graphics, install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) to enable GPU acceleration inside the container.

### Workspace Deployment

1. Create a workspace directory and clone this repository:

```bash
mkdir -p ~/pandabot_ws/src
cd ~/pandabot_ws/src
git clone https://github.com/NaitikDobariya/PandaBot.git 
```


- Open the workspace root folder (`~/pandabot_ws`) in VSCode or Cursor.

- Press `Ctrl+Shift+P`, select **Dev Containers: Reopen in Container**, and choose the configuration located in `.devcontainer/`.

- Once inside the container terminal, compile the workspace:

```bash
colcon build --symlink-install
source install/setup.bash

```



---

## Execution Guide

### 1. Launching the Simulation

To run the robot inside the Gazebo environment with full sensor simulation and active `ros2_control` nodes:

```bash
ros2 launch robo_gazebo pandabot_simulation.launch.py

```

### 2. Physical Hardware Bringup

Compile and upload the firmware within `robo_drivetrain` to the Arduino Uno. Connect all hardware sensors to the Raspberry Pi 5, then run the core driver launch file:

```bash
ros2 launch robo_bringup pandabot_core.launch.py

```

### 3. Mapping and Autonomous Navigation

With the robot running (either in simulation or real-world), use one of the following operations:

* **Generate a Map (SLAM Toolbox):**
```bash
ros2 launch robo_navigation mapping.launch.py
```


* **Execute Autonomous Navigation (Nav2):**
```bash
ros2 launch robo_navigation navigation.launch.py map:=/path/to/your/saved_map.yaml
```



### Troubleshooting Serial Device Permissions

If the LiDAR, Arduino, or Pico drivers fail to initialize due to connection limits, grant read/write access to the host communication interfaces:

```bash
sudo chmod 666 /dev/ttyUSB0   # RPLIDAR connection mapping
sudo chmod 666 /dev/ttyACM0   # Arduino Uno MCU mapping
sudo chmod 666 /dev/ttyACM1   # Raspberry Pi Pico IMU mapping

```

---

## Hardware Specifications & Bill of Materials (BOM)

| Component Category | Hardware Item | Operational/Technical Role |
| --- | --- | --- |
| **Primary Compute** | Raspberry Pi 5 (8GB RAM) | Runs ROS 2 nodes, SLAM Toolbox, Nav2 stack, and processing tasks. |
| **Low-Level Compute** | Arduino Uno R3 | Manages physical motor encoder tracking and real-time PID control loops. |
| **Primary Sensor** | SLAMTEC RPLIDAR A1M8 (6m Range) | Generates 360° 2D laser scan data for mapping and obstacle avoidance. |
| **Inertial Sensor** | BNO085 IMU Subsystem (via [VibeChecker](https://github.com/NaitikDobariya/VibeChecker)) | Supplies stable, fused 9-DOF orientation data to the EKF odometry node. |
| **Motor Drivers** | Cytron MDD10A (Dual Channel) | Translates logic PWM control lines from the Arduino into high-current motor power. |
| **Actuators** | 2x Geared DC Motors with Encoders | Drives wheels while feeding high-resolution rotation ticks back to the MCU. |
| **Power Infrastructure** | Custom PDB + 2500 mAh LiPo Battery | Distributes isolated power tracks to the compute units and high-surge drive motors. |
| **Chassis Elements** | 3D Printed Structural Decks & Spacers | Provides the modular physical frame and variable mounting tiers. |

---

