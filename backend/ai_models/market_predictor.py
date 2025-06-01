import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class MarketPredictor:
    def __init__(self,
                 prediction_horizon: int = 1,
                 lookback_window: int = 60,
                 model_type: str = 'random_forest',
                 feature_importance_threshold: float = 0.01,
                 validation_split: float = 0.2):
        """
        Initialize market predictor
        
        Args:
            prediction_horizon: Number of periods to predict
            lookback_window: Number of past periods to use
            model_type: Type of prediction model
            feature_importance_threshold: Minimum importance for features
            validation_split: Split ratio for validation set
        """
        self.prediction_horizon = prediction_horizon
        self.lookback_window = lookback_window
        self.model_type = model_type
        self.feature_importance_threshold = feature_importance_threshold
        self.validation_split = validation_split
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importances = {}
        self.last_update: Optional[datetime] = None
        
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and target for prediction"""
        try:
            # Create lag features
            features = []
            targets = []
            
            for i in range(len(df) - self.lookback_window - self.prediction_horizon):
                X = df.iloc[i:i + self.lookback_window].values
                y = df.iloc[i + self.lookback_window + self.prediction_horizon]['close']
                features.append(X)
                targets.append(y)
                
            return np.array(features), np.array(targets)
            
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            raise

    def train_model(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train prediction model"""
        try:
            # Split data
            split_idx = int(len(X) * (1 - self.validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Scale features
            X_train = self.scaler.fit_transform(X_train.reshape(-1, X.shape[-1])).reshape(X_train.shape)
            X_val = self.scaler.transform(X_val.reshape(-1, X.shape[-1])).reshape(X_val.shape)
            
            # Initialize model
            if self.model_type == 'random_forest':
                self.model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    random_state=42
                )
            elif self.model_type == 'gradient_boosting':
                self.model = GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=42
                )
            
            # Train model
            self.model.fit(X_train.reshape(X_train.shape[0], -1), y_train)
            
            # Calculate feature importances
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
                self.feature_importances = {
                    f'feature_{i}': importance
                    for i, importance in enumerate(importances)
                    if importance > self.feature_importance_threshold
                }
            
            # Update last update time
            self.last_update = datetime.now()
            logger.info(f"Model trained successfully: {self.model_type}")
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        try:
            if self.model is None:
                raise ValueError("Model not trained yet")
                
            # Scale features
            X = self.scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
            
            # Make predictions
            predictions = self.model.predict(X.reshape(X.shape[0], -1))
            return predictions
            
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            raise

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance"""
        try:
            if self.model is None:
                raise ValueError("Model not trained yet")
                
            predictions = self.predict(X)
            
            # Calculate metrics
            mse = np.mean((predictions - y) ** 2)
            mae = np.mean(np.abs(predictions - y))
            r2 = 1 - (np.sum((predictions - y) ** 2) / 
                      np.sum((y - np.mean(y)) ** 2))
            
            return {
                'mse': mse,
                'mae': mae,
                'r2': r2,
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            raise

    def get_feature_importances(self) -> Dict[str, float]:
        """Get feature importances"""
        return self.feature_importances

    def get_model_metrics(self) -> Dict[str, float]:
        """Get model metrics"""
        try:
            if self.model is None:
                return {}
                
            return {
                'feature_count': len(self.feature_importances),
                'model_type': self.model_type,
                'lookback_window': self.lookback_window,
                'prediction_horizon': self.prediction_horizon,
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            return {}

    def create_prediction_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create complete prediction pipeline"""
        try:
            # Prepare features
            X, y = self.prepare_features(df)
            
            # Train model
            self.train_model(X, y)
            
            # Make predictions
            predictions = self.predict(X)
            
            # Create prediction DataFrame
            prediction_df = pd.DataFrame({
                'timestamp': df.index[self.lookback_window:],
                'actual': y,
                'predicted': predictions,
                'error': predictions - y
            })
            
            return prediction_df
            
        except Exception as e:
            logger.error(f"Error in prediction pipeline: {str(e)}")
            raise

# Initialize global instance
market_predictor = MarketPredictor()
