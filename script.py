# I'll create a comprehensive codebase for the Knowledge-Capture MVP project
# Let me start by creating the main directory structure and core files

import os

# Create directory structure
directories = [
    "knowledge_capture_mvp",
    "knowledge_capture_mvp/api",
    "knowledge_capture_mvp/core",
    "knowledge_capture_mvp/db",
    "knowledge_capture_mvp/services",
    "knowledge_capture_mvp/models",
    "knowledge_capture_mvp/utils",
    "knowledge_capture_mvp/frontend",
    "knowledge_capture_mvp/config",
    "knowledge_capture_mvp/tests",
    "knowledge_capture_mvp/scripts"
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    
print("Directory structure created!")
print("\n".join(directories))