import os
import yaml
import sys

owner = sys.argv[1]
repo = sys.argv[2]

project_type = detect_project_type()
print("Project type: " + project_type)