def fix_trade_journal():
    file_path = 'backend/utils/trade_journal.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix log_trade method indentation
    content = content.replace('async def log_trade(self, entry: TradeEntry, exit: TradeExit) -> None:\n    """\n    Log a complete trade with entry and exit\n    """\n    try:\n        # Create trade record\n        trade_record = {',
                           'async def log_trade(self, entry: TradeEntry, exit: TradeExit) -> None:\n        """\n        Log a complete trade with entry and exit\n        """\n        try:\n            # Create trade record\n            trade_record = {')
    
    # Fix generate_daily_summary indentation
    content = content.replace('async def generate_daily_summary(self, date_str: str) -> None:\n    """\n    Generate daily trade summary\n    """\n    try:\n        # Load trades for day\n        daily_file = os.path.join(self.logs_dir, f\'trade_journal_{date_str}.json\')\n        with open(daily_file, \"r\") as f:\n            trades = json.load(f)',
                           'async def generate_daily_summary(self, date_str: str) -> None:\n        """\n        Generate daily trade summary\n        """\n        try:\n            # Load trades for day\n            daily_file = os.path.join(self.logs_dir, f\'trade_journal_{date_str}.json\')\n            with open(daily_file, \"r\") as f:\n                trades = json.load(f)')
    
    # Fix generate_screenshot indentation
    content = content.replace('    async def generate_screenshot(self, symbol: str, timeframe: str = \'1d\') -> str:\n        """\n        Generate chart screenshot for trade analysis\n        """\n        try:\n            # Get historical data (implementation depends on data source)\n            data = await self.get_historical_data(symbol, timeframe)',
                           '    async def generate_screenshot(self, symbol: str, timeframe: str = \'1d\') -> str:\n        """\n        Generate chart screenshot for trade analysis\n        """\n        try:\n            # Get historical data (implementation depends on data source)\n            data = await self.get_historical_data(symbol, timeframe)')
    
    # Fix get_historical_data indentation
    content = content.replace('    async def get_historical_data(self, symbol: str, timeframe: str) -> pd.DataFrame:\n        """\n        Get historical price data\n        """\n        # Implementation depends on data source\n        return pd.DataFrame()',
                           '    async def get_historical_data(self, symbol: str, timeframe: str) -> pd.DataFrame:\n        """\n        Get historical price data\n        """\n        # Implementation depends on data source\n        return pd.DataFrame()')
    
    # Fix docstring indentation
    content = content.replace('        """\n        Log a complete trade with entry and exit\n        """',
                           '        """\n        Log a complete trade with entry and exit\n        """')
    
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_trade_journal()
