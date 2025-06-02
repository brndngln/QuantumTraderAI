from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from fastapi import HTTPException
import plotly.graph_objects as go
from enum import Enum
import json

logger = logging.getLogger(__name__)

# Define macro indicators
MACRO_INDICATORS = {
    'economic': [
        'GDP',
        'Inflation',
        'Unemployment',
        'Interest Rates',
        'PMI'
    ],
    'political': [
        'Elections',
        'Trade Policies',
        'Regulations',
        'Geopolitical'
    ],
    'market': [
        'Volatility',
        'Sentiment',
        'Liquidity',
        'Valuation'
    ]
}

class RiskTier(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class MacroIndicator(BaseModel):
    category: str
    name: str
    value: float
    trend: float
    timestamp: datetime
    risk_tier: RiskTier

class MacroHeatmap:
    def __init__(self):
        self.indicators = {}
        self.last_update = None
        self.risk_matrix = {}
        
    def update_indicator(self, indicator: MacroIndicator) -> Dict:
        """
        Update a macro indicator
        
        Args:
            indicator: MacroIndicator object
            
        Returns:
            Dict containing updated risk matrix
        """
        try:
            # Store indicator
            key = f"{indicator.category}_{indicator.name}"
            self.indicators[key] = indicator
            self.last_update = datetime.now()
            
            # Update risk matrix
            self._update_risk_matrix()
            
            return self.get_risk_matrix()
            
        except Exception as e:
            logger.error(f"Error updating indicator: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error updating indicator: {str(e)}"
            )
            
    def get_heatmap_data(self) -> Dict:
        """
        Get data for heatmap visualization
        
        Returns:
            Dict containing:
            - x: Categories
            - y: Indicators
            - z: Values
            - colorscale: Color scale
        """
        try:
            categories = list(MACRO_INDICATORS.keys())
            values = np.zeros((len(categories), len(categories)))
            
            # Fill matrix
            for i, cat1 in enumerate(categories):
                for j, cat2 in enumerate(categories):
                    values[i, j] = self._calculate_correlation(cat1, cat2)
            
            return {
                'x': categories,
                'y': categories,
                'z': values.tolist(),
                'colorscale': 'RdYlGn',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting heatmap data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting heatmap data: {str(e)}"
            )
            
    def get_risk_matrix(self) -> Dict:
        """
        Get current risk matrix
        
        Returns:
            Dict containing:
            - economic: Economic risk scores
            - political: Political risk scores
            - market: Market risk scores
            - overall: Overall risk score
        """
        try:
            return self.risk_matrix
            
        except Exception as e:
            logger.error(f"Error getting risk matrix: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting risk matrix: {str(e)}"
            )
            
    def _update_risk_matrix(self) -> None:
        """
        Update risk matrix based on current indicators
        """
        try:
            # Initialize matrix
            self.risk_matrix = {
                'economic': 0.0,
                'political': 0.0,
                'market': 0.0,
                'overall': 0.0
            }
            
            # Calculate category scores
            for category in MACRO_INDICATORS:
                indicators = [
                    ind for key, ind in self.indicators.items()
                    if ind.category == category
                ]
                
                if indicators:
                    # Calculate weighted average
                    values = np.array([ind.value for ind in indicators])
                    weights = np.array([abs(ind.trend) for ind in indicators])
                    weighted_avg = np.average(values, weights=weights)
                    
                    # Normalize to 0-1 range
                    normalized = (weighted_avg - min(values)) / (max(values) - min(values))
                    
                    # Store in matrix
                    self.risk_matrix[category] = float(normalized)
            
            # Calculate overall risk
            category_weights = {
                'economic': 0.4,
                'political': 0.3,
                'market': 0.3
            }
            
            overall = sum(
                self.risk_matrix[cat] * weight
                for cat, weight in category_weights.items()
            )
            
            self.risk_matrix['overall'] = float(overall)
            
        except Exception as e:
            logger.error(f"Error updating risk matrix: {str(e)}")
            
    def _calculate_correlation(self, cat1: str, cat2: str) -> float:
        """
        Calculate correlation between two categories
        """
        try:
            # Get indicators for both categories
            indicators1 = [
                ind for key, ind in self.indicators.items()
                if ind.category == cat1
            ]
            indicators2 = [
                ind for key, ind in self.indicators.items()
                if ind.category == cat2
            ]
            
            if not indicators1 or not indicators2:
                return 0.0
                
            # Calculate correlation
            values1 = np.array([ind.value for ind in indicators1])
            values2 = np.array([ind.value for ind in indicators2])
            
            return float(np.corrcoef(values1, values2)[0, 1])
            
        except Exception as e:
            logger.error(f"Error calculating correlation: {str(e)}")
            return 0.0
            
    def generate_heatmap(self) -> str:
        """
        Generate heatmap visualization
        
        Returns:
            HTML string of the heatmap
        """
        try:
            data = self.get_heatmap_data()
            
            fig = go.Figure(data=go.Heatmap(
                z=data['z'],
                x=data['x'],
                y=data['y'],
                colorscale=data['colorscale'],
                zmin=-1,
                zmax=1
            ))
            
            fig.update_layout(
                title='Macro Indicator Correlation Heatmap',
                xaxis_title='Category',
                yaxis_title='Category',
                width=800,
                height=800
            )
            
            return fig.to_html(full_html=False)
            
        except Exception as e:
            logger.error(f"Error generating heatmap: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating heatmap: {str(e)}"
            )
            
    def get_strategy_recommendations(self) -> Dict:
        """
        Get trading strategy recommendations based on risk matrix
        
        Returns:
            Dict containing:
            - risk_level: Overall risk level
            - strategy: Recommended strategy
            - confidence: Confidence score
            - factors: Contributing factors
        """
        try:
            risk_level = self.risk_matrix['overall']
            
            # Determine strategy based on risk
            if risk_level < 0.3:
                strategy = 'aggressive'
            elif risk_level < 0.6:
                strategy = 'balanced'
            else:
                strategy = 'defensive'
            
            # Calculate confidence
            confidence = 1.0 - abs(risk_level - 0.5)
            
            # Get contributing factors
            factors = {
                'economic': self.risk_matrix['economic'],
                'political': self.risk_matrix['political'],
                'market': self.risk_matrix['market']
            }
            
            return {
                'risk_level': float(risk_level),
                'strategy': strategy,
                'confidence': float(confidence),
                'factors': factors,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting recommendations: {str(e)}"
            )
