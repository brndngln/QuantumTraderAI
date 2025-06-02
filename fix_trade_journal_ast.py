import ast
import astor
import os

def fix_indentation(node):
    if isinstance(node, ast.ClassDef):
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                fix_indentation(child)
    elif isinstance(node, ast.FunctionDef):
        # Fix docstring indentation
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            docstring = node.body[0].value.s
            docstring_lines = docstring.split('\n')
            fixed_docstring = '\n'.join(line.strip() for line in docstring_lines)
            node.body[0].value.s = fixed_docstring
        
        # Fix try-except blocks
        for stmt in node.body:
            if isinstance(stmt, ast.Try):
                stmt.body = [ast.fix_missing_locations(stmt) for stmt in stmt.body]
                stmt.handlers = [ast.fix_missing_locations(handler) for handler in stmt.handlers]
                if stmt.orelse:
                    stmt.orelse = [ast.fix_missing_locations(stmt) for stmt in stmt.orelse]
                if stmt.finalbody:
                    stmt.finalbody = [ast.fix_missing_locations(stmt) for stmt in stmt.finalbody]
    
    return node

def fix_trade_journal():
    file_path = 'backend/utils/trade_journal.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    try:
        # Parse the file into AST
        tree = ast.parse(content)
        
        # Fix indentation issues
        tree = fix_indentation(tree)
        
        # Convert AST back to code
        fixed_code = astor.to_source(tree)
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(fixed_code)
            
        print("Successfully fixed indentation issues")
        
    except SyntaxError as e:
        print(f"Syntax error in file: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    fix_trade_journal()
