#!/bin/bash

# Ensure kte.txt exists
if [ ! -f "kte.txt" ]; then
  echo "Error: kte.txt file is required but not found."
  exit 1
fi

# Install required libraries
if [ -f "requirements.txt" ]; then
  echo "Installing dependencies from requirements.txt..."
  pip install -r requirements.txt
else
  echo "Warning: requirements.txt file not found. Dependencies may be missing."
fi

# Specify kte.txt file explicitly
kte_file="kte.txt"

# Convert fix_main.py to an executable
pyinstaller --onefile fix_main.py --add-data "$kte_file:."

# Notify the user
if [ $? -eq 0 ]; then
  echo "Executable created successfully."
else
  echo "Failed to create executable."
fi
