def fix_trade_journal():
    file_path = 'backend/utils/trade_journal.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix TradeSummary class indentation
    content = content.replace('class TradeSummary(BaseModel):\n        date: datetime\n    trades: List[Dict]\n    total_profit: float\n    win_rate: float\n    avg_profit: float\n    avg_loss: float\n    max_drawdown: float\n    sharpe_ratio: float',
                           'class TradeSummary(BaseModel):\n    date: datetime\n    trades: List[Dict]\n    total_profit: float\n    win_rate: float\n    avg_profit: float\n    avg_loss: float\n    max_drawdown: float\n    sharpe_ratio: float')
    
    # Fix log_trade method indentation
    content = content.replace('async def log_trade(self, entry: TradeEntry, exit: TradeExit) -> None:\n            """\n        Log a complete trade with entry and exit\n            """\n        try:\n            # Create trade record\n            trade_id = f"trade_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}\"\n            trade_record = {',
                           'async def log_trade(self, entry: TradeEntry, exit: TradeExit) -> None:\n    """\n    Log a complete trade with entry and exit\n    """\n    try:\n        # Create trade record\n        trade_record = {')
    
    # Fix try-except blocks indentation in log_trade
    content = content.replace('        except Exception as e:\n            raise HTTPException(\n                status_code=500,\n                detail=f"Error logging trade: {str(e)}"\n            )',
                           '    except Exception as e:\n        raise HTTPException(\n            status_code=500,\n            detail=f"Error logging trade: {str(e)}"\n        )')
    
    # Fix generate_daily_summary indentation
    content = content.replace('async def generate_daily_summary(self, date_str: str) -> None:\n                """\n    Generate daily trade summary\n    """\n        try:\n            # Load trades for day\n            daily_file = os.path.join(self.logs_dir, f\'trade_journal_{date_str}.json\')\n            with open(daily_file, \"r\") as f:\n                trades = json.load(f)',
                           'async def generate_daily_summary(self, date_str: str) -> None:\n    """\n    Generate daily trade summary\n    """\n    try:\n        # Load trades for day\n        daily_file = os.path.join(self.logs_dir, f\'trade_journal_{date_str}.json\')\n        with open(daily_file, \"r\") as f:\n            trades = json.load(f)')
    
    # Fix try-except blocks indentation in generate_daily_summary
    content = content.replace('        except Exception as e:\n            raise HTTPException(\n                status_code=500,\n                detail=f"Error generating summary: {str(e)}"\n            )',
                           '    except Exception as e:\n        raise HTTPException(\n            status_code=500,\n            detail=f"Error generating summary: {str(e)}"\n        )')
    
    # Fix calculate_sharpe_ratio indentation
    content = content.replace('        def calculate_sharpe_ratio(self, trades: List[Dict]) -> float:\n        """\n        Calculate Sharpe ratio for trades\n        """\n        returns = [t[\'exit\'][\'profit\'] for t in trades]\n        if not returns:\n            return 0.0',
                           '    def calculate_sharpe_ratio(self, trades: List[Dict]) -> float:\n        """\n        Calculate Sharpe ratio for trades\n        """\n        returns = [t[\'exit\'][\'profit\'] for t in trades]\n        if not returns:\n            return 0.0')
    
    # Fix generate_screenshot indentation
    content = content.replace('async     def generate_screenshot(self, symbol: str, timeframe: str = \'1d\') -> str:\n        """\n        Generate chart screenshot for trade analysis\n        """\n        try:\n            # Get historical data (implementation depends on data source)\n            data = await self.get_historical_data(symbol, timeframe)',
                           '    async def generate_screenshot(self, symbol: str, timeframe: str = \'1d\') -> str:\n        """\n        Generate chart screenshot for trade analysis\n        """\n        try:\n            # Get historical data (implementation depends on data source)\n            data = await self.get_historical_data(symbol, timeframe)')
    
    # Fix get_historical_data indentation
    content = content.replace('async def get_historical_data(self, symbol: str, timeframe: str) -> pd.DataFrame:\n    """\n    Get historical price data\n    """\n    # Implementation depends on data source\n    return pd.DataFrame()',
                           '    async def get_historical_data(self, symbol: str, timeframe: str) -> pd.DataFrame:\n        """\n        Get historical price data\n        """\n        # Implementation depends on data source\n        return pd.DataFrame()')
    
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_trade_journal()
