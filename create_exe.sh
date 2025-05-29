#!/bin/bash

# Install required libraries
if [ -f "requirements.txt" ]; then
  echo "Installing dependencies from requirements.txt..."
  pip install -r requirements.txt
else
  echo "Warning: requirements.txt file not found. Dependencies may be missing."
fi

# Convert fix_main.py to an executable
pyinstaller --onefile main.py

# Notify the user
if [ $? -eq 0 ]; then
  echo "Executable created successfully."
else
  echo "Failed to create executable."
fi
