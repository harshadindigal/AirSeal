import ast
import os
import sys
import pipreqs
import json

class DependencyAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.dependencies = set()

    def extract_imports(self):
        """
        Extract imported modules from Python file using AST
        """
        with open(self.file_path, 'r') as file:
            tree = ast.parse(file.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    self.dependencies.add(n.name.split('.')[0])
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.dependencies.add(node.module.split('.')[0])
        
        return list(self.dependencies)

    def get_package_requirements(self):
        """
        Use pipreqs to get actual package requirements
        """
        temp_requirements_path = 'temp_requirements.txt'
        pipreqs.process_imports(
            path=os.path.dirname(self.file_path), 
            output=temp_requirements_path
        )
        
        with open(temp_requirements_path, 'r') as f:
            requirements = f.read().splitlines()
        
        os.remove(temp_requirements_path)
        
        return requirements

def analyze_dependencies(file_path):
    """
    Comprehensive dependency analysis
    """
    analyzer = DependencyAnalyzer(file_path)
    
    # Extract direct imports
    direct_imports = analyzer.extract_imports()
    
    # Get package requirements
    package_requirements = analyzer.get_package_requirements()
    
    return {
        'direct_imports': direct_imports,
        'package_requirements': package_requirements
    }

# For standalone testing
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python dependency_analyzer.py <python_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    deps = analyze_dependencies(file_path)
    print(json.dumps(deps, indent=2))
