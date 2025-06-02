import os

def fix_trade_journal():
    file_path = 'backend/utils/trade_journal.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix imports - remove duplicates and organize
    content = content.replace('from typing import Optional\nfrom typing import Any\nimport json\nfrom typing import Dict\nimport pandas as pd\nfrom fastapi import HTTPException\nimport os\nfrom typing import List, Dict, Any, Optional\nfrom fastapi import HTTPException\nimport os\nimport datetime\nimport json\nimport pandas as pd\nimport pandas as pd\nfrom fastapi import HTTPException\nfrom datetime import datetime\nfrom fastapi import HTTPException\nfrom redis import asyncio as aioredis\nfrom pydantic import BaseModel\nfrom enum import Enum\nimport matplotlib.pyplot as plt\nimport mplfinance as mpf',
                           'from typing import Any, Dict, List, Optional\nfrom datetime import datetime\nimport json\nimport os\nimport pandas as pd\nfrom fastapi import HTTPException\nfrom redis import asyncio as aioredis\nfrom pydantic import BaseModel\nfrom enum import Enum\nimport matplotlib.pyplot as plt\nimport mplfinance as mpf')
    
    # Fix method definitions and indentation
    content = content.replace('def log_trade(self, entry: TradeEntry, exit: TradeExit) -> None:\n        """\n        Log a complete trade with entry and exit\n            """\n        try:\n            # Create trade record\n            trade_id = f"trade_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}\"\n            trade_record = {',
                           '    def log_trade(self, entry: TradeEntry, exit: TradeExit) -> None:\n        """\n        Log a complete trade with entry and exit\n        """\n        try:\n            # Create trade record\n            trade_record = {')
    
    # Fix try-except blocks indentation
    content = content.replace('try:\n            # Load trades for day\n            daily_file = os.path.join(self.logs_dir, f\'trade_journal_{date_str}.json\')\n            if os.path.exists(daily_file):\n                with open(daily_file, \"r\") as f:\n                    trades = json.load(f)\n            else:\n                trades = []\n            trades.append(trade_record)\n            with open(daily_file, \"w\") as f:\n                json.dump(trades, f, indent=2)\n            await self.generate_daily_summary(date_str)\n        except Exception as e:\n            raise HTTPException(status_code=500, detail=f\"Error logging trade: {str(e)}\")',
                           '        try:\n            # Load trades for day\n            daily_file = os.path.join(self.logs_dir, f\'trade_journal_{date_str}.json\')\n            if os.path.exists(daily_file):\n                with open(daily_file, \"r\") as f:\n                    trades = json.load(f)\n            else:\n                trades = []\n            trades.append(trade_record)\n            with open(daily_file, \"w\") as f:\n                json.dump(trades, f, indent=2)\n            await self.generate_daily_summary(date_str)\n        except Exception as e:\n            raise HTTPException(status_code=500, detail=f\"Error logging trade: {str(e)}\")')
    
    # Fix docstrings indentation
    content = content.replace('"""\n    Generate daily trade summary\n        """', '    """\n    Generate daily trade summary\n    """')
    
    # Fix class indentation
    content = content.replace('class TradeSummary(BaseModel):\n    date: datetime', 'class TradeSummary(BaseModel):\n        date: datetime')
    
    # Fix method indentation
    content = content.replace('    async def generate_daily_summary(self, date_str: str) -> None:',
                             '    async def generate_daily_summary(self, date_str: str) -> None:')
    
    # Fix try-except blocks in generate_daily_summary
    content = content.replace('try:\n            # Load trades for day\n            daily_file = os.path.join(self.logs_dir, f\'trade_journal_{date_str}.json\')\n            if os.path.exists(daily_file):\n                with open(daily_file, \"r\") as f:\n                    trades = json.load(f)\n            else:\n                trades = []\n            trades.append(trade_record)\n            with open(daily_file, \"w\") as f:\n                json.dump(trades, f, indent=2)\n            await self.generate_daily_summary(date_str)\n        except Exception as e:\n            raise HTTPException(status_code=500, detail=f\"Error logging trade: {str(e)}\")',
                           '        try:\n            # Load trades for day\n            daily_file = os.path.join(self.logs_dir, f\'trade_journal_{date_str}.json\')\n            if os.path.exists(daily_file):\n                with open(daily_file, \"r\") as f:\n                    trades = json.load(f)\n            else:\n                trades = []\n            trades.append(trade_record)\n            with open(daily_file, \"w\") as f:\n                json.dump(trades, f, indent=2)\n            await self.generate_daily_summary(date_str)\n        except Exception as e:\n            raise HTTPException(status_code=500, detail=f\"Error logging trade: {str(e)}\")')
    
    # Fix calculate_sharpe_ratio indentation
    content = content.replace('def calculate_sharpe_ratio(self, trades: List[Dict]) -> float:\n            """\n        Calculate Sharpe ratio for trades\n            """\n        returns = [t[\'exit\'][\'profit\'] for t in trades]\n        if not returns:\n            return 0.0',
                           '    def calculate_sharpe_ratio(self, trades: List[Dict]) -> float:\n        """\n        Calculate Sharpe ratio for trades\n        """\n        returns = [t[\'exit\'][\'profit\'] for t in trades]\n        if not returns:\n            return 0.0')
    
    # Fix generate_screenshot indentation
    content = content.replace('def generate_screenshot(self, symbol: str, timeframe: str = \'1d\') -> str:\n            """\n        Generate chart screenshot for trade analysis\n            """\n        try:\n            # Get historical data (implementation depends on data source)\n            data = await self.get_historical_data(symbol, timeframe)',
                           '    def generate_screenshot(self, symbol: str, timeframe: str = \'1d\') -> str:\n        """\n        Generate chart screenshot for trade analysis\n        """\n        try:\n            # Get historical data (implementation depends on data source)\n            data = await self.get_historical_data(symbol, timeframe)')
    
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_trade_journal()
