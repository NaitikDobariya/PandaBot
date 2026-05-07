# 1. Use the Humble Base image (Lighter than Desktop for Pi's RAM)
FROM osrf/ros:humble-ros-base

# Avoid user interaction during apt installations
ENV DEBIAN_FRONTEND=noninteractive

# 2. Update and install basic dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-setuptools \
    python3-colcon-common-extensions \
    python3-rosdep \
    tmux \
    git \
    nano \
    vim \
    bash-completion \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Core Robotics Packages (No heavy GUI, but keeps the brains)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-ros-gz-bridge \
    ros-humble-robot-state-publisher \
    ros-humble-xacro \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    && rm -rf /var/lib/apt/lists/*

# 4. Navigation 2 (Essential for Pandabot's movement)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-slam-toolbox \
    && rm -rf /var/lib/apt/lists/*

# 5. User Management & PI HARDWARE ACCESS
ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    # CRITICAL: Add user to dialout (Serial), video (Camera), i2c, and gpio
    && usermod -aG dialout,video,i2c,gpio $USERNAME

# Auto-source ROS 2 Humble
RUN echo "source /opt/ros/humble/setup.bash" >> /home/$USERNAME/.bashrc

# Switch to the non-root user
USER $USERNAME
WORKDIR /home/$USERNAME/pandabot_ws