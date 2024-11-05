#!/bin/bash

# Check if we're inside a TMUX session
if [ -z "$TMUX" ]; then
  echo "This script must be run inside a tmux session."
  exit 1
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

# Create a new window
tmux new-window -n my_window

# Run commands in each pane
tmux send-keys -t my_window.1 "cd $SCRIPT_DIR/src/other_service" C-m
tmux send-keys -t my_window.1 'docker compose up' C-m

sleep 5

tmux split-window -h      # Split horizontally to create two columns
tmux split-window -v -t 0 # Split the left pane vertically
tmux split-window -v -t 1 # Split the right pane vertically
tmux split-window -h -t 4 # Split the right pane vertically

tmux send-keys -t my_window.2 "cd $SCRIPT_DIR/src/preprocessing" C-m
tmux send-keys -t my_window.2 'rye sync' C-m
tmux send-keys -t my_window.2 'source .venv/bin/activate' C-m
tmux send-keys -t my_window.2 './run_server.sh' C-m

tmux send-keys -t my_window.3 "cd $SCRIPT_DIR/src/ensemble" C-m
tmux send-keys -t my_window.3 'rye sync' C-m
tmux send-keys -t my_window.3 'source .venv/bin/activate' C-m
tmux send-keys -t my_window.3 './run_server.sh' C-m

tmux send-keys -t my_window.4 "cd $SCRIPT_DIR/src/inference" C-m
tmux send-keys -t my_window.4 'rye sync --all-features' C-m
tmux send-keys -t my_window.4 'source .venv/bin/activate' C-m
tmux send-keys -t my_window.4 './run_server.sh' C-m

tmux send-keys -t my_window.5 "cd $SCRIPT_DIR/src/inference" C-m
tmux send-keys -t my_window.5 'source .venv/bin/activate' C-m
tmux send-keys -t my_window.5 './run_server.sh --model EfficientNetB0' C-m
#
# Optional: switch to the new window
tmux select-window -t my_window
