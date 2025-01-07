from dataclasses import dataclass
from typing import List, Optional, Dict, Set
from pathlib import Path
import os
import ast
import re
import subprocess
import json
import tempfile

@dataclass
class Dependency:
    type: str  # 'package', 'module', 'class', 'function', 'crate', 'header'
    name: str  # Full name/path
    version: Optional[str] = None
    source: Optional[str] = None
    dependencies: Set[str] = None
    language: str = ''  # 'python', 'java', 'javascript', 'cpp', 'go', 'rust'

    def __hash__(self):
        return hash((self.type, self.name, self.version, self.language))

class DependencyAnalyzer:
    def __init__(self):
        self.language_handlers = {
            '.py': self._analyze_python,
            '.java': self._analyze_java,
            '.js': self._analyze_javascript,
            '.cpp': self._analyze_cpp,
            '.hpp': self._analyze_cpp,
            '.h': self._analyze_cpp,
            '.go': self._analyze_go,
            '.rs': self._analyze_rust
        }
        self.analyzed_paths = set()
        self.project_root = None

    def analyze(self, file_path: str) -> List[Dependency]:
        """Analyze file and all its dependencies recursively"""
        self.project_root = os.path.dirname(os.path.abspath(file_path))
        ext = Path(file_path).suffix
        
        if ext not in self.language_handlers:
            raise ValueError(f"Unsupported file type: {ext}")

        dependencies = set()
        self._analyze_file_recursive(file_path, dependencies)
        return list(dependencies)

    def _analyze_file_recursive(self, file_path: str, all_dependencies: Set[Dependency]) -> None:
        """Recursively analyze a file and its dependencies"""
        if file_path in self.analyzed_paths:
            return
        
        self.analyzed_paths.add(file_path)
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            ext = Path(file_path).suffix
            direct_deps = self.language_handlers[ext](content, file_path)
            all_dependencies.update(direct_deps)

            for dep in direct_deps:
                self._analyze_dependency_recursive(dep, all_dependencies)

        except Exception as e:
            print(f"Error analyzing {file_path}: {str(e)}")

    def _analyze_python(self, content: str, file_path: str) -> Set[Dependency]:
        """Analyze Python dependencies"""
        dependencies = set()
        try:
            tree = ast.parse(content)
            
            # Track imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        dep = self._get_python_package_info(name.name)
                        if dep:
                            dependencies.add(dep)
                            
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dep = self._get_python_package_info(node.module)
                        if dep:
                            dependencies.add(dep)
                            
                # Check for pip requirements
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == 'install_requires':
                        for arg in node.args:
                            if isinstance(arg, ast.List):
                                for elt in arg.elts:
                                    if isinstance(elt, ast.Str):
                                        pkg_name = re.split('[><=~]', elt.s)[0].strip()
                                        dependencies.add(Dependency(
                                            type='package',
                                            name=pkg_name,
                                            language='python'
                                        ))

            # Check for requirements.txt
            req_file = os.path.join(os.path.dirname(file_path), 'requirements.txt')
            if os.path.exists(req_file):
                with open(req_file) as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            pkg_name = re.split('[><=~]', line)[0].strip()
                            dependencies.add(Dependency(
                                type='package',
                                name=pkg_name,
                                language='python'
                            ))
                            
        except Exception as e:
            print(f"Error analyzing Python dependencies: {str(e)}")
            
        return dependencies

    def _analyze_javascript(self, content: str, file_path: str) -> Set[Dependency]:
        """Analyze JavaScript dependencies"""
        dependencies = set()
        
        # Check for require/import statements
        require_pattern = r'(?:require|import)\s*\([\'"]([^\'\"]+)[\'"]\)'
        import_pattern = r'(?:import|export).*?[\'"]([^\'\"]+)[\'"]'
        
        for pattern in [require_pattern, import_pattern]:
            for match in re.finditer(pattern, content):
                dep_name = match.group(1)
                dependencies.add(Dependency(
                    type='module',
                    name=dep_name,
                    language='javascript'
                ))

        # Check package.json
        package_json = os.path.join(os.path.dirname(file_path), 'package.json')
        if os.path.exists(package_json):
            with open(package_json) as f:
                try:
                    data = json.load(f)
                    for dep_type in ['dependencies', 'devDependencies']:
                        if dep_type in data:
                            for name, version in data[dep_type].items():
                                dependencies.add(Dependency(
                                    type='package',
                                    name=name,
                                    version=version,
                                    language='javascript'
                                ))
                except json.JSONDecodeError:
                    pass

        return dependencies

    def _analyze_java(self, content: str, file_path: str) -> Set[Dependency]:
        """Analyze Java dependencies"""
        dependencies = set()
        
        # Check for imports
        import_pattern = r'import\s+([\w.]+(?:\s*\*)?);'
        package_pattern = r'package\s+([\w.]+);'
        
        # Get package dependencies
        package_matches = re.finditer(package_pattern, content)
        for match in package_matches:
            dependencies.add(Dependency(
                type='package',
                name=match.group(1),
                language='java'
            ))

        # Get import dependencies
        import_matches = re.finditer(import_pattern, content)
        for match in import_matches:
            import_path = match.group(1)
            dependencies.add(Dependency(
                type='package',
                name=import_path,
                language='java'
            ))

        # Check build files for dependencies
        build_gradle = os.path.join(os.path.dirname(file_path), 'build.gradle')
        pom_xml = os.path.join(os.path.dirname(file_path), 'pom.xml')
        
        if os.path.exists(build_gradle):
            with open(build_gradle) as f:
                gradle_content = f.read()
                # Look for dependencies in build.gradle
                dep_pattern = r'implementation\s+[\'"]([^\'\"]+)[\'"]'
                for match in re.finditer(dep_pattern, gradle_content):
                    dep_str = match.group(1)
                    parts = dep_str.split(':')
                    if len(parts) >= 2:
                        dependencies.add(Dependency(
                            type='package',
                            name=f"{parts[0]}:{parts[1]}",
                            version=parts[2] if len(parts) > 2 else None,
                            language='java'
                        ))

        elif os.path.exists(pom_xml):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(pom_xml)
                root = tree.getroot()
                
                # Parse Maven dependencies
                for dep in root.findall(".//dependency"):
                    group_id = dep.find('groupId').text
                    artifact_id = dep.find('artifactId').text
                    version = dep.find('version').text if dep.find('version') is not None else None
                    
                    dependencies.add(Dependency(
                        type='package',
                        name=f"{group_id}:{artifact_id}",
                        version=version,
                        language='java'
                    ))
            except Exception as e:
                print(f"Error parsing pom.xml: {str(e)}")

        return dependencies

    def _analyze_cpp(self, content: str, file_path: str) -> Set[Dependency]:
        """Analyze C++ dependencies"""
        dependencies = set()
        
        # Check for includes
        system_include_pattern = r'#include\s*<([^>]+)>'
        local_include_pattern = r'#include\s*"([^"]+)"'
        
        # System includes
        for match in re.finditer(system_include_pattern, content):
            dependencies.add(Dependency(
                type='header',
                name=match.group(1),
                language='cpp'
            ))

        # Local includes
        for match in re.finditer(local_include_pattern, content):
            include_path = match.group(1)
            full_path = os.path.join(os.path.dirname(file_path), include_path)
            
            if os.path.exists(full_path):
                dependencies.add(Dependency(
                    type='header',
                    name=include_path,
                    source=full_path,
                    language='cpp'
                ))

        # Check for CMakeLists.txt
        cmake_file = os.path.join(os.path.dirname(file_path), 'CMakeLists.txt')
        if os.path.exists(cmake_file):
            with open(cmake_file) as f:
                cmake_content = f.read()
                # Look for find_package commands
                package_pattern = r'find_package\s*\(\s*(\w+)(?:\s+(\d+(?:\.\d+)*))?\s*\)'
                for match in re.finditer(package_pattern, cmake_content):
                    dependencies.add(Dependency(
                        type='package',
                        name=match.group(1),
                        version=match.group(2),
                        language='cpp'
                    ))

        return dependencies

    def _analyze_go(self, content: str, file_path: str) -> Set[Dependency]:
        """Analyze Go dependencies"""
        dependencies = set()
        
        # Check for imports
        import_block_pattern = r'import\s*\((.*?)\)'
        single_import_pattern = r'import\s+"([^"]+)"'
        
        # Block imports
        for match in re.finditer(import_block_pattern, content, re.DOTALL):
            imports = match.group(1).strip().split('\n')
            for imp in imports:
                imp = imp.strip().strip('"')
                if imp and not imp.startswith('//'):
                    dependencies.add(Dependency(
                        type='package',
                        name=imp,
                        language='go'
                    ))

        # Single imports
        for match in re.finditer(single_import_pattern, content):
            dependencies.add(Dependency(
                type='package',
                name=match.group(1),
                language='go'
            ))

        # Check go.mod file
        go_mod = os.path.join(os.path.dirname(file_path), 'go.mod')
        if os.path.exists(go_mod):
            with open(go_mod) as f:
                for line in f:
                    if line.startswith('require '):
                        parts = line.split()
                        if len(parts) >= 2:
                            dependencies.add(Dependency(
                                type='package',
                                name=parts[1],
                                version=parts[2] if len(parts) > 2 else None,
                                language='go'
                            ))

        return dependencies

    def _analyze_rust(self, content: str, file_path: str) -> Set[Dependency]:
        """Analyze Rust dependencies"""
        dependencies = set()
        
        # Check for use statements
        use_pattern = r'use\s+((?:(?:crate|self|super)::)?\w+(?:::\w+)*)'
        
        for match in re.finditer(use_pattern, content):
            dependencies.add(Dependency(
                type='module',
                name=match.group(1),
                language='rust'
            ))

        # Check Cargo.toml for dependencies
        cargo_toml = os.path.join(os.path.dirname(file_path), 'Cargo.toml')
        if os.path.exists(cargo_toml):
            try:
                import toml
                with open(cargo_toml) as f:
                    cargo_data = toml.load(f)
                    
                for section in ['dependencies', 'dev-dependencies']:
                    if section in cargo_data:
                        for name, info in cargo_data[section].items():
                            version = info if isinstance(info, str) else info.get('version')
                            dependencies.add(Dependency(
                                type='crate',
                                name=name,
                                version=version,
                                language='rust'
                            ))
            except Exception as e:
                print(f"Error parsing Cargo.toml: {str(e)}")

        return dependencies

    def _analyze_dependency_recursive(self, dep: Dependency, all_dependencies: Set[Dependency]) -> None:
        """Recursively analyze a dependency's dependencies"""
        if not dep.source:
            return

        # If we have source code, analyze it
        if os.path.exists(dep.source):
            self._analyze_file_recursive(dep.source, all_dependencies)
