import os
import re

def fix_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add missing imports at the top
    if 'from typing import Any' not in content:
        content = 'from typing import Any\n' + content
    if 'from typing import Optional' not in content:
        content = 'from typing import Optional\n' + content
    
    # Fix method definitions and return types
    content = content.replace('def validate_usage(self) -> Dict[str, Any]:\n-> Dict[str, Any]:', 'def validate_usage(self) -> Dict[str, Any]:')
    content = content.replace('def check_compliance(self) -> Dict[str, Any]:\n-> Dict[str, Any]:', 'def check_compliance(self) -> Dict[str, Any]:')
    content = content.replace('def calculate_indicators(self, data: pd.DataFrame, timeframe: Timeframe) -> Dict[str, Any]:\n-> Dict[str, Any]:', 
                             'def calculate_indicators(self, data: pd.DataFrame, timeframe: Timeframe) -> Dict[str, Any]:')
    
    # Fix docstring indentation
    content = content.replace('"""', '    """')
    
    # Fix trade_journal.py class definition
    content = content.replace('market_context: Dict[str, Any]\n    optional: Optional[str] = None\n', 'market_context: Dict[str, Any]\n    optional: Optional[str] = None\n')
    
    # Fix indentation of method bodies
    content = content.replace('    def _save_compliance_record(self, record_type: str, data: Dict[str, Any]) -> None:\n        \n', '    def _save_compliance_record(self, record_type: str, data: Dict[str, Any]) -> None:\n        \n')
    content = content.replace('    def log_action(self, action_type: str, details: Dict[str, Any]) -> None:\n        \n', '    def log_action(self, action_type: str, details: Dict[str, Any]) -> None:\n        \n')
    content = content.replace('    def get_disclaimer(self) -> str:\n        \n', '    def get_disclaimer(self) -> str:\n        \n')
    content = content.replace('    def get_user_agreement(self) -> str:\n        \n', '    def get_user_agreement(self) -> str:\n        \n')
    content = content.replace('    def get_privacy_policy(self) -> str:\n        \n', '    def get_privacy_policy(self) -> str:\n        \n')
    
    # Remove duplicate imports
    content = content.replace('from fastapi import HTTPException\nfrom fastapi import HTTPException\n', 'from fastapi import HTTPException\n')
    content = content.replace('import pandas as pd\nimport pandas as pd\n', 'import pandas as pd\n')
    
    # Remove unused variables
    content = content.replace('trade_id = f"trade_{datetime.now().strftime("%Y%m%d_%H%M%S")}"\n', '')
    
    # Fix docstring formatting
    content = content.replace('""""', '"""')
    content = content.replace('"""""', '"""')
    
    with open(file_path, 'w') as f:
        f.write(content)

# List of files to fix
files_to_fix = [
    'backend/utils/cooldown_manager.py',
    'backend/utils/legal.py',
    'backend/utils/timeframe_alignment.py',
    'backend/utils/trade_journal.py'
]

for file in files_to_fix:
    if os.path.exists(file):
        fix_file(file)
    else:
        print(f"Warning: {file} not found")
