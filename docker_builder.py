import os
import subprocess
import tempfile
import shutil

class DockerImageBuilder:
    def __init__(self, package_requirements, python_file_path):
        self.package_requirements = package_requirements
        self.python_file_path = python_file_path

    def _create_dockerfile(self, dockerfile_path):
        """Create a Dockerfile for the image"""
        dockerfile_content = """
        FROM python:3.10-slim
        
        # Set working directory in container
        WORKDIR /app
        
        # Install dependencies
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        
        # Copy the Python application file
        COPY app.py .
        
        # Set the entry point to run the app
        CMD ["python", "app.py"]
        """
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

    def build_image(self):
        try:
            # Create a temporary directory for Docker setup
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create Dockerfile in the temporary directory
                dockerfile_path = os.path.join(temp_dir, "Dockerfile")
                self._create_dockerfile(dockerfile_path)
                
                # Create requirements.txt in the temporary directory
                requirements_path = os.path.join(temp_dir, "requirements.txt")
                with open(requirements_path, 'w') as f:
                    f.write("\n".join(self.package_requirements))
                
                # Copy the Python file into the temporary directory
                python_file_dest = os.path.join(temp_dir, "app.py")
                with open(python_file_dest, 'w') as f:
                    f.write(open(self.python_file_path).read())

                # Build the Docker image and capture output
                image_name = "airseal-app"
                build_command = ['docker', 'build', '--tag', image_name, temp_dir]
                result = subprocess.run(build_command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

                # Check for errors during Docker build
                if result.returncode != 0:
                    raise RuntimeError(f"Docker build failed with error: {result.stderr}")
                
                # Save the Docker image to a file directly in the current working directory
                current_working_dir = os.getcwd()
                image_file_path = os.path.join(current_working_dir, f"{image_name}.img")
                subprocess.run(
                    ['docker', 'save', '-o', image_file_path, image_name],
                    check=True
                )

                return image_file_path
        except Exception as e:
            raise RuntimeError(f"Error building Docker image: {str(e)}")
