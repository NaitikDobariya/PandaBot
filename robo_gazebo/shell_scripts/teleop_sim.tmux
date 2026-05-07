#!/bin/bash

# tmux to launch the simulation setup and the keyboard teleop node.

SESSION="robo_sim"

WORKSPACE_DIR="/home/ros/pandabot_ws"

# Kill existing session if running
tmux kill-session -t $SESSION 2>/dev/null

# Create new session
tmux new-session -d -s $SESSION

# -----------------------------
# Pane 1 → Simulation
# -----------------------------
tmux send-keys -t $SESSION "
cd $WORKSPACE_DIR &&
source install/setup.bash &&
ros2 launch robo_gazebo sim.launch.py
" C-m

# -----------------------------
# Split window for teleop
# -----------------------------
tmux split-window -h -t $SESSION

# -----------------------------
# Pane 2 → Teleop
# -----------------------------
tmux send-keys -t $SESSION:0.1 "
cd $WORKSPACE_DIR &&
source install/setup.bash &&
sleep 3 &&
ros2 run robo_control keyboard_teleop.py
" C-m


tmux attach -t $SESSION