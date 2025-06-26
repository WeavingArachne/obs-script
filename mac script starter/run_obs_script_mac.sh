#!/bin/bash

echo "=== OBS Auto Recording Script ==="
echo
echo "Starting OBS Recording Automator..."
echo

# Change to your script's directory (adjust the path as needed)
cd "$HOME/Desktop/All Projects/ah/obs-script-updating" || {
  echo "Failed to change directory. Make sure the path exists."
  exit 1
}

# Run the Python script
python3 obs_auto_recorder.py

echo
echo "Script finished. Press [Enter] to close..."
read
