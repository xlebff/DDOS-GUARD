from pathlib import Path
import yaml # type: ignore

class DockerfileGenerator:
    def __init__(self, templates_dir="templates", outputs_dir="outputs"):
        self.templates_dir = Path(templates_dir)
        self.outputs_dir = Path(outputs_dir)
        self.outputs_dir.mkdir(exist_ok=True)
    
    def detect_project_structure(self, repo_path: Path) -> dict:
        # Analyze project structure for Dockerfile customization
        repo_path = Path(repo_path)
        
        analysis = {
            'entry_point': None,
            'config_files': [],
            'dependencies_files': [],
            'build_commands': [],
            'python_framework': 'generic',
            'is_web_app': False,
            'port': 8080,
            'java_type': None
        }
        
        # Find entry point file with better detection
        entry_points = [
            'main.py', 'app.py', 'run.py', 'manage.py', 
            'wsgi.py', 'application.py', 'index.py'
        ]
        
        # Check for common entry points
        for ep in entry_points:
            if (repo_path / ep).exists():
                analysis['entry_point'] = ep
                break
        
        # If no common entry point found, look for any .py file with main function
        if not analysis['entry_point']:
            for py_file in repo_path.glob('*.py'):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'if __name__ == "__main__"' in content or 'def main()' in content:
                            analysis['entry_point'] = py_file.name
                            break
                except:
                    continue
        
        # Fallback to first .py file if still not found
        if not analysis['entry_point']:
            py_files = list(repo_path.glob('*.py'))
            if py_files:
                analysis['entry_point'] = py_files[0].name
        
        # Ultimate fallback
        if not analysis['entry_point']:
            analysis['entry_point'] = 'app.py'
        
        # Find configuration files
        config_patterns = ['package.json', 'requirements.txt', 'pom.xml', 'build.gradle', 'go.mod', 'Cargo.toml']
        analysis['dependencies_files'] = [f for f in config_patterns if (repo_path / f).exists()]
        
        # Determine build commands based on project type
        if (repo_path / 'package.json').exists():
            analysis['build_commands'] = ['npm install', 'npm run build']
        elif (repo_path / 'requirements.txt').exists():
            analysis['build_commands'] = ['pip install -r requirements.txt']
        elif (repo_path / 'pom.xml').exists():
            analysis['build_commands'] = ['mvn clean package']
        
        print(f"Detected entry point: {analysis['entry_point']}")
        return analysis

    def generate_dockerfile(self, repo_path: Path, project_type: str) -> Path:
        # Generate Dockerfile based on template and project analysis
        
        # Analyze project structure
        analysis = self.detect_project_structure(repo_path)
        
        # Select appropriate template
        template_file = self.templates_dir / f"Dockerfile.{project_type}"
        if not template_file.exists():
            template_file = self.templates_dir / "Dockerfile.generic"
        
        # Read template file
        with open(template_file, 'r') as f:
            template = f.read()
        
        # Customize template with project-specific values
        dockerfile_content = self._customize_template(template, analysis, repo_path.name)
        
        # Save generated Dockerfile
        output_dockerfile = self.outputs_dir / f"Dockerfile.{repo_path.name}"
        with open(output_dockerfile, 'w') as f:
            f.write(dockerfile_content)
        
        print(f"Dockerfile created: {output_dockerfile}")
        return output_dockerfile
    
    def _customize_template(self, template: str, analysis: dict, repo_name: str) -> str:
        # Customize template with project-specific values
        
        replacements = {
            '{{PROJECT_NAME}}': repo_name,
            '{{ENTRY_POINT}}': analysis['entry_point'] or 'app.py',
            '{{INSTALL_COMMANDS}}': self._generate_install_commands(analysis),
            '{{BUILD_COMMANDS}}': self._generate_build_commands(analysis),
        }
        
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        
        return template
    
    def _generate_install_commands(self, analysis: dict) -> str:
        # Generate dependency installation commands
        commands = []
        
        if 'package.json' in analysis['dependencies_files']:
            commands.append('RUN npm install')
        elif 'requirements.txt' in analysis['dependencies_files']:
            commands.append('RUN pip install -r requirements.txt')
        elif 'pom.xml' in analysis['dependencies_files']:
            commands.append('RUN mvn dependency:resolve')
        
        return '\n'.join(commands) if commands else '# No specific install commands detected'
    
    def _generate_build_commands(self, analysis: dict) -> str:
        # Generate build commands
        if analysis['build_commands']:
            return '\n'.join([f'RUN {cmd}' for cmd in analysis['build_commands']])
        return '# No build commands detected'
    
    def get_available_templates(self) -> list:
        # List all available Dockerfile templates
        templates = []
        for template_file in self.templates_dir.glob("Dockerfile.*"):
            templates.append(template_file.name.replace("Dockerfile.", ""))
        return templates