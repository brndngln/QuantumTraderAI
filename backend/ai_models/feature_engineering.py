import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import ta
from scipy.stats import zscore
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class FeatureEngineer:
    def __init__(self,
                 window_sizes: List[int] = [10, 20, 50, 100],
                 technical_indicators: List[str] = ['RSI', 'MACD', 'BB', 'ADX', 'OBV'],
                 volatility_features: List[str] = ['ATR', 'BBANDS'],
                 volume_features: List[str] = ['OBV', 'MFI'],
                 momentum_features: List[str] = ['RSI', 'ROC', 'ADX'],
                 user_config: Dict = None):
        """
        Initialize feature engineering pipeline with safety measures
        
        Args:
            window_sizes: List of window sizes for rolling calculations
            technical_indicators: List of technical indicators to calculate
            volatility_features: List of volatility features
            volume_features: List of volume features
            momentum_features: List of momentum features
            user_config: User-defined configuration overrides
        """
        self.window_sizes = window_sizes
        self.technical_indicators = technical_indicators
        self.volatility_features = volatility_features
        self.volume_features = volume_features
        self.momentum_features = momentum_features
        self.scaler = StandardScaler()
        self.feature_cache = {}
        self.last_update = None
        
        # Safety parameters
        self.max_features = 100  # Maximum number of features
        self.feature_importance_threshold = 0.01  # Minimum importance
        self.memory_limit = 1e9  # 1GB memory limit
        self.computation_time_limit = 5  # 5 seconds per calculation
        
        # User configuration
        self.user_config = user_config or {}
        self.user_override = False
        self.feature_blacklist = set(self.user_config.get('blacklisted_features', []))
        self.feature_whitelist = set(self.user_config.get('whitelisted_features', []))
        
        # Feature importance tracking
        self.feature_importance = {}
        self.last_feature_update = datetime.now()
        
        # Performance monitoring
        self.feature_calculation_times = {}
        self.memory_usage = {}
        
        # Error handling
        self.error_count = 0
        self.max_errors = 5  # Maximum allowed errors before pause
        
        # Logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Initialize feature selection model
        self.feature_selector = None
        self.last_feature_selection = None
        
        # Validate configuration
        self._validate_configuration()
        
    def _validate_configuration(self):
        """Validate user configuration"""
        if self.user_config.get('max_features'):
            self.max_features = min(self.max_features, self.user_config['max_features'])
            
        if self.user_config.get('feature_importance_threshold'):
            self.feature_importance_threshold = max(
                self.feature_importance_threshold,
                self.user_config['feature_importance_threshold']
            )
            
        if self.feature_whitelist and self.feature_blacklist:
            if self.feature_whitelist & self.feature_blacklist:
                raise ValueError("Whitelist and blacklist cannot contain overlapping features")
                
    def _check_memory_usage(self, df: pd.DataFrame) -> bool:
        """Check if memory usage is within limits"""
        memory_usage = df.memory_usage(deep=True).sum()
        self.memory_usage[df.columns.name] = memory_usage
        return memory_usage < self.memory_limit
        
    def _check_computation_time(self, start_time: float) -> bool:
        """Check if computation time is within limits"""
        return (time.time() - start_time) < self.computation_time_limit
        
    def _log_feature_calculation(self, feature_name: str, calculation_time: float):
        """Log feature calculation statistics"""
        self.feature_calculation_times[feature_name] = calculation_time
        self.logger.info({
            'type': 'feature_calculation',
            'feature': feature_name,
            'time': calculation_time,
            'memory': self.memory_usage.get(feature_name, 0)
        })
        
    def _handle_error(self, error: Exception, feature_name: str):
        """Handle calculation errors with safety measures"""
        self.error_count += 1
        self.logger.error({
            'type': 'feature_error',
            'feature': feature_name,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        })
        
        if self.error_count >= self.max_errors:
            raise RuntimeError("Too many feature calculation errors")
            
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators with safety checks"""
        try:
            start_time = time.time()
            
            for indicator in self.technical_indicators:
                if indicator in self.feature_blacklist:
                    continue
                    
                if self.feature_whitelist and indicator not in self.feature_whitelist:
                    continue
                    
                if not self._check_computation_time(start_time):
                    self.logger.warning(f"Computation time limit exceeded for {indicator}")
                    break
                    
                # Calculate indicator
                try:
                    if indicator == 'RSI':
                        df['RSI'] = ta.momentum.RSIIndicator(
                            df['close'], window=14
                        ).rsi()
                        
                    elif indicator == 'MACD':
                        macd = ta.trend.MACD(
                            df['close'], window_slow=26, window_fast=12, window_sign=9
                        )
                        df['MACD'] = macd.macd()
                        df['MACD_Signal'] = macd.macd_signal()
                        df['MACD_Hist'] = macd.macd_diff()
                        
                    elif indicator == 'BB':
                        bb = ta.volatility.BollingerBands(
                            df['close'], window=20, window_dev=2
                        )
                        df['BB_Upper'] = bb.bollinger_hband()
                        df['BB_Lower'] = bb.bollinger_lband()
                        df['BB_Middle'] = bb.bollinger_mavg()
                        
                    elif indicator == 'ADX':
                        adx = ta.trend.ADXIndicator(
                            df['high'], df['low'], df['close'], window=14
                        )
                        df['ADX'] = adx.adx()
                        df['ADX_Pos'] = adx.adx_pos()
                        df['ADX_Neg'] = adx.adx_neg()
                        
                    elif indicator == 'OBV':
                        df['OBV'] = ta.volume.OnBalanceVolumeIndicator(
                            df['close'], df['volume']
                        ).on_balance_volume()
                        
                    # Update memory usage
                    if not self._check_memory_usage(df):
                        self.logger.warning(f"Memory limit exceeded for {indicator}")
                        break
                        
                    # Log calculation time
                    calculation_time = time.time() - start_time
                    self._log_feature_calculation(indicator, calculation_time)
                    
                except Exception as e:
                    self._handle_error(e, indicator)
                    continue
                    
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {str(e)}")
            raise

    def calculate_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility features"""
        try:
            # Calculate ATR
            if 'ATR' in self.volatility_features:
                df['ATR'] = ta.volatility.AverageTrueRange(
                    df['high'], df['low'], df['close'], window=14
                ).average_true_range()
            
            # Calculate Bollinger Bands Width
            if 'BBANDS' in self.volatility_features:
                bb = ta.volatility.BollingerBands(df['close'], window=20)
                df['BB_Width'] = bb.bollinger_wband()
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating volatility features: {str(e)}")
            raise

    def calculate_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volume-based features"""
        try:
            # Calculate Money Flow Index
            if 'MFI' in self.volume_features:
                df['MFI'] = ta.volume.MFIIndicator(
                    df['high'], df['low'], df['close'], df['volume'], window=14
                ).money_flow_index()
            
            # Calculate Volume Rate of Change
            df['Volume_ROC'] = df['volume'].pct_change()
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating volume features: {str(e)}")
            raise

    def calculate_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum indicators"""
        try:
            # Calculate Rate of Change
            if 'ROC' in self.momentum_features:
                df['ROC'] = ta.momentum.ROCIndicator(
                    df['close'], window=12
                ).roc()
            
            # Calculate ADX
            if 'ADX' in self.momentum_features:
                df['ADX'] = ta.trend.ADXIndicator(
                    df['high'], df['low'], df['close'], window=14
                ).adx()
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating momentum features: {str(e)}")
            raise

    def calculate_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate time-based features with safety checks"""
        try:
            start_time = time.time()
            
            # Extract time features
            df['hour'] = df.index.hour
            df['day_of_week'] = df.index.dayofweek
            df['month'] = df.index.month
            df['quarter'] = df.index.quarter
            df['year'] = df.index.year
            
            # Create time-based indicators
            df['is_weekend'] = df['day_of_week'].isin([5, 6])
            df['is_end_of_month'] = df.index.is_month_end
            df['is_start_of_month'] = df.index.is_month_start
            
            # Create cyclical features for time
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
            df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
            
            # Add market hours indicator
            df['is_trading_hours'] = ((df['hour'] >= 9) & (df['hour'] < 16))
            
            # Add seasonal indicators
            df['is_earnings_season'] = df['month'].isin([1, 4, 7, 10])
            
            # Add holiday indicators
            df['is_holiday'] = False  # Add specific holidays as needed
            
            # Check memory usage
            if not self._check_memory_usage(df):
                self.logger.warning("Memory limit exceeded for time features")
                return df.drop([
                    'hour_sin', 'hour_cos',
                    'day_of_week_sin', 'day_of_week_cos'
                ], axis=1)
                
            # Log calculation time
            calculation_time = time.time() - start_time
            self._log_feature_calculation('time_features', calculation_time)
            
            return df
            
        except Exception as e:
            self._handle_error(e, 'time_features')
            raise

    def calculate_market_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate market regime features"""
        try:
            # Calculate market trend
            df['trend'] = df['close'].rolling(window=20).apply(
                lambda x: 1 if x[-1] > x[0] else 0
            )
            
            # Calculate volatility regime
            df['volatility_regime'] = pd.qcut(
                df['ATR'].rolling(window=20).mean(),
                q=3,
                labels=[0, 1, 2]
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating market regime features: {str(e)}")
            raise

    def normalize_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize features using Z-score normalization"""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                df[col] = zscore(df[col], nan_policy='omit')
            return df
            
        except Exception as e:
            logger.error(f"Error normalizing features: {str(e)}")
            raise

    def create_feature_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create complete feature matrix"""
        try:
            # Calculate all features
            df = self.calculate_technical_indicators(df)
            df = self.calculate_volatility_features(df)
            df = self.calculate_volume_features(df)
            df = self.calculate_momentum_features(df)
            df = self.calculate_time_features(df)
            df = self.calculate_market_regime_features(df)
            
            # Drop any remaining NaN values
            df = df.dropna()
            
            # Normalize features
            df = self.normalize_features(df)
            
            # Track feature columns
            self.feature_columns = df.columns.tolist()
            
            return df
            
        except Exception as e:
            logger.error(f"Error creating feature matrix: {str(e)}")
            raise

    def get_feature_columns(self) -> List[str]:
        """Get list of feature columns"""
        return self.feature_columns

# Initialize global instance
feature_engineer = FeatureEngineer()
