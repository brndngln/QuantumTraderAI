import unittest
from datetime import datetime
import pandas as pd
import numpy as np

from backend.real_time_analysis import RealTimeAnalyzer
from backend.metrics import Metrics
from backend.risk_management import RiskManager
from backend.cost_analysis import TransactionCostAnalyzer
from backend.portfolio_optimizer import PortfolioOptimizer

class TestRealTimeAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = RealTimeAnalyzer(
            window_size=252,
            update_frequency=60,
            risk_threshold=0.02,
            rebalance_threshold=0.05,
            max_position_size=0.05
        )
        
        # Mock data
        self.positions = {
            'AAPL': 0.3,
            'GOOGL': 0.2,
            'MSFT': 0.15,
            'AMZN': 0.15,
            'META': 0.2
        }
        
        self.returns = pd.Series(
            np.random.normal(0, 0.01, 252),
            index=pd.date_range('2023-01-01', periods=252)
        )
        
        self.price_data = pd.DataFrame(
            np.random.normal(100, 10, (252, 5)),
            index=pd.date_range('2023-01-01', periods=252),
            columns=['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
        )

    def test_update_positions(self):
        self.analyzer.update_positions(self.positions)
        self.assertEqual(self.analyzer.current_positions, self.positions)
        self.assertTrue(len(self.analyzer.risk_metrics) > 0)

    def test_check_risk_limits(self):
        alerts = self.analyzer.check_risk_limits()
        self.assertIn('max_position', alerts)
        self.assertIn('position_count', alerts)
        self.assertIn('concentration', alerts)

    def test_calculate_position_sizing(self):
        price = 100
        volatility = 0.1
        portfolio_value = 1000000
        
        size = self.analyzer.calculate_position_sizing(
            price, volatility, portfolio_value
        )
        self.assertGreater(size, 0)
        self.assertLess(size, portfolio_value * self.analyzer.max_position_size)

    def test_optimize_positions(self):
        current_positions = self.positions
        target_positions = {
            'AAPL': 0.4,
            'GOOGL': 0.3,
            'MSFT': 0.2,
            'AMZN': 0.1,
            'META': 0.0
        }
        portfolio_value = 1000000
        
        trades = self.analyzer.optimize_positions(
            current_positions,
            target_positions,
            portfolio_value
        )
        
        self.assertTrue(isinstance(trades, dict))
        self.assertTrue(len(trades) > 0)

    def test_get_real_time_metrics(self):
        metrics = self.analyzer.get_real_time_metrics()
        self.assertIn('risk_metrics', metrics)
        self.assertIn('current_positions', metrics)
        self.assertIn('risk_alerts', metrics)

    def test_plot_real_time_analysis(self):
        try:
            self.analyzer.plot_real_time_analysis()
        except Exception as e:
            self.fail(f"plot_real_time_analysis failed: {str(e)}")

    def test_get_position_adjustments(self):
        adjustments = self.analyzer.get_position_adjustments(
            self.positions,
            self.price_data
        )
        self.assertTrue(isinstance(adjustments, dict))
        self.assertTrue(len(adjustments) > 0)

if __name__ == '__main__':
    unittest.main()
