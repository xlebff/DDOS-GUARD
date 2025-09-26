import sys
import os
from dotenv import load_dotenv
from scaner import GitHubScanner
from clone_manager import RepositoryManager

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv('TOKEN')

    owner = sys.argv[1]
    repo = sys.argv[2]
    
    scanner = GitHubScanner(TOKEN)
    
    project_type = scanner.detect_project_type(owner, repo)
    print(f"🎯 Определен тип проекта: {project_type}")

    manager = RepositoryManager()
    
    repo_path = manager.clone_github_repo(owner, repo)
    
    if repo_path:
        info = manager.get_repo_info(repo_path)
        print("\n📋 Информация о репозитории:")
        for key, value in info.items():
            print(f"  {key}: {value}")