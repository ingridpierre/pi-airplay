#!/bin/bash

# Path to the project directory
PROJECT_DIR="/home/pi/Pi-DAD"

# Activate virtual environment and run the application
cd "$PROJECT_DIR"
source .venv/bin/activate
python app.py