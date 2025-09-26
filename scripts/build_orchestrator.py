from pathlib import Path
from docker_generator import DockerfileGenerator
from builder import DockerBuilder
import json
from datetime import datetime

class BuildOrchestrator:
    def __init__(self):
        self.docker_gen = DockerfileGenerator()
        self.builder = DockerBuilder()
        self.results_file = Path("build_results.json")
    
    def build_project(self, repo_name: str, project_type: str) -> dict:        
        repo_path = Path("cloned_repos") / repo_name
        
        if not repo_path.exists():
            return {'error': f'repository {repo_name} not found in cloned_repos'}
        
        print(f"project assembly...: {repo_name}")
        
        print("generating a dockerfile...")
        dockerfile_path = self.docker_gen.generate_dockerfile(repo_path, project_type)
        
        target_dockerfile = repo_path / "Dockerfile"
        dockerfile_path.rename(target_dockerfile)
        
        print("building a docker image...")
        build_result = self.builder.build_image(repo_path, target_dockerfile, project_type)
        
        if 'image_name' in build_result:
            print("testing...")
            test_result = self.builder.test_image(build_result['image_name'])
            build_result['test_passed'] = test_result
        
        self._save_build_result(repo_name, project_type, build_result)
        
        return build_result
    
    def _save_build_result(self, repo_name: str, project_type: str, result: dict):        
        if self.results_file.exists():
            with open(self.results_file, 'r') as f:
                results = json.load(f)
        else:
            results = {}
        
        results[repo_name] = {
            'project_type': project_type,
            'timestamp': datetime.now().isoformat(),
            'result': result
        }
        
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)