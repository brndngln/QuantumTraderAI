import numpy as np
from typing import Dict, Optional
import pandas as pd
from fastapi import HTTPException
import logging
from datetime import datetime
import json

class Reporter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = {
            'performance': [],
            'risk': [],
            'trades': []
        }

    def add_performance_metrics(self, metrics: Dict) -> None:
        """
        Add performance metrics to the report
        """
        try:
            self.metrics['performance'].append({
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics
            })
        except Exception as e:
            self.logger.error(f"Error adding performance metrics: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error adding performance metrics: {str(e)}"
            )

    def add_risk_metrics(self, metrics: Dict) -> None:
        """
        Add risk metrics to the report
        """
        try:
            self.metrics['risk'].append({
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics
            })
        except Exception as e:
            self.logger.error(f"Error adding risk metrics: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error adding risk metrics: {str(e)}"
            )

    def add_trade(self, trade: Dict) -> None:
        """
        Add a trade to the report
        """
        try:
            self.metrics['trades'].append({
                'timestamp': datetime.now().isoformat(),
                'trade': trade
            })
        except Exception as e:
            self.logger.error(f"Error adding trade: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error adding trade: {str(e)}"
            )

    def generate_html_report(self, 
                            predictions: Optional[pd.Series] = None,
                            actuals: Optional[pd.Series] = None) -> str:
        """
        Generate HTML report
        """
        try:
            html = """
            <html>
            <head>
                <title>Trading Report</title>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .metric { margin-bottom: 20px; }
                    .trade { margin-bottom: 10px; padding: 5px; border: 1px solid #ddd; }
                    .positive { color: green; }
                    .negative { color: red; }
                </style>
            </head>
            <body>
                <h1>Trading Report</h1>
            """

            # Add performance metrics
            if self.metrics['performance']:
                html += "<h2>Performance Metrics</h2>"
                for metric in self.metrics['performance']:
                    html += f"<div class='metric'>"
                    html += f"<h3>{metric['timestamp']}</h3>"
                    for key, value in metric['metrics'].items():
                        html += f"<p><strong>{key}:</strong> {value}</p>"
                    html += "</div>"

            # Add risk metrics
            if self.metrics['risk']:
                html += "<h2>Risk Metrics</h2>"
                for metric in self.metrics['risk']:
                    html += f"<div class='metric'>"
                    html += f"<h3>{metric['timestamp']}</h3>"
                    for key, value in metric['metrics'].items():
                        html += f"<p><strong>{key}:</strong> {value}</p>"
                    html += "</div>"

            # Add trades
            if self.metrics['trades']:
                html += "<h2>Trade History</h2>"
                for trade in self.metrics['trades']:
                    html += f"<div class='trade'>"
                    html += f"<h3>{trade['timestamp']}</h3>"
                    for key, value in trade['trade'].items():
                        if isinstance(value, (float, int)):
                            value = f"{value:.2f}"
                        html += f"<p><strong>{key}:</strong> {value}</p>"
                    html += "</div>"

            # Add predictions vs actuals plot if available
            if predictions is not None and actuals is not None:
                html += "<h2>Predictions vs Actuals</h2>"
                html += "<div id='plot'></div>"
                html += "<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>"
                html += "<script>"
                html += "Plotly.newPlot('plot', [{"
                html += "x: [" + json.dumps(predictions.index.tolist()) + "],"
                html += "y: [" + json.dumps(predictions.tolist()) + "],"
                html += "type: 'scatter', name: 'Predictions'" + "}, {"
                html += "x: [" + json.dumps(actuals.index.tolist()) + "],"
                html += "y: [" + json.dumps(actuals.tolist()) + "],"
                html += "type: 'scatter', name: 'Actuals'" + "}]);"
                html += "</script>"

            html += "</body></html>"
            return html

        except Exception as e:
            self.logger.error(f"Error generating HTML report: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating HTML report: {str(e)}"
            )

    def save_report(self, 
                    predictions: Optional[pd.Series] = None,
                    actuals: Optional[pd.Series] = None,
                    filename: str = 'report.html') -> None:
        """
        Save report to file
        """
        try:
            html = self.generate_html_report(predictions, actuals)
            with open(filename, 'w') as f:
                f.write(html)
        except Exception as e:
            self.logger.error(f"Error saving report: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error saving report: {str(e)}"
            )

# Initialize global instance
reporter = Reporter()
