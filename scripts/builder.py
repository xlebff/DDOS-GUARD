import docker # type: ignore
from pathlib import Path
from datetime import datetime

class DockerBuilder:
    def __init__(self, outputs_dir="outputs", logs_dir="logs"):
        self.outputs_dir = Path(outputs_dir)
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Connect to Docker daemon
        try:
            self.client = docker.from_env()
            print("Docker client connected successfully")
        except Exception as e:
            print(f"Error connecting to Docker: {e}")
            self.client = None
    
    def build_image(self, repo_path: Path, dockerfile_path: Path, project_type: str) -> dict:        
        if not self.client:
            return {'error': 'Docker not available'}
        
        repo_name = repo_path.name
        image_name = f"amazing-automata/{repo_name.lower()}:latest"
        log_file = self.logs_dir / f"build_{repo_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        print(f"Building Docker image: {image_name}")
        
        try:
            # Build the Docker image
            image, build_logs = self.client.images.build(
                path=str(repo_path),  # Directory containing Dockerfile and source code
                dockerfile="Dockerfile",  # Dockerfile name in the build context
                tag=image_name,
                rm=True,  # Remove intermediate containers
                forcerm=True
            )
            
            # Save build logs to file
            self._save_build_logs(build_logs, log_file)
            
            print(f"Image built successfully: {image_name}")
            print(f"Image size: {self._get_image_size(image)}")
            
            return {
                'success': True,
                'image_id': image.id,
                'image_name': image_name,
                'size': self._get_image_size(image),
                'log_file': str(log_file)
            }
            
        except docker.errors.BuildError as e:
            error_msg = f"Build error: {e}"
            print(f"Build failed: {error_msg}")
            self._save_error_log(e, log_file)
            return {'error': error_msg, 'log_file': str(log_file)}
        
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(f"Build failed: {error_msg}")
            return {'error': error_msg}
    
    def _get_image_size(self, image) -> str:
        # Convert image size from bytes to megabytes
        size_bytes = image.attrs['Size']
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.1f} MB"
    
    def _save_build_logs(self, build_logs, log_file: Path):
        # Write build logs to file for debugging
        with open(log_file, 'w', encoding='utf-8') as f:
            for chunk in build_logs:
                if 'stream' in chunk:
                    f.write(chunk['stream'])
                if 'error' in chunk:
                    f.write(f"ERROR: {chunk['error']}\n")
    
    def _save_error_log(self, error, log_file: Path):
        # Save error details to log file
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Build Error: {error}\n")
            for line in getattr(error, 'build_log', []):
                f.write(str(line) + '\n')
    
    def test_image(self, image_name: str) -> bool:
        # Test the built image by running a container
        try:
            print(f"Testing image: {image_name}")
            
            # Run container in detached mode
            container = self.client.containers.run(
                image_name,
                detach=True,
                ports={},  # Port mappings can be added here
                environment={},  # Environment variables can be added here
                command="echo 'Container started successfully'"
            )
            
            # Wait for container to complete and check logs
            container.wait(timeout=30)
            logs = container.logs().decode('utf-8')
            print(f"Container logs: {logs.strip()}")
            
            # Remove the test container
            container.remove()
            
            print("Image test completed successfully")
            return True
            
        except Exception as e:
            print(f"Image test failed: {e}")
            return False
    
    def list_images(self) -> list:
        # List all images with amazing-automata prefix
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