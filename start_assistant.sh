#!/bin/bash
# Quick start script for OpenAI Query Assistant

# Navigate to project directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source ../auv/.venv/bin/activate

# Run the assistant
python version2/openai_query_assistant.py data/data2.csv "$@"
