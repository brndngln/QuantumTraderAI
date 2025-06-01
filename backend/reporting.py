import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from backend.metrics import Metrics
from backend.real_time_analysis import real_time_analyzer
from backend.portfolio_optimizer import portfolio_optimizer
from backend.cost_analysis import cost_analyzer

logger = logging.getLogger(__name__)

class Reporter:
    def __init__(self,
                 window_size: int = 252,
                 report_frequency: str = 'D',
                 metrics: List[str] = None):
        """
        Initialize reporter
        
        Args:
            window_size: Rolling window size
            report_frequency: Frequency of reports
            metrics: List of metrics to track
        """
        self.window_size = window_size
        self.report_frequency = report_frequency
        self.metrics = metrics or [
            'sharpe_ratio', 'max_drawdown', 'volatility',
            'turnover', 'information_ratio', 'tracking_error'
        ]
        self.metrics_calculator = Metrics()
        self.reports = []
        
    def generate_performance_report(self, 
                                  returns: pd.Series, 
                                  positions: pd.Series, 
                                  predictions: Optional[pd.Series] = None,
                                  actuals: Optional[pd.Series] = None) -> Dict:
        """Generate performance report"""
        try:
            # Calculate basic metrics
            metrics = self.metrics_calculator.calculate_basic_metrics(returns)
            
            # Calculate advanced metrics
            if predictions is not None and actuals is not None:
                metrics.update({
                    'information_coefficient': self.metrics_calculator.calculate_information_coefficient(
                        predictions, actuals
                    ),
                    'tracking_error': self.metrics_calculator.calculate_tracking_error(
                        returns, actuals
                    )
                })
            
            # Calculate risk metrics
            risk_metrics = real_time_analyzer.risk_metrics
            metrics.update(risk_metrics)
            
            # Calculate transaction costs
            cost_metrics = cost_analyzer.get_cost_metrics()
            metrics.update(cost_metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {}

    def generate_portfolio_report(self, 
                                positions: pd.DataFrame, 
                                returns: pd.DataFrame) -> Dict:
        """Generate portfolio report"""
        try:
            # Calculate portfolio metrics
            portfolio_metrics = portfolio_optimizer.calculate_portfolio_metrics(
                returns,
                positions.iloc[-1].to_dict()
            )
            
            # Calculate position metrics
            position_metrics = {
                'total_positions': len(positions.columns),
                'avg_position_size': positions.abs().mean().mean(),
                'max_position_size': positions.abs().max().max(),
                'position_turnover': positions.diff().abs().sum().sum() / positions.abs().sum().sum()
            }
            
            return {
                'portfolio_metrics': portfolio_metrics,
                'position_metrics': position_metrics
            }
            
        except Exception as e:
            logger.error(f"Error generating portfolio report: {str(e)}")
            return {}

    def generate_risk_report(self) -> Dict:
        """Generate risk report"""
        try:
            # Get current risk metrics
            risk_metrics = real_time_analyzer.risk_metrics
            
            # Get risk alerts
            risk_alerts = real_time_analyzer.check_risk_limits()
            
            return {
                'risk_metrics': risk_metrics,
                'risk_alerts': risk_alerts,
                'max_position': risk_metrics.get('max_position', 0),
                'position_count': risk_metrics.get('position_count', 0),
                'concentration': risk_metrics.get('concentration', 0)
            }
            
        except Exception as e:
            logger.error(f"Error generating risk report: {str(e)}")
            return {}

    def plot_performance(self, returns: pd.Series) -> None:
        """Plot performance metrics"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Create DataFrame
            df = pd.DataFrame({
                'Cumulative Returns': (1 + returns).cumprod(),
                'Daily Returns': returns
            })
            
            # Plot cumulative returns
            plt.figure(figsize=(15, 10))
            plt.subplot(2, 2, 1)
            df['Cumulative Returns'].plot()
            plt.title('Cumulative Returns')
            
            # Plot daily returns
            plt.subplot(2, 2, 2)
            df['Daily Returns'].plot(kind='hist', bins=50)
            plt.title('Daily Returns Distribution')
            
            # Plot rolling Sharpe ratio
            plt.subplot(2, 2, 3)
            rolling_sharpe = returns.rolling(self.window_size).apply(
                lambda x: self.metrics_calculator.calculate_sharpe_ratio(x)
            )
            rolling_sharpe.plot()
            plt.title('Rolling Sharpe Ratio')
            
            # Plot drawdown
            plt.subplot(2, 2, 4)
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            drawdown.plot()
            plt.title('Drawdown')
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting performance: {str(e)}")
            raise

    def plot_portfolio_analysis(self, positions: pd.DataFrame) -> None:
        """Plot portfolio analysis"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Create DataFrame
            df = pd.DataFrame(positions)
            
            # Plot position sizes
            plt.figure(figsize=(15, 10))
            plt.subplot(2, 2, 1)
            df.abs().sum().plot(kind='bar')
            plt.title('Position Sizes')
            
            # Plot position turnover
            plt.subplot(2, 2, 2)
            df.diff().abs().sum().plot()
            plt.title('Position Turnover')
            
            # Plot concentration
            plt.subplot(2, 2, 3)
            concentration = df.abs() / df.abs().sum()
            concentration.max().plot()
            plt.title('Position Concentration')
            
            # Plot correlation
            plt.subplot(2, 2, 4)
            corr = df.corr()
            sns.heatmap(corr, annot=True)
            plt.title('Position Correlation')
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting portfolio analysis: {str(e)}")
            raise

    def generate_html_report(self, 
                           returns: pd.Series, 
                           positions: pd.DataFrame,
                           predictions: Optional[pd.Series] = None,
                           actuals: Optional[pd.Series] = None) -> str:
        """Generate HTML report"""
        try:
            # Generate reports
            performance = self.generate_performance_report(
                returns, positions, predictions, actuals
            )
            portfolio = self.generate_portfolio_report(
                positions, returns
            )
            risk = self.generate_risk_report()
            
            # Create HTML
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Trading Performance Report</title>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .metric { margin: 10px; padding: 10px; border: 1px solid #ddd; }
                    .alert { color: red; font-weight: bold; }
                </style>
            </head>
            <body>
                <h1>Trading Performance Report</h1>
                <h2>Performance Metrics</h2>
                <div class="metric">
                    <h3>Basic Metrics</h3>
                    <ul>
                        <li>Sharpe Ratio: {:.2f}</li>
                        <li>Max Drawdown: {:.2%}</li>
                        <li>Annualized Return: {:.2%}</li>
                        <li>Volatility: {:.2%}</li>
                    </ul>
                </div>
                
                <div class="metric">
                    <h3>Risk Metrics</h3>
                    <ul>
                        <li>Max Position Size: {:.2%}</li>
                        <li>Position Count: {}</li>
                        <li>Concentration: {:.2%}</li>
                    </ul>
                </div>
                
                <div class="metric">
                    <h3>Alerts</h3>
                    <ul>
                        <li>{} Risk Alerts</li>
                    </ul>
                </div>
            </body>
            </html>
            """.format(
                performance['sharpe_ratio'],
                performance['max_drawdown'],
                performance['avg_return'],
                performance['volatility'],
                risk['max_position'],
                risk['position_count'],
                risk['concentration'],
                len([a for a in risk['risk_alerts'].values() if a])
            )
            
            return html
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            return """""

    def save_report(self, 
                   returns: pd.Series, 
                   positions: pd.DataFrame,
                   predictions: Optional[pd.Series] = None,
                   actuals: Optional[pd.Series] = None,
                   filename: str = 'report.html') -> None:
        """Save report to file"""
        try:
            html = self.generate_html_report(
                returns, positions, predictions, actuals
            )
            with open(filename, 'w') as f:
                f.write(html)
                
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            raise

# Initialize global instance
reporter = Reporter()
