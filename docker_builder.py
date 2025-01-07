from typing import Optional, Dict
import os
import tempfile
import subprocess
from pathlib import Path
from dependency_analyzer import DependencyAnalyzer, Dependency

class DockerBuilder:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.temp_dir = tempfile.mkdtemp()
        self.dependency_analyzer = DependencyAnalyzer()
        
    def build(self) -> Optional[str]:
        """Build Docker image based on file type"""
        ext = Path(self.file_path).suffix
        
        builders = {
            '.py': self._build_python_image,
            '.java': self._build_java_image,
            '.js': self._build_node_image,
            '.cpp': self._build_cpp_image,
            '.go': self._build_go_image,
            '.rs': self._build_rust_image
        }
        
        if ext not in builders:
            print(f"Unsupported file type: {ext}")
            return None
            
        return builders[ext]()

    def _generate_dockerfile(self, base_image: str, deps_commands: list, build_commands: list, run_command: str) -> str:
        """Generate Dockerfile content"""
        return f"""
FROM {base_image}
WORKDIR /app
{chr(10).join(deps_commands)}
COPY . .
{chr(10).join(build_commands)}
CMD {run_command}
"""

    def _build_python_image(self) -> Optional[str]:
        """Build Python Docker image"""
        try:
            # Analyze dependencies
            dependencies = self.dependency_analyzer.analyze(self.file_path)
            
            # Generate requirements.txt
            requirements_path = os.path.join(self.temp_dir, 'requirements.txt')
            with open(requirements_path, 'w') as f:
                for dep in dependencies:
                    if dep.type == 'package':
                        f.write(f"{dep.name}{f'=={dep.version}' if dep.version else ''}\n")

            # Copy source file
            dest_path = os.path.join(self.temp_dir, os.path.basename(self.file_path))
            with open(self.file_path, 'rb') as src, open(dest_path, 'wb') as dst:
                dst.write(src.read())

            # Generate Dockerfile
            dockerfile = self._generate_dockerfile(
                base_image="python:3.9-slim",
                deps_commands=[
                    "COPY requirements.txt .",
                    "RUN pip install --no-cache-dir -r requirements.txt"
                ],
                build_commands=[],
                run_command=f'["python", "{os.path.basename(self.file_path)}"]'
            )

            return self._build_from_dockerfile(dockerfile)

        except Exception as e:
            print(f"Error building Python image: {str(e)}")
            return None

    def _build_java_image(self) -> Optional[str]:
        """Build Java Docker image"""
        try:
            # Copy source file
            filename = os.path.basename(self.file_path)
            # Get the class name from the file content
            with open(self.file_path, 'r') as f:
                content = f.read()
                # Find public class name
                import re
                class_match = re.search(r'public\s+class\s+(\w+)', content)
                if class_match:
                    class_name = class_match.group(1)
                    # Rename file to match class name
                    filename = f"{class_name}.java"

            dest_path = os.path.join(self.temp_dir, filename)
            with open(self.file_path, 'rb') as src, open(dest_path, 'wb') as dst:
                dst.write(src.read())

            base_name = os.path.splitext(filename)[0]
            dockerfile = self._generate_dockerfile(
                base_image="openjdk:11-jdk-slim",
                deps_commands=[],
                build_commands=[
                    f"RUN mkdir -p build && \\\n"
                    f"    javac -d build {filename} || echo 'Compilation failed' && \\\n"
                    f"    cd build && \\\n"
                    f"    jar cfe {base_name}.jar {base_name} *.class || echo 'Jar creation failed'"
                ],
                run_command=f'["java", "-jar", "build/{base_name}.jar"]'
            )

            return self._build_from_dockerfile(dockerfile)

        except Exception as e:
            print(f"Error building Java image: {str(e)}")
            return None
    def _build_node_image(self) -> Optional[str]:
        """Build Node.js Docker image"""
        try:
            dependencies = self.dependency_analyzer.analyze(self.file_path)
            
            # Generate package.json
            package_json = {
                "name": "app",
                "version": "1.0.0",
                "dependencies": {}
            }
            
            for dep in dependencies:
                if dep.type == 'package':
                    package_json["dependencies"][dep.name] = dep.version or "latest"

            with open(os.path.join(self.temp_dir, 'package.json'), 'w') as f:
                json.dump(package_json, f, indent=2)

            dockerfile = self._generate_dockerfile(
                base_image="node:16-slim",
                deps_commands=[
                    "COPY package.json .",
                    "RUN npm install"
                ],
                build_commands=[],
                run_command=f'["node", "{os.path.basename(self.file_path)}"]'
            )

            return self._build_from_dockerfile(dockerfile)

        except Exception as e:
            print(f"Error building Node image: {str(e)}")
            return None

    def _build_cpp_image(self) -> Optional[str]:
        """Build C++ Docker image"""
        try:
            dependencies = self.dependency_analyzer.analyze(self.file_path)
            
            # Generate CMakeLists.txt
            cmake_content = f"""
cmake_minimum_required(VERSION 3.10)
project(app)

set(CMAKE_CXX_STANDARD 17)
"""
            for dep in dependencies:
                if dep.type == 'package':
                    cmake_content += f"\nfind_package({dep.name} REQUIRED)"

            cmake_content += f"""
add_executable(app {os.path.basename(self.file_path)})
"""

            with open(os.path.join(self.temp_dir, 'CMakeLists.txt'), 'w') as f:
                f.write(cmake_content)

            dockerfile = self._generate_dockerfile(
                base_image="gcc:latest",
                deps_commands=[
                    "RUN apt-get update && apt-get install -y cmake"
                ],
                build_commands=[
                    "RUN cmake . && make"
                ],
                run_command='["./app"]'
            )

            return self._build_from_dockerfile(dockerfile)

        except Exception as e:
            print(f"Error building C++ image: {str(e)}")
            return None

    def _build_go_image(self) -> Optional[str]:
        """Build Go Docker image"""
        try:
            dependencies = self.dependency_analyzer.analyze(self.file_path)
            
            # Generate go.mod
            module_name = "app"
            go_mod_content = f"module {module_name}\n\ngo 1.16\n\nrequire (\n"
            
            for dep in dependencies:
                if dep.type == 'package':
                    version = dep.version or "latest"
                    go_mod_content += f"\t{dep.name} {version}\n"
            
            go_mod_content += ")\n"

            with open(os.path.join(self.temp_dir, 'go.mod'), 'w') as f:
                f.write(go_mod_content)

            dockerfile = self._generate_dockerfile(
                base_image="golang:1.16",
                deps_commands=[
                    "COPY go.mod .",
                    "RUN go mod download"
                ],
                build_commands=[
                    "RUN go build -o app"
                ],
                run_command='["./app"]'
            )

            return self._build_from_dockerfile(dockerfile)

        except Exception as e:
            print(f"Error building Go image: {str(e)}")
            return None

    def _build_rust_image(self) -> Optional[str]:
        """Build Rust Docker image"""
        try:
            dependencies = self.dependency_analyzer.analyze(self.file_path)
            
            # Generate Cargo.toml
            cargo_toml = {
                "package": {
                    "name": "app",
                    "version": "0.1.0",
                    "edition": "2021"
                },
                "dependencies": {}
            }
            
            for dep in dependencies:
                if dep.type == 'crate':
                    cargo_toml["dependencies"][dep.name] = dep.version or "*"

            with open(os.path.join(self.temp_dir, 'Cargo.toml'), 'w') as f:
                import toml
                toml.dump(cargo_toml, f)

            dockerfile = self._generate_dockerfile(
                base_image="rust:1.60",
                deps_commands=[
                    "COPY Cargo.toml .",
                    "RUN mkdir src && echo 'fn main() {}' > src/main.rs",
                    "RUN cargo build --release",
                    "RUN rm -rf src"
                ],
                build_commands=[
                    "RUN cargo build --release"
                ],
                run_command='["./target/release/app"]'
            )

            return self._build_from_dockerfile(dockerfile)

        except Exception as e:
            print(f"Error building Rust image: {str(e)}")
            return None

    def _build_from_dockerfile(self, dockerfile_content: str) -> Optional[str]:
        """Build Docker image from Dockerfile content"""
        try:
            # Write Dockerfile
            dockerfile_path = os.path.join(self.temp_dir, 'Dockerfile')
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)

            # Build Docker image
            image_name = f"airseal-app:{os.path.basename(self.file_path)}"
            subprocess.run(['docker', 'build', '-t', image_name, self.temp_dir], check=True)
            return image_name

        except subprocess.CalledProcessError as e:
            print(f"Docker build failed: {str(e)}")
            return None
        except Exception as e:
            print(f"Error building Docker image: {str(e)}")
            return None

    def cleanup(self):
        """Clean up temporary directory"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error cleaning up: {str(e)}")
