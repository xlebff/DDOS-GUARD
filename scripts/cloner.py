import git # type: ignore
import shutil
import stat
from pathlib import Path

class RepositoryManager:
    def __init__(self, base_dir="cloned_repos"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def remove_readonly(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def clone_repository(self, repo_url: str, folder_name: str = None) -> Path:
        # Clone repository to specified folder
        
        if folder_name is None:
            # Extract repository name from URL
            folder_name = repo_url.split('/')[-1].replace('.git', '')
        
        clone_path = self.base_dir / folder_name
        
        # Remove folder if it already exists
        if clone_path.exists():
            try:
                shutil.rmtree(clone_path, onerror=self.remove_readonly)
                print(f"Removed existing folder: {folder_name}")
            except PermissionError:
                print(f"Warning: Could not remove existing folder {folder_name}, trying to continue...")
                # Try to remove .git folder specifically
                git_path = clone_path / ".git"
                if git_path.exists():
                    try:
                        shutil.rmtree(git_path)
                        print("Removed .git folder")
                    except PermissionError:
                        print("Warning: Could not remove .git folder")
        
        try:
            print(f"Cloning {repo_url} to {clone_path}...")
            
            # Clone the repository
            repo = git.Repo.clone_from(repo_url, clone_path)
            
            print(f"Successfully cloned to: {clone_path}")
            print(f"Latest commit: {repo.head.commit.message[:50]}...")
            
            return clone_path
            
        except git.exc.GitCommandError as e:
            print(f"Cloning error: {e}")
            return None
    
    def clone_github_repo(self, owner: str, repo_name: str, use_https: bool = True) -> Path:
        # Clone repository from GitHub using owner and repository name
        
        if use_https:
            repo_url = f"https://github.com/{owner}/{repo_name}.git"
        else:
            repo_url = f"git@github.com:{owner}/{repo_name}.git"
        
        return self.clone_repository(repo_url, repo_name)
    
    def get_repo_info(self, repo_path: Path) -> dict:
        # Get information about cloned repository
        try:
            repo = git.Repo(repo_path)
            
            return {
                'path': str(repo_path),
                'branch': repo.active_branch.name,
                'commit': repo.head.commit.hexsha[:8],
                'message': repo.head.commit.message,
                'files_count': len(list(repo_path.rglob('*'))),
                'size_mb': self.get_folder_size(repo_path)
            }
        except Exception as e:
            print(f"Error getting repository info: {e}")
            return {}
    
    def get_folder_size(self, path: Path) -> float:
        # Calculate folder size in megabytes
        total_size = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return round(total_size / (1024 * 1024), 2)
    
    def list_cloned_repos(self) -> list:
        # List all cloned repositories
        repos = []
        for item in self.base_dir.iterdir():
            if item.is_dir():
                repo_info = self.get_repo_info(item)
                repos.append(repo_info)
        return repos
    
    def remove_repository(self, repo_name: str) -> bool:
        # Remove cloned repository
        repo_path = self.base_dir / repo_name
        if repo_path.exists():
            shutil.rmtree(repo_path)
            print(f"Repository removed: {repo_name}")
            return True
        else:
            print(f"Repository not found: {repo_name}")
            return False