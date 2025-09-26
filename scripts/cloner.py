import git # type: ignore
import shutil
from pathlib import Path

class RepositoryManager:
    def __init__(self, base_dir="cloned_repos"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def clone_repository(self, repo_url: str, folder_name: str = None) -> Path:
        """Клонирует репозиторий в указанную папку"""
        
        if folder_name is None:
            # Извлекаем имя репозитория из URL
            folder_name = repo_url.split('/')[-1].replace('.git', '')
        
        clone_path = self.base_dir / folder_name
        
        # Удаляем папку, если она уже существует
        if clone_path.exists():
            shutil.rmtree(clone_path)
            print(f"🗑️  Удалена существующая папка: {folder_name}")
        
        try:
            print(f"⬇️  Клонируем {repo_url} в {clone_path}...")
            
            # Клонируем репозиторий
            repo = git.Repo.clone_from(repo_url, clone_path)
            
            print(f"✅ Успешно клонирован в: {clone_path}")
            print(f"📊 Последний коммит: {repo.head.commit.message[:50]}...")
            
            return clone_path
            
        except git.exc.GitCommandError as e:
            print(f"❌ Ошибка при клонировании: {e}")
            return None
    
    def clone_github_repo(self, owner: str, repo_name: str, use_https: bool = True) -> Path:
        """Клонирует репозиторий с GitHub по имени владельца и репозитория"""
        
        if use_https:
            repo_url = f"https://github.com/{owner}/{repo_name}.git"
        else:
            repo_url = f"git@github.com:{owner}/{repo_name}.git"
        
        return self.clone_repository(repo_url, repo_name)
    
    def get_repo_info(self, repo_path: Path) -> dict:
        """Получает информацию о клонированном репозитории"""
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
            print(f"Ошибка при получении информации: {e}")
            return {}
    
    def get_folder_size(self, path: Path) -> float:
        """Вычисляет размер папки в МБ"""
        total_size = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return round(total_size / (1024 * 1024), 2)