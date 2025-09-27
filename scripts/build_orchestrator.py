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
            return {'error': f'Repository {repo_name} not found in cloned_repos'}
        
        print(f"Starting project build: {repo_name}")
        print(f"Project type: {project_type}")
        
        # Debug: list repository contents
        print("Repository contents:")
        for item in repo_path.iterdir():
            print(f"  - {item.name}")
        
        # Check if Dockerfile already exists
        target_dockerfile = repo_path / "Dockerfile"
        
        if target_dockerfile.exists():
            print("Using existing Dockerfile...")
        else:
            # Step 1: Generate Dockerfile
            print("Generating Dockerfile...")
            dockerfile_path = self.docker_gen.generate_dockerfile(repo_path, project_type)
            
            # Copy Dockerfile to repository directory for build context
            if dockerfile_path.exists():
                import shutil
                shutil.copy2(dockerfile_path, target_dockerfile)
                print(f"Dockerfile copied to: {target_dockerfile}")
            else:
                return {'error': f'Failed to generate Dockerfile for {repo_name}'}
        
        # Step 2: Build Docker image
        print("Building Docker image...")
        build_result = self.builder.build_image(repo_path, target_dockerfile, project_type)
        
        # Step 3: Test the built image
        if 'image_name' in build_result:
            print("Testing Docker image...")
            test_result = self.builder.test_image(build_result['image_name'])
            build_result['test_passed'] = test_result
        
        # Save build results
        self._save_build_result(repo_name, project_type, build_result)
        
        return build_result
    
    def _save_build_result(self, repo_name: str, project_type: str, result: dict):
        # Load existing results or create new results dictionary
        if self.results_file.exists():
            with open(self.results_file, 'r') as f:
                results = json.load(f)
        else:
            results = {}
        
        # Add new build result
        results[repo_name] = {
            'project_type': project_type,
            'timestamp': datetime.now().isoformat(),
            'result': result
        }
        
        # Save updated results to file
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    def build_all_projects(self, projects_list: list):
        # Build multiple projects from a list
        print("Starting batch build process...")
        
        for repo_name, project_type in projects_list:
            print(f"Building project: {repo_name} ({project_type})")
            result = self.build_project(repo_name, project_type)
            
            if 'error' in result:
                print(f"Build failed for {repo_name}: {result['error']}")
            else:
                print(f"Build completed for {repo_name}")
    
    def get_build_summary(self) -> dict:
        # Get summary of all build results
        if not self.results_file.exists():
            return {'total': 0, 'success': 0, 'failed': 0}
        
        with open(self.results_file, 'r') as f:
            results = json.load(f)
        
        success_count = 0
        failed_count = 0
        
        for repo_name, build_info in results.items():
            if 'error' in build_info['result']:
                failed_count += 1
            else:
                success_count += 1
        
        return {
            'total': len(results),
            'success': success_count,
            'failed': failed_count,
            'projects': list(results.keys())
        }