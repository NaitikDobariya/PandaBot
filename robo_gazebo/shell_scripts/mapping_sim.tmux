#!/bin/bash

# tmux to launch the working Simulator + SLAM, RViz, and Teleop setup.

SESSION="robo_mapping"
WORKSPACE_DIR="/home/ros/pandabot_ws"

# Kill existing session if running
tmux kill-session -t $SESSION 2>/dev/null

# Create new session (Pane 0: Left)
tmux new-session -d -s $SESSION

# Split horizontally to create Left and Right halves
tmux split-window -h -t $SESSION

# Select Right pane and split vertically (Creates Pane 1: Top-Right, Pane 2: Bottom-Right)
tmux select-pane -t $SESSION:0.1
tmux split-window -v -t $SESSION:0.1

# -----------------------------
# Pane 0 (Left) → Simulation & SLAM
# -----------------------------
# Boot your working launch file immediately.
tmux send-keys -t $SESSION:0.0 "cd $WORKSPACE_DIR && source install/setup.bash && ros2 launch robo_gazebo sim_mapping.launch.py" C-m

# -----------------------------
# Pane 1 (Top-Right) → RViz
# -----------------------------
# Wait 5 seconds to let Gazebo and SLAM spin up before RViz loads.
tmux send-keys -t $SESSION:0.1 "cd $WORKSPACE_DIR && source install/setup.bash && sleep 5 && ros2 run rviz2 rviz2 -d src/robo_gazebo/rviz/sim_mapping.rviz" C-m

# -----------------------------
# Pane 2 (Bottom-Right) → Teleop
# -----------------------------
# Wait 8 seconds so you don't accidentally send commands before Gazebo is ready.
tmux send-keys -t $SESSION:0.2 "cd $WORKSPACE_DIR && source install/setup.bash && sleep 8 && ros2 run robo_control keyboard_teleop.py" C-m

# -----------------------------
# Final Setup
# -----------------------------
# Focus on the Teleop pane so you can drive the robot immediately
tmux select-pane -t $SESSION:0.2

# Attach to the session
tmux attach -t $SESSION