def fix_timeframe_alignment():
    file_path = 'backend/utils/timeframe_alignment.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix imports
    content = content.replace('from typing import List, Dict, Any\nfrom enum import Enum\nfrom datetime import datetime\nimport pandas as pd\nfrom fastapi import HTTPException',
                           'from typing import List, Dict, Any\nfrom enum import Enum\nimport pandas as pd\nfrom fastapi import HTTPException')
    
    # Fix method indentation
    content = content.replace('    def calculate_indicators(self, data: pd.DataFrame, timeframe: Timeframe) -> Dict[str, Any]:\n        """\n        Calculate technical indicators\n        """\n        indicators = {}\n        indicators[\'rsi\'] = self.calculate_rsi(data)\n        indicators[\'macd\'] = self.calculate_macd(data)\n        indicators[\'bb\'] = self.calculate_bollinger_bands(data)\n        return indicators',
                           '    def calculate_indicators(self, data: pd.DataFrame, timeframe: Timeframe) -> Dict[str, Any]:\n        """\n        Calculate technical indicators\n        """\n        indicators = {}\n        indicators[\'rsi\'] = self.calculate_rsi(data)\n        indicators[\'macd\'] = self.calculate_macd(data)\n        indicators[\'bb\'] = self.calculate_bollinger_bands(data)\n        return indicators')
    
    # Fix try-except blocks
    content = content.replace('        except Exception as e:\n            raise HTTPException(\n                status_code=500,\n                detail=f"Error analyzing timeframes: {str(e)}"\n            )',
                           '        except Exception as e:\n            raise HTTPException(\n                status_code=500,\n                detail=f"Error analyzing timeframes: {str(e)}"\n            )')
    
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_timeframe_alignment()
