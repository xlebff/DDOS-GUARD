import docker # type: ignore
from pathlib import Path
from datetime import datetime

class DockerBuilder:
    def __init__(self, outputs_dir="outputs", logs_dir="logs"):
        self.outputs_dir = Path(outputs_dir)
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Connecting to Docker
        try:
            self.client = docker.from_env()
            print("docker client connected")
        except Exception as e:
            print(f"error connecting to docker: {e}")
            self.client = None
    
    def build_image(self, repo_path: Path, dockerfile_path: Path, project_type: str) -> dict:        
        if not self.client:
            return {'error': 'Docker not available'}
        
        repo_name = repo_path.name
        image_name = f"amazing-automata/{repo_name.lower()}:latest"
        log_file = self.logs_dir / f"build_{repo_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        print(f"assembling the image: {image_name}")
        
        try:
            image, build_logs = self.client.images.build(
                path=str(repo_path.parent),  # Папка с Dockerfile и исходниками
                dockerfile=str(dockerfile_path),
                tag=image_name,
                rm=True,  # Удалять промежуточные контейнеры
                forcerm=True
            )
            
            # Сохраняем логи
            self._save_build_logs(build_logs, log_file)
            
            print(f"✅ Образ собран: {image_name}")
            print(f"📊 Размер образа: {self._get_image_size(image)}")
            
            return {
                'success': True,
                'image_id': image.id,
                'image_name': image_name,
                'size': self._get_image_size(image),
                'log_file': str(log_file)
            }
            
        except docker.errors.BuildError as e:
            error_msg = f"Ошибка сборки: {e}"
            print(f"❌ {error_msg}")
            self._save_error_log(e, log_file)
            return {'error': error_msg, 'log_file': str(log_file)}
        
        except Exception as e:
            error_msg = f"Неожиданная ошибка: {e}"
            print(f"❌ {error_msg}")
            return {'error': error_msg}
    
    def _get_image_size(self, image) -> str:
        """Возвращает размер образа в читаемом формате"""
        size_bytes = image.attrs['Size']
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.1f} MB"
    
    def _save_build_logs(self, build_logs, log_file: Path):
        """Сохраняет логи сборки в файл"""
        with open(log_file, 'w', encoding='utf-8') as f:
            for chunk in build_logs:
                if 'stream' in chunk:
                    f.write(chunk['stream'])
                if 'error' in chunk:
                    f.write(f"ERROR: {chunk['error']}\n")
    
    def _save_error_log(self, error, log_file: Path):
        """Сохраняет ошибку в лог-файл"""
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Build Error: {error}\n")
            for line in getattr(error, 'build_log', []):
                f.write(str(line) + '\n')
    
    def test_image(self, image_name: str) -> bool:
        """Тестирует собранный образ запуском контейнера"""
        try:
            print(f"🧪 Тестируем образ: {image_name}")
            
            # Запускаем контейнер в фоновом режиме
            container = self.client.containers.run(
                image_name,
                detach=True,
                ports={},  # Можно указать порты если нужно
                environment={},  # Можно добавить переменные окружения
                command="echo 'Container started successfully'"
            )
            
            # Ждем завершения и проверяем логи
            container.wait(timeout=30)
            logs = container.logs().decode('utf-8')
            print(f"📄 Логи контейнера: {logs.strip()}")
            
            # Удаляем контейнер
            container.remove()
            
            print("✅ Тестирование пройдено успешно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            return False
    
    def list_images(self) -> list:
        if not self.client:
            return []
        
        amazing_images = []
        for image in self.client.images.list():
            for tag in image.tags:
                if tag.startswith('amazing-automata/'):
                    amazing_images.append({
                        'tag': tag,
                        'id': image.id[:12],
                        'size': self._get_image_size(image)
                    })
        
        return amazing_images