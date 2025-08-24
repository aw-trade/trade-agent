"""Docker operations service."""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from config.settings import settings
from config.validation import validate_docker_name, validate_file_path, ValidationError


class DockerError(Exception):
    """Exception raised when Docker operations fail."""
    pass


class DockerService:
    """Service for Docker operations."""
    
    def __init__(self):
        self.build_timeout = settings.docker_config['build_timeout']
    
    def is_docker_available(self) -> bool:
        """Check if Docker is available on the system."""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def build_image(self, project_path: str, image_name: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Build a Docker image for the project."""
        try:
            # Validate inputs
            project_dir = validate_file_path(project_path, must_exist=True)
            dockerfile_path = project_dir / 'Dockerfile'
            
            if not dockerfile_path.exists():
                raise DockerError(f"Dockerfile not found in {project_path}")
            
            # Validate and sanitize image name
            clean_image_name = validate_docker_name(image_name)
            
            # Check Docker availability
            if not self.is_docker_available():
                raise DockerError("Docker is not available. Please install Docker and ensure it's running.")
            
            # Prepare build command
            if tags is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                tags = ['latest', timestamp]
            
            build_cmd = ['docker', 'build']
            
            # Add tags
            for tag in tags:
                build_cmd.extend(['-t', f"{clean_image_name}:{tag}"])
            
            build_cmd.append('.')
            
            # Execute build
            print(f"Building Docker image: {clean_image_name}")
            print(f"Build command: {' '.join(build_cmd)}")
            
            start_time = datetime.now()
            
            result = subprocess.run(
                build_cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=self.build_timeout
            )
            
            build_duration = datetime.now() - start_time
            
            if result.returncode == 0:
                # Get image information
                image_info = self._get_image_info(clean_image_name, tags[0])
                
                return {
                    'success': True,
                    'image_name': clean_image_name,
                    'tags': tags,
                    'build_duration': build_duration.total_seconds(),
                    'size': image_info.get('size', 'Unknown'),
                    'image_id': image_info.get('image_id', ''),
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                return {
                    'success': False,
                    'error': 'Docker build failed',
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'build_duration': build_duration.total_seconds()
                }
                
        except subprocess.TimeoutExpired:
            raise DockerError(f"Docker build timed out after {self.build_timeout} seconds")
        except ValidationError as e:
            raise DockerError(f"Validation error: {e}")
        except Exception as e:
            raise DockerError(f"Docker build error: {e}")
    
    def _get_image_info(self, image_name: str, tag: str = 'latest') -> Dict[str, str]:
        """Get information about a Docker image."""
        try:
            full_name = f"{image_name}:{tag}"
            
            # Get image details
            inspect_cmd = ['docker', 'inspect', full_name]
            result = subprocess.run(inspect_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {}
            
            # Get size
            size_cmd = ['docker', 'images', image_name, '--format', 'table {{.Size}}']
            size_result = subprocess.run(size_cmd, capture_output=True, text=True, timeout=30)
            
            size = 'Unknown'
            if size_result.returncode == 0:
                lines = size_result.stdout.strip().split('\n')
                if len(lines) > 1:
                    size = lines[1]
            
            # Get image ID
            id_cmd = ['docker', 'images', image_name, '--format', 'table {{.ID}}']
            id_result = subprocess.run(id_cmd, capture_output=True, text=True, timeout=30)
            
            image_id = ''
            if id_result.returncode == 0:
                lines = id_result.stdout.strip().split('\n')
                if len(lines) > 1:
                    image_id = lines[1]
            
            return {
                'size': size,
                'image_id': image_id
            }
            
        except Exception:
            return {}
    
    def list_images(self, filter_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Docker images, optionally filtered by name."""
        try:
            if not self.is_docker_available():
                return []
            
            cmd = ['docker', 'images', '--format', 'json']
            if filter_name:
                cmd = ['docker', 'images', filter_name, '--format', 'json']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return []
            
            import json
            images = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        image_data = json.loads(line)
                        images.append({
                            'repository': image_data.get('Repository', ''),
                            'tag': image_data.get('Tag', ''),
                            'image_id': image_data.get('ID', ''),
                            'created': image_data.get('CreatedAt', ''),
                            'size': image_data.get('Size', '')
                        })
                    except json.JSONDecodeError:
                        continue
            
            return images
            
        except Exception as e:
            raise DockerError(f"Failed to list Docker images: {e}")
    
    def remove_image(self, image_name: str, tag: str = 'latest', force: bool = False) -> Dict[str, Any]:
        """Remove a Docker image."""
        try:
            if not self.is_docker_available():
                raise DockerError("Docker is not available")
            
            full_name = f"{image_name}:{tag}"
            cmd = ['docker', 'rmi', full_name]
            
            if force:
                cmd.append('-f')
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except Exception as e:
            raise DockerError(f"Failed to remove Docker image: {e}")
    
    def run_container(self, image_name: str, tag: str = 'latest', 
                     ports: Optional[Dict[str, str]] = None,
                     env_vars: Optional[Dict[str, str]] = None,
                     detached: bool = False) -> Dict[str, Any]:
        """Run a Docker container."""
        try:
            if not self.is_docker_available():
                raise DockerError("Docker is not available")
            
            full_name = f"{image_name}:{tag}"
            cmd = ['docker', 'run', '--rm']
            
            if detached:
                cmd.append('-d')
            
            # Add port mappings
            if ports:
                for host_port, container_port in ports.items():
                    cmd.extend(['-p', f"{host_port}:{container_port}"])
            
            # Add environment variables
            if env_vars:
                for key, value in env_vars.items():
                    cmd.extend(['-e', f"{key}={value}"])
            
            cmd.append(full_name)
            
            if detached:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return {
                    'success': result.returncode == 0,
                    'container_id': result.stdout.strip() if result.returncode == 0 else None,
                    'stderr': result.stderr
                }
            else:
                # For non-detached runs, we don't wait for completion
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                return {
                    'success': True,
                    'process_id': process.pid,
                    'command': ' '.join(cmd)
                }
                
        except Exception as e:
            raise DockerError(f"Failed to run Docker container: {e}")
    
    def generate_docker_commands(self, image_name: str, base_name: str) -> Dict[str, List[str]]:
        """Generate useful Docker commands for the created image."""
        return {
            'build_commands': [
                f"docker build -t {image_name}:latest .",
                f"docker build -t {image_name}:v1.0.0 .",
                f"docker build --build-arg RUST_VERSION=1.75 -t {image_name}:latest ."
            ],
            'run_commands': [
                f"docker run --rm {image_name}:latest",
                f"docker run --rm -p 3000:3000 {image_name}:latest",
                f"docker run --rm -e IMBALANCE_THRESHOLD=0.7 {image_name}:latest",
                f"docker run --rm -v $(pwd)/logs:/app/logs {image_name}:latest",
                f"docker run -d --name {base_name}-strategy {image_name}:latest"
            ],
            'management_commands': [
                "docker ps",
                f"docker logs {base_name}-strategy",
                f"docker stop {base_name}-strategy",
                f"docker rm {base_name}-strategy",
                f"docker images {image_name}"
            ],
            'development_commands': [
                f"docker run --rm -it {image_name}:latest /bin/sh",
                f"docker exec -it {base_name}-strategy /bin/sh"
            ]
        }
    
    def cleanup_old_images(self, keep_latest: int = 5) -> Dict[str, Any]:
        """Clean up old Docker images, keeping only the most recent ones."""
        try:
            if not self.is_docker_available():
                return {'cleaned': 0, 'error': 'Docker not available'}
            
            # Get all images with 'algo' in the name (our generated images)
            images = self.list_images()
            algo_images = [img for img in images if 'algo' in img['repository'].lower()]
            
            if len(algo_images) <= keep_latest:
                return {'cleaned': 0, 'message': f'Only {len(algo_images)} images found, keeping all'}
            
            # Sort by creation date (newest first) and remove old ones
            algo_images.sort(key=lambda x: x['created'], reverse=True)
            images_to_remove = algo_images[keep_latest:]
            
            cleaned = 0
            errors = []
            
            for image in images_to_remove:
                try:
                    result = self.remove_image(image['repository'], image['tag'])
                    if result['success']:
                        cleaned += 1
                    else:
                        errors.append(f"Failed to remove {image['repository']}:{image['tag']}")
                except Exception as e:
                    errors.append(f"Error removing {image['repository']}:{image['tag']}: {e}")
            
            return {
                'cleaned': cleaned,
                'errors': errors,
                'total_checked': len(algo_images)
            }
            
        except Exception as e:
            return {'cleaned': 0, 'error': str(e)}


# Global Docker service instance
docker_service = DockerService()