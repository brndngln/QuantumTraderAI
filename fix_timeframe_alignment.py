def fix_timeframe_alignment():
    file_path = 'backend/utils/timeframe_alignment.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix calculate_indicators indentation
    content = content.replace('    def calculate_indicators(self, data: pd.DataFrame, timeframe: Timeframe) -> Dict[str, Any]\n-> Dict[str, Any]:\n            """\n        Calculate technical indicators\n            """\n        indicators = {}',
                           '    def calculate_indicators(self, data: pd.DataFrame, timeframe: Timeframe) -> Dict[str, Any]:\n        """\n        Calculate technical indicators\n        """\n        indicators = {}')
    
    # Fix generate_signal indentation
    content = content.replace('    def generate_signal(self, indicators: Dict[str, Any]) -> SignalType:\n            """\n        Generate trading signal based on indicators\n            """\n        # Implementation depends on strategy\n        return SignalType.NEUTRAL',
                           '    def generate_signal(self, indicators: Dict[str, Any]) -> SignalType:\n        """\n        Generate trading signal based on indicators\n        """\n        # Implementation depends on strategy\n        return SignalType.NEUTRAL')
    
    # Fix calculate_signal_confidence indentation
    content = content.replace('    def calculate_signal_confidence(self, indicators: Dict[str, Any]) -> float:\n            """\n        Calculate confidence score for signal\n            """\n        # Implementation depends on strategy\n        return 0.5',
                           '    def calculate_signal_confidence(self, indicators: Dict[str, Any]) -> float:\n        """\n        Calculate confidence score for signal\n        """\n        # Implementation depends on strategy\n        return 0.5')
    
    # Fix calculate_rsi indentation
    content = content.replace('    def calculate_rsi(self, data: pd.DataFrame) -> float:\n            """\n        Calculate RSI\n            """\n        # Implementation\n        return 50.0',
                           '    def calculate_rsi(self, data: pd.DataFrame) -> float:\n        """\n        Calculate RSI\n        """\n        # Implementation\n        return 50.0')
    
    # Fix calculate_macd indentation
    content = content.replace('    def calculate_macd(self, data: pd.DataFrame) -> Dict[str, float]:\n            """\n        Calculate MACD\n            """\n        # Implementation\n        return {\n            \'macd\': 0.0,\n            \'signal\': 0.0\n        }',
                           '    def calculate_macd(self, data: pd.DataFrame) -> Dict[str, float]:\n        """\n        Calculate MACD\n        """\n        # Implementation\n        return {\n            \'macd\': 0.0,\n            \'signal\': 0.0\n        }')
    
    # Fix calculate_bollinger_bands indentation
    content = content.replace('    def calculate_bollinger_bands(self, data: pd.DataFrame) -> Dict[str, float]:\n            """\n        Calculate Bollinger Bands\n            """\n        # Implementation\n        return {\n            \'upper\': 0.0,\n            \'middle\': 0.0,\n            \'lower\': 0.0\n        }',
                           '    def calculate_bollinger_bands(self, data: pd.DataFrame) -> Dict[str, float]:\n        """\n        Calculate Bollinger Bands\n        """\n        # Implementation\n        return {\n            \'upper\': 0.0,\n            \'middle\': 0.0,\n            \'lower\': 0.0\n        }')
    
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_timeframe_alignment()
