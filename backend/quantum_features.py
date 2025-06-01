import numpy as np
from numba import jit, prange
import pandas as pd
from scipy import stats

class QuantumFeatureExtractor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.window_size = 24  # 24 hours for feature calculation
        
    @jit(nopython=True)
    def calculate_quantum_features(self, price_data: np.ndarray) -> np.ndarray:
        """
        Calculate quantum-inspired features from price data
        
        Args:
            price_data: Array of price data
            
        Returns:
            Array of quantum features
        """
        n = len(price_data)
        features = np.zeros((n, 12))  # 12 quantum features
        
        # Calculate basic returns
        returns = np.zeros(n)
        for i in range(1, n):
            returns[i] = price_data[i] / price_data[i-1] - 1
        
        # Quantum-inspired volatility features
        for i in range(self.window_size, n):
            window_returns = returns[i-self.window_size:i]
            
            # Quantum superposition features
            features[i, 0] = np.mean(window_returns)
            features[i, 1] = np.std(window_returns)
            features[i, 2] = np.sum(np.abs(window_returns))
            
            # Quantum entanglement features
            for j in range(1, len(window_returns)):
                features[i, 3] += window_returns[j] * window_returns[j-1]
            features[i, 3] /= len(window_returns) - 1
            
            # Quantum probability amplitudes
            features[i, 4] = np.sum(np.cos(window_returns))
            features[i, 5] = np.sum(np.sin(window_returns))
            
            # Quantum coherence features
            features[i, 6] = np.sum(window_returns**2)
            features[i, 7] = np.sum(np.abs(window_returns)**2)
            
            # Quantum interference features
            features[i, 8] = np.sum(np.exp(-window_returns**2))
            features[i, 9] = np.sum(np.exp(-np.abs(window_returns)**2))
            
            # Quantum correlation features
            features[i, 10] = stats.kurtosis(window_returns)
            features[i, 11] = stats.skew(window_returns)
        
        return features
        
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract quantum features from market data DataFrame
        
        Args:
            df: DataFrame containing price data
            
        Returns:
            DataFrame with quantum features
        """
        # Calculate features for each price series
        features = {}
        for col in df.columns:
            price_data = df[col].values
            features[col] = self.calculate_quantum_features(price_data)
        
        # Create feature DataFrame
        feature_df = pd.DataFrame()
        for col, feat in features.items():
            for i in range(feat.shape[1]):
                feature_df[f'{col}_quantum_{i}'] = feat[:, i]
        
        return feature_df
        
    def normalize_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize quantum features using StandardScaler
        
        Args:
            df: DataFrame containing quantum features
            
        Returns:
            Normalized DataFrame
        """
        return pd.DataFrame(
            self.scaler.fit_transform(df),
            columns=df.columns,
            index=df.index
        )
