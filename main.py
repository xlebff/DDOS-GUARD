import sys
import os
from dotenv import load_dotenv
from scaner import GitHubScanner

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv('TOKEN')

    scanner = GitHubScanner(TOKEN)
    
    owner = sys.argv[1]
    repo = sys.argv[2]
    
    project_type = scanner.detect_project_type(owner, repo)
    print(f"🎯 Определен тип проекта: {project_type}")