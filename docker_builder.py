import os
import docker
from dotenv import load_dotenv
import subprocess
import pkg_resources
from typing import List, Dict
import logging

class DockerImageBuilder:
    def __init__(self, requirements: List[str], source_file: str):
        load_dotenv()
        self.client = docker.from_env()
        self.requirements = requirements
        self.source_file = source_file
        self.build_dir = os.getenv('DOCKER_BUILD_DIR', '/tmp/airseal_builds')
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger('DockerBuilder')

    def get_all_dependencies(self) -> List[str]:
        """
        Get all dependencies including transitive ones using pip-tools
        """
        try:
            # Write initial requirements to a file
            temp_req_file = os.path.join(self.build_dir, 'temp_requirements.txt')
            with open(temp_req_file, 'w') as f:
                for req in self.requirements:
                    f.write(f"{req}\n")

            # Use pip-compile to get all dependencies
            result = subprocess.run(
                ['pip-compile', '--output-file=-', temp_req_file],
                capture_output=True,
                text=True
            )
            
            # Parse the output to get all dependencies
            all_deps = []
            for line in result.stdout.split('\n'):
                if line and not line.startswith('#'):
                    all_deps.append(line.strip())
            
            return all_deps
        
        except Exception as e:
            self.logger.error(f"Error getting dependencies: {e}")
            return self.requirements

    def prepare_build_context(self):
        """
        Prepare Docker build context with all dependencies
        """
        os.makedirs(self.build_dir, exist_ok=True)
        
        # Get all dependencies including transitive ones
        all_dependencies = self.get_all_dependencies()
        
        # Write complete requirements file
        requirements_path = os.path.join(self.build_dir, 'requirements.txt')
        with open(requirements_path, 'w') as f:
            f.write('\n'.join(all_dependencies))
        
        # Copy source file
        import shutil
        shutil.copy(self.source_file, os.path.join(self.build_dir, 'app.py'))
        
        return self.build_dir

    def generate_dockerfile(self):
        """
        Generate optimized Dockerfile for the project
        """
        dockerfile_content = """
FROM python:3.9-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.9-slim

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY app.py .

# Set Python path
ENV PYTHONPATH=/usr/local/lib/python3.9/site-packages

# Run as non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Default command
CMD ["python", "app.py"]
"""
        dockerfile_path = os.path.join(self.build_dir, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

    def build_image(self, tag='airseal-app:latest'):
        """
        Build Docker image with all dependencies
        """
        try:
            self.prepare_build_context()
            self.generate_dockerfile()
            
            self.logger.info("Building Docker image...")
            image, build_logs = self.client.images.build(
                path=self.build_dir,
                tag=tag,
                rm=True,
                pull=True
            )
            
            # Export the image as .img file
            output_path = os.path.join(self.build_dir, 'airseal_image.img')
            self.logger.info(f"Saving image to {output_path}")
            
            # Use docker save with subprocess for better control
            subprocess.run([
                'docker', 'save',
                '-o', output_path,
                tag
            ], check=True)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error building Docker image: {e}")
            raise
