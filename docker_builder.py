import os
import docker
from dotenv import load_dotenv

class DockerImageBuilder:
    def __init__(self, requirements, source_file):
        load_dotenv()
        self.client = docker.from_env()
        self.requirements = requirements
        self.source_file = source_file
        self.build_dir = os.getenv('DOCKER_BUILD_DIR', '/tmp/airseal_builds')

    def prepare_build_context(self):
        """
        Prepare Docker build context
        """
        os.makedirs(self.build_dir, exist_ok=True)
        
        # Write requirements file
        requirements_path = os.path.join(self.build_dir, 'requirements.txt')
        with open(requirements_path, 'w') as f:
            f.write('\n'.join(self.requirements))
        
        # Copy source file
        import shutil
        shutil.copy(self.source_file, os.path.join(self.build_dir, 'app.py'))
        
        return self.build_dir

    def generate_dockerfile(self):
        """
        Generate Dockerfile for the project
        """
        dockerfile_content = f"""
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Default command
CMD ["python", "app.py"]
"""
        dockerfile_path = os.path.join(self.build_dir, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

    def build_image(self, tag='airseal-app:latest'):
        """
        Build Docker image
        """
        self.prepare_build_context()
        self.generate_dockerfile()
        
        try:
            image, build_logs = self.client.images.build(
                path=self.build_dir,
                tag=tag,
                rm=True
            )
            return image, build_logs
        except docker.errors.BuildError as e:
            print(f"Docker build error: {e}")
            return None, None

    def save_image(self, image, output_path):
        """
        Save Docker image to tar file
        """
        if image:
            with open(output_path, 'wb') as f:
                for chunk in image.save():
                    f.write(chunk)
            return True
        return False

# Standalone usage example
if __name__ == '__main__':
    requirements = ['streamlit', 'numpy']
    builder = DockerImageBuilder(requirements, 'test_app.py')
    image, logs = builder.build_image()
    
    if image:
        builder.save_image(image, 'airseal_image.tar')
        print("Image built successfully")
