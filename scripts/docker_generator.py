from pathlib import Path
import yaml # type: ignore

class DockerfileGenerator:
    def __init__(self, templates_dir="templates", outputs_dir="outputs"):
        self.templates_dir = Path(templates_dir)
        self.outputs_dir = Path(outputs_dir)
        self.outputs_dir.mkdir(exist_ok=True)
    
    def detect_project_structure(self, repo_path: Path) -> dict:
        """Анализирует структуру проекта для точной настройки Dockerfile"""
        repo_path = Path(repo_path)
        
        analysis = {
            'entry_point': None,
            'config_files': [],
            'dependencies_files': [],
            'build_commands': []
        }
        
        # entry point
        entry_points = ['main.py', 'app.py', 'index.js', 'server.js', 'src/main.java', 'main.go']
        for ep in entry_points:
            if (repo_path / ep).exists():
                analysis['entry_point'] = ep
                break
        
        # config files
        config_patterns = ['package.json', 'requirements.txt', 'pom.xml', 'build.gradle', 'go.mod', 'Cargo.toml']
        analysis['dependencies_files'] = [f for f in config_patterns if (repo_path / f).exists()]
        
        # Определяем команды сборки на основе типа проекта
        if (repo_path / 'package.json').exists():
            analysis['build_commands'] = ['npm install', 'npm run build']
        elif (repo_path / 'requirements.txt').exists():
            analysis['build_commands'] = ['pip install -r requirements.txt']
        elif (repo_path / 'pom.xml').exists():
            analysis['build_commands'] = ['mvn clean package']
        
        return analysis
    
    def generate_dockerfile(self, repo_path: Path, project_type: str) -> Path:
        """Генерирует Dockerfile на основе шаблона и анализа проекта"""
        
        # Анализируем проект
        analysis = self.detect_project_structure(repo_path)
        
        # Выбираем шаблон
        template_file = self.templates_dir / f"Dockerfile.{project_type}"
        if not template_file.exists():
            template_file = self.templates_dir / "Dockerfile.generic"
        
        # Читаем шаблон
        with open(template_file, 'r') as f:
            template = f.read()
        
        # Заменяем плейсхолдеры
        dockerfile_content = self._customize_template(template, analysis, repo_path.name)
        
        # Сохраняем Dockerfile
        output_dockerfile = self.outputs_dir / f"Dockerfile.{repo_path.name}"
        with open(output_dockerfile, 'w') as f:
            f.write(dockerfile_content)
        
        print(f"✅ Dockerfile создан: {output_dockerfile}")
        return output_dockerfile
    
    def _customize_template(self, template: str, analysis: dict, repo_name: str) -> str:
        """Настраивает шаблон под конкретный проект"""
        
        # Заменяем плейсхолдеры
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
        """Генерирует команды установки зависимостей"""
        commands = []
        
        if 'package.json' in analysis['dependencies_files']:
            commands.append('RUN npm install')
        elif 'requirements.txt' in analysis['dependencies_files']:
            commands.append('RUN pip install -r requirements.txt')
        elif 'pom.xml' in analysis['dependencies_files']:
            commands.append('RUN mvn dependency:resolve')
        
        return '\n'.join(commands) if commands else '# No specific install commands detected'
    
    def _generate_build_commands(self, analysis: dict) -> str:
        """Генерирует команды сборки"""
        if analysis['build_commands']:
            return '\n'.join([f'RUN {cmd}' for cmd in analysis['build_commands']])
        return '# No build commands detected'