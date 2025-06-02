import ast
import os
from pathlib import Path
import re
from typing import Dict, List, Optional

class PythonFileFixer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tree = None
        self.imports = set()
        self._load_file()
        
    def _load_file(self):
        with open(self.file_path, 'r') as f:
            self.content = f.read()
            try:
                self.tree = ast.parse(self.content)
            except SyntaxError as e:
                print(f"Syntax error in {self.file_path}: {e}")

    def _fix_imports(self):
        # Extract all imports
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    self.imports.add(alias.name)
        
        # Remove duplicates
        imports = list(self.imports)
        imports.sort()
        
        # Create new import section
        import_content = """
from typing import Any, Optional, Dict, List
import os
import datetime
import json
import pandas as pd
from fastapi import HTTPException
"""
        
        # Replace existing imports
        self.content = import_content + "\n" + self.content

    def _fix_method_definitions(self):
        # Fix method definitions and return types
        pattern = re.compile(r'def ([\w_]+)\(self\) -> Dict\[str, Any\]:\n-> Dict\[str, Any\]:')
        self.content = pattern.sub(r'def \1(self) -> Dict[str, Any]:', self.content)

    def _fix_docstrings(self):
        # Fix docstring indentation
        pattern = re.compile(r'"""\n\s*([\w\s]+)\n\s*"""')
        self.content = pattern.sub(r'    """\1"""', self.content)

    def _fix_try_except_blocks(self):
        # Fix try-except block indentation
        pattern = re.compile(r'try:\n\s+\# Create trade record\n\s+trade_id = f"trade_{datetime.now().strftime("%Y%m%d_%H%M%S")}"\n\s+trade_record = {')
        self.content = pattern.sub('try:\n            # Create trade record\n            trade_record = {', self.content)

    def fix_file(self):
        self._fix_imports()
        self._fix_method_definitions()
        self._fix_docstrings()
        self._fix_try_except_blocks()
        
        # Write changes back to file
        with open(self.file_path, 'w') as f:
            f.write(self.content)

def fix_files_in_directory(directory: str):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    fixer = PythonFileFixer(file_path)
                    fixer.fix_file()
                    print(f"Fixed {file_path}")
                except Exception as e:
                    print(f"Error fixing {file_path}: {e}")

if __name__ == "__main__":
    # Fix files in the backend/utils directory
    fix_files_in_directory("backend/utils")
