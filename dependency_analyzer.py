import ast
import os
import sys
import pkg_resources
from pipreqs import pipreqs
import json
from typing import Dict, List, Set
import importlib

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
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy the target file to temp directory
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
        
        # Get installed versions
        installed_versions = analyzer.get_installed_versions(direct_imports)
        
        return {
            'direct_imports': direct_imports,
            'package_requirements': package_requirements,
            'installed_versions': installed_versions
        }
    
    except Exception as e:
        raise Exception(f"Dependency analysis failed: {str(e)}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python dependency_analyzer.py <python_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        deps = analyze_dependencies(file_path)
        print(json.dumps(deps, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
