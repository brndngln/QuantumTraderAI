
import json
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class MetaLearner:
    def __init__(self, 
                 history_file: str = 'data/trade_history.json',
                 lookback_window: int = 30,
                 confidence_threshold: float = 0.6,
                 min_samples: int = 10):
        self.history_file = history_file
        self.strategy_scores = {}
        self.lookback_window = lookback_window
        self.confidence_threshold = confidence_threshold
        self.min_samples = min_samples
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.feature_columns = ['pnl', 'volatility', 'market_trend', 'time_of_day']
        self.last_update: Optional[datetime] = None

    def load_history(self) -> List[Dict]:
        """Load and validate trade history"""
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
            if not isinstance(history, list):
                raise ValueError("Trade history must be a list")
            return history
        except FileNotFoundError:
            logger.warning("Trade history file not found, starting fresh")
            return []
        except Exception as e:
            logger.error(f"Error loading history: {str(e)}")
            raise

    def _calculate_features(self, trade: Dict) -> Dict:
        """Calculate advanced features for each trade"""
        features = {
            'pnl': trade.get('pnl', 0),
            'volatility': trade.get('volatility', 0),
            'market_trend': trade.get('market_trend', 0),
            'time_of_day': self._get_time_of_day_feature(trade.get('timestamp', datetime.now().isoformat())),
            'duration': trade.get('duration', 0),
            'risk_reward_ratio': trade.get('risk_reward_ratio', 0),
            'position_size': trade.get('position_size', 0)
        }
        return features

    def _get_time_of_day_feature(self, timestamp: str) -> float:
        """Convert timestamp to time of day feature"""
        try:
            dt = datetime.fromisoformat(timestamp)
            return (dt.hour + dt.minute/60) / 24
        except:
            return 0.5  # Default to midday if timestamp is invalid

    def _prepare_features(self, history: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and labels for training"""
        features = []
        labels = []
        
        for trade in history:
            try:
                feat = self._calculate_features(trade)
                features.append([feat[col] for col in self.feature_columns])
                labels.append(trade.get('strategy_performance', 0))
            except Exception as e:
                logger.warning(f"Error preparing features for trade: {str(e)}")
                continue
                
        if len(features) < self.min_samples:
            raise ValueError(f"Not enough samples ({len(features)} < {self.min_samples})")
            
        return np.array(features), np.array(labels)

    def evaluate_strategies(self, history: List[Dict]) -> Dict[str, float]:
        """Evaluate strategies using advanced statistical methods"""
        scores = {}
        strategy_data = {}
        
        for trade in history:
            strategy = trade.get("strategy")
            if strategy not in strategy_data:
                strategy_data[strategy] = []
            strategy_data[strategy].append(trade)
        
        for strategy, trades in strategy_data.items():
            try:
                pnls = [t.get('pnl', 0) for t in trades]
                if len(pnls) < self.min_samples:
                    continue
                    
                # Calculate statistical metrics
                mean = np.mean(pnls)
                std = np.std(pnls)
                sharpe = mean / std if std != 0 else 0
                
                # Calculate confidence intervals
                confidence = norm.interval(0.95, loc=mean, scale=std/np.sqrt(len(pnls)))
                
                # Calculate risk-adjusted performance
                risk_adjusted = mean / (std + 1e-6)
                
                scores[strategy] = {
                    'mean': mean,
                    'std': std,
                    'sharpe': sharpe,
                    'confidence': confidence,
                    'risk_adjusted': risk_adjusted,
                    'n_samples': len(pnls)
                }
            except Exception as e:
                logger.error(f"Error evaluating strategy {strategy}: {str(e)}")
                continue
        
        # Sort by risk-adjusted performance
        sorted_scores = sorted(
            [(s, v['risk_adjusted']) for s, v in scores.items()],
            key=lambda x: -x[1]
        )
        
        return {s: score for s, score in sorted_scores}

    def train_model(self, force: bool = False) -> bool:
        """Train the meta-learning model"""
        try:
            if not force and self.last_update and (datetime.now() - self.last_update).days < 7:
                logger.info("Model training not required - recent training exists")
                return False
                
            history = self.load_history()
            if not history:
                logger.warning("No history available for training")
                return False
                
            X, y = self._prepare_features(history)
            X_scaled = self.scaler.fit_transform(X)
            
            self.model.fit(X_scaled, y)
            self.last_update = datetime.now()
            logger.info("Meta-learning model trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training meta-learning model: {str(e)}")
            return False

    def recommend_strategies(self) -> List[Tuple[str, float]]:
        """Recommend strategies with confidence scores"""
        try:
            history = self.load_history()
            self.strategy_scores = self.evaluate_strategies(history)
            
            # Train model if enough data exists
            if len(history) >= self.min_samples:
                self.train_model()
                
            recommendations = []
            for strategy, score in self.strategy_scores.items():
                confidence = self.confidence_score(strategy)
                if confidence >= self.confidence_threshold:
                    recommendations.append((strategy, confidence))
                    
            return sorted(recommendations, key=lambda x: -x[1])
            
        except Exception as e:
            logger.error(f"Error in strategy recommendation: {str(e)}")
            return []

    def confidence_score(self, strategy: str) -> float:
        """Calculate confidence score using multiple metrics"""
        if strategy not in self.strategy_scores:
            return 0.0
            
        stats = self.strategy_scores[strategy]
        
        # Calculate weighted confidence score
        score = (
            0.4 * stats['sharpe'] +
            0.3 * stats['risk_adjusted'] +
            0.2 * (stats['n_samples'] / self.min_samples) +
            0.1 * (1 - abs(stats['std']))
        )
        
        return max(0, min(1, score))

    def get_strategy_metrics(self, strategy: str) -> Dict:
        """Get detailed metrics for a specific strategy"""
        if strategy not in self.strategy_scores:
            return {
                'error': f'Strategy {strategy} not found',
                'status': 'not_found'
            }
            
        stats = self.strategy_scores[strategy]
        return {
            'strategy': strategy,
            'mean_pnl': stats['mean'],
            'std_pnl': stats['std'],
            'sharpe_ratio': stats['sharpe'],
            'confidence_interval': stats['confidence'],
            'risk_adjusted_score': stats['risk_adjusted'],
            'sample_size': stats['n_samples'],
            'confidence_score': self.confidence_score(strategy),
            'last_update': self.last_update.isoformat() if self.last_update else None
        }

# Initialize global instance with more robust defaults
meta = MetaLearner(
    history_file='data/trade_history.json',
    lookback_window=60,
    confidence_threshold=0.7,
    min_samples=20
)
