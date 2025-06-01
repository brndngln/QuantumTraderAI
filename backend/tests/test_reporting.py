import unittest
from datetime import datetime
import pandas as pd
import numpy as np

from backend.reporting import Reporter
from backend.metrics import Metrics
from backend.real_time_analysis import RealTimeAnalyzer
from backend.portfolio_optimizer import PortfolioOptimizer
from backend.cost_analysis import TransactionCostAnalyzer

class TestReporter(unittest.TestCase):
    def setUp(self):
        self.reporter = Reporter(
            window_size=252,
            report_frequency='D'
        )
        
        # Mock data
        self.returns = pd.Series(
            np.random.normal(0, 0.01, 252),
            index=pd.date_range('2023-01-01', periods=252)
        )
        
        self.positions = pd.DataFrame(
            np.random.normal(0, 0.1, (252, 5)),
            index=pd.date_range('2023-01-01', periods=252),
            columns=['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
        )
        
        self.predictions = pd.Series(
            np.random.normal(0, 0.01, 252),
            index=pd.date_range('2023-01-01', periods=252)
        )
        
        self.actuals = pd.Series(
            np.random.normal(0, 0.01, 252),
            index=pd.date_range('2023-01-01', periods=252)
        )

    def test_generate_performance_report(self):
        report = self.reporter.generate_performance_report(
            self.returns,
            self.positions.iloc[-1].to_dict(),
            self.predictions,
            self.actuals
        )
        self.assertIn('sharpe_ratio', report)
        self.assertIn('max_drawdown', report)
        self.assertIn('information_coefficient', report)

    def test_generate_portfolio_report(self):
        report = self.reporter.generate_portfolio_report(
            self.positions,
            self.returns
        )
        self.assertIn('portfolio_metrics', report)
        self.assertIn('position_metrics', report)

    def test_generate_risk_report(self):
        report = self.reporter.generate_risk_report()
        self.assertIn('risk_metrics', report)
        self.assertIn('risk_alerts', report)

    def test_plot_performance(self):
        try:
            self.reporter.plot_performance(self.returns)
        except Exception as e:
            self.fail(f"plot_performance failed: {str(e)}")

    def test_plot_portfolio_analysis(self):
        try:
            self.reporter.plot_portfolio_analysis(self.positions)
        except Exception as e:
            self.fail(f"plot_portfolio_analysis failed: {str(e)}")

    def test_generate_html_report(self):
        html = self.reporter.generate_html_report(
            self.returns,
            self.positions,
            self.predictions,
            self.actuals
        )
        self.assertTrue(len(html) > 0)
        self.assertIn('<html>', html)
        self.assertIn('</html>', html)

    def test_save_report(self):
        try:
            self.reporter.save_report(
                self.returns,
                self.positions,
                self.predictions,
                self.actuals,
                'test_report.html'
            )
            # Verify file exists
            with open('test_report.html', 'r') as f:
                content = f.read()
            self.assertTrue(len(content) > 0)
        except Exception as e:
            self.fail(f"save_report failed: {str(e)}")

if __name__ == '__main__':
    unittest.main()
