import ast
import os
import sys
import pkg_resources
from pipreqs import pipreqs
import subprocess
import tempfile
import json
from typing import Dict, List, Set


class DependencyAnalyzer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.dependencies = set()
        self.stdlib_modules = self._get_stdlib_modules()

    def _get_stdlib_modules(self) -> Set[str]:
        """Get a set of Python standard library module names."""
        return set(sys.stdlib_module_names)

    def extract_imports(self) -> List[str]:
        """Extract imported modules from Python file using AST"""
        with open(self.file_path, 'r') as file:
            try:
                tree = ast.parse(file.read())
            except SyntaxError as e:
                raise ValueError(f"Invalid Python file: {str(e)}")

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    base_module = n.name.split('.')[0]
                    if base_module not in self.stdlib_modules:
                        self.dependencies.add(base_module)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    base_module = node.module.split('.')[0]
                    if base_module not in self.stdlib_modules:
                        self.dependencies.add(base_module)
        
        return list(self.dependencies)

    def get_package_requirements(self) -> List[str]:
        """Use pipreqs to get package requirements with versions"""
        try:
            # Create a temporary directory for pipreqs output
            with tempfile.TemporaryDirectory() as temp_dir:
                import shutil
                temp_file_path = os.path.join(temp_dir, os.path.basename(self.file_path))
                shutil.copy2(self.file_path, temp_file_path)

                # Run pipreqs on the temp directory
                requirements_file = os.path.join(temp_dir, "requirements.txt")
                pipreqs.init({
                    '<path>': temp_dir,
                    '--savepath': requirements_file,
                    '--use-local': None,
                    '--force': True,
                    '--encoding': 'utf-8'
                })

                # Read requirements if file exists
                if os.path.exists(requirements_file):
                    with open(requirements_file, 'r') as f:
                        requirements = f.read().splitlines()
                    return requirements
                return []

        except Exception as e:
            print(f"Warning: Error getting package versions: {str(e)}")
            # Fallback: return just the package names without versions
            return [pkg for pkg in self.dependencies]

    def get_installed_versions(self, packages: List[str]) -> Dict[str, str]:
        """Get installed versions of packages"""
        versions = {}
        for package in packages:
            try:
                pkg = pkg_resources.working_set.by_key[package]
                versions[package] = pkg.version
            except KeyError:
                versions[package] = "not installed"
        return versions


def get_all_dependencies(requirements: List[str]) -> List[str]:
    """
    Resolve all dependencies and their versions using pip-tools
    """
    try:
        with tempfile.NamedTemporaryFile('w', delete=False) as req_file:
            req_file.write('\n'.join(requirements))
            req_path = req_file.name

        # Use pip-tools to resolve dependencies
        output = subprocess.check_output(
            ['pip-compile', '--output-file=-', req_path],
            universal_newlines=True
        )
        
        # Parse resolved dependencies
        resolved_dependencies = [
            line for line in output.splitlines() if not line.startswith('#') and line.strip()
        ]
        return resolved_dependencies
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to resolve dependencies: {str(e)}")


def analyze_dependencies(file_path: str) -> Dict:
    """
    Comprehensive dependency analysis
    Returns dict with direct imports and their requirements
    """
    analyzer = DependencyAnalyzer(file_path)
    
    try:
        # Extract direct imports
        direct_imports = analyzer.extract_imports()
        
        # Get package requirements with versions
        package_requirements = analyzer.get_package_requirements()

        # Resolve all transitive dependencies
        all_dependencies = get_all_dependencies(package_requirements)
        
        # Get installed versions
        installed_versions = analyzer.get_installed_versions(direct_imports)
        
        return {
            'direct_imports': direct_imports,
            'package_requirements': all_dependencies,
            'installed_versions': installed_versions
        }
    
    except Exception as e:
        raise Exception(f"Dependency analysis failed: {str(e)}")
