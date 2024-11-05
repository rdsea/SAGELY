#!/bin/bash

# Check if we're inside a TMUX session
if [ -z "$TMUX" ]; then
  echo "This script must be run inside a tmux session."
  exit 1
fi

# Create a new window
tmux select-window -t my_window

# Run commands in each pane
tmux send-keys -t my_window.2 C-c
tmux send-keys -t my_window.3 C-c
tmux send-keys -t my_window.4 C-c
tmux send-keys -t my_window.5 C-c
sleep 2
tmux send-keys -t my_window.1 C-c
sleep 3
tmux kill-window -t my_window

# tmux send-keys -t my_window.4 'cd src/inference' C-m
# tmux send-keys -t my_window.4 'echo "Running command in pane 3"' C-m
#
# tmux send-keys -t my_window.5 'cd src/inference' C-m
# tmux send-keys -t my_window.5 'echo "Running command in pane 3"' C-m
#
# Optional: switch to the new window
