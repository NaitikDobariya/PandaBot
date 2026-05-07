#!/bin/bash

SESSION="robo_sim"
WORKSPACE_DIR="/home/ros/pandabot_ws"

# Create new session (Pane 0: Left Half)
tmux new-session -d -s $SESSION

# Split horizontally to create Left and Right halves
tmux split-window -h -t $SESSION

# Select Right pane and split vertically (Creates Pane 1: Top-Right, Pane 2: Bottom-Right)
tmux select-pane -t $SESSION:0.1
tmux split-window -v -t $SESSION:0.1

# Pane 0 (Left Half) → Main Launch (Gazebo, Bridges, Spawner, Nav2)
tmux send-keys -t $SESSION:0.0 "cd $WORKSPACE_DIR && source install/setup.bash && ros2 launch robo_navigation nav2_amcl.launch.py" C-m

# Pane 1 (Top-Right) → RViz
# Delaying 5s to ensure ROS processes are registered
tmux send-keys -t $SESSION:0.1 "cd $WORKSPACE_DIR && source install/setup.bash && sleep 5 && ros2 run rviz2 rviz2 -d /opt/ros/humble/share/nav2_bringup/rviz/nav2_default_view.rviz" C-m

# Pane 2 (Bottom-Right) → Teleop
# Delaying 10s to ensure Nav2 and Gazebo are completely ready before sending cmd_vel
tmux send-keys -t $SESSION:0.2 "cd $WORKSPACE_DIR && source install/setup.bash && sleep 10 && ros2 run robo_control keyboard_teleop.py" C-m

# Final Setup
# Focus on the Teleop pane so you can drive immediately upon attaching
tmux select-pane -t $SESSION:0.2

# Attach to the session
tmux attach -t $SESSION