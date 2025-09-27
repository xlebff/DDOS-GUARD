import requests
from typing import List, Dict

class GitHubScanner:
    def __init__(self, token=None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {}
        
        if token:
            self.headers = {"Authorization": f"token {token}"}
    
    # Retrieves the contents of a repository or a specific folder
    def get_repo_contents(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе к GitHub API: {e}")
            return []
    

    # Scans the entire repository and returns information about files
    def scan_repository(self, owner: str, repo: str) -> Dict:
        print(f"🔍 Сканируем репозиторий {owner}/{repo}...")
        
        files_info = {
            'root_files': [],
            'directories': [],
            'all_files': []
        }
        
        # Root dir
        root_contents = self.get_repo_contents(owner, repo)
        
        for item in root_contents:
            file_info = {
                'name': item['name'],
                'path': item['path'],
                'type': item['type'],
                'size': item.get('size', 0),
                'download_url': item.get('download_url')
            }
            
            files_info['root_files'].append(file_info)
            files_info['all_files'].append(file_info)
            
            if item['type'] == 'dir':
                files_info['directories'].append(item['name'])
                self._scan_directory(owner, repo, item['path'], files_info)
        
        return files_info
    
    def _scan_directory(self, owner: str, repo: str, path: str, files_info: Dict):
        contents = self.get_repo_contents(owner, repo, path)
        
        for item in contents:
            file_info = {
                'name': item['name'],
                'path': item['path'],
                'type': item['type'],
                'size': item.get('size', 0),
                'download_url': item.get('download_url')
            }
            
            files_info['all_files'].append(file_info)
            
            if item['type'] == 'dir':
                self._scan_directory(owner, repo, item['path'], files_info)
    

    def detect_project_type(self, owner: str, repo: str) -> str:
        files_info = self.scan_repository(owner, repo)
        file_names = [f['name'] for f in files_info['all_files']]
        
        detection_rules = {
            'python': ['requirements.txt', 'pyproject.toml', 'setup.py'],
            'nodejs': ['package.json'],
            'java-maven': ['pom.xml'],
            'java-gradle': ['build.gradle', 'build.gradle.kts'],
            'go': ['go.mod'],
            'rust': ['Cargo.toml'],
            'docker': ['Dockerfile'],
            'dotnet': ['.csproj']
        }
        
        for project_type, indicators in detection_rules.items():
            for indicator in indicators:
                if project_type == 'dotnet':
                    if any(f.endswith('.csproj') for f in file_names):
                        return project_type
                elif indicator in file_names:
                    if project_type == 'java-gradle' and 'build.gradle' in file_names:
                        return 'java-gradle'
                    elif project_type == 'java-maven' and 'pom.xml' in file_names:
                        return 'java-maven'
                    else:
                        return project_type
        
        # Дополнительная проверка для Python проектов по .py файлам
        if any(f.endswith('.py') for f in file_names):
            return 'python'
        
        return 'unknown'