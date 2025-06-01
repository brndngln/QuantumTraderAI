import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class LSTMModel:
    def __init__(self,
                 input_shape: Tuple[int, int] = (60, 10),
                 dropout_rate: float = 0.2,
                 learning_rate: float = 0.001,
                 batch_size: int = 32,
                 epochs: int = 100,
                 patience: int = 10,
                 verbose: int = 1,
                 user_config: Dict = None):
        """
        Initialize LSTM model with safety measures
        
        Args:
            input_shape: Shape of input data (timesteps, features)
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for optimizer
            batch_size: Batch size for training
            epochs: Number of training epochs
            patience: Patience for early stopping
            verbose: Verbosity level
            user_config: User-defined configuration overrides
        """
        self.input_shape = input_shape
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.patience = patience
        self.verbose = verbose
        self.model = None
        self.scaler = StandardScaler()
        self.metrics = {
            'loss': [],
            'val_loss': [],
            'accuracy': [],
            'val_accuracy': []
        }
        self.last_update = None
        
        # Safety parameters
        self.max_memory_usage = 2e9  # 2GB limit
        self.max_training_time = 3600  # 1 hour limit
        self.max_prediction_time = 5  # 5 seconds
        self.error_threshold = 0.05  # Maximum allowed error
        self.max_consecutive_errors = 3
        self.error_count = 0
        self.last_error = None
        
        # User configuration
        self.user_config = user_config or {}
        self.user_override = False
        self.user_paused = False
        self.user_configured = False
        
        # Performance monitoring
        self.training_times = []
        self.prediction_times = []
        self.memory_usage = []
        self.cpu_usage = []
        
        # Model state
        self.is_training = False
        self.is_predicting = False
        self.last_training_start = None
        self.last_prediction_start = None
        self.last_memory_check = None
        
        # Logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Initialize metrics
        self.train_metrics = {
            'loss': [],
            'accuracy': [],
            'val_loss': [],
            'val_accuracy': [],
            'memory_usage': [],
            'cpu_usage': [],
            'training_time': [],
            'prediction_time': []
        }
        
        # Validate configuration
        self._validate_configuration()
        
    def _validate_configuration(self):
        """Validate user configuration"""
        if self.user_config.get('max_memory_usage'):
            self.max_memory_usage = min(
                self.max_memory_usage,
                self.user_config['max_memory_usage']
            )
            
        if self.user_config.get('max_training_time'):
            self.max_training_time = min(
                self.max_training_time,
                self.user_config['max_training_time']
            )
            
        if self.user_config.get('error_threshold'):
            self.error_threshold = max(
                self.error_threshold,
                self.user_config['error_threshold']
            )
            
        if self.user_config.get('max_consecutive_errors'):
            self.max_consecutive_errors = min(
                self.max_consecutive_errors,
                self.user_config['max_consecutive_errors']
            )
            
    def _check_memory_usage(self) -> bool:
        """Check if memory usage is within limits"""
        import psutil
        process = psutil.Process()
        mem = process.memory_info().rss
        self.memory_usage.append(mem)
        
        if mem > self.max_memory_usage:
            self.logger.warning(f"Memory usage exceeded limit: {mem} > {self.max_memory_usage}")
            return False
            
        return True
        
    def _check_cpu_usage(self) -> bool:
        """Check if CPU usage is within limits"""
        import psutil
        cpu = psutil.cpu_percent()
        self.cpu_usage.append(cpu)
        
        if cpu > 90:  # Warning threshold
            self.logger.warning(f"High CPU usage: {cpu}%")
            return False
            
        return True
        
    def _log_model_state(self, state: str):
        """Log model state changes"""
        self.logger.info({
            'type': 'model_state',
            'state': state,
            'timestamp': datetime.now().isoformat(),
            'memory_usage': self.memory_usage[-1] if self.memory_usage else 0,
            'cpu_usage': self.cpu_usage[-1] if self.cpu_usage else 0,
            'error_count': self.error_count
        })
        
    def _handle_error(self, error: Exception, operation: str):
        """Handle model errors with safety measures"""
        self.error_count += 1
        self.last_error = error
        
        self.logger.error({
            'type': 'model_error',
            'operation': operation,
            'error': str(error),
            'timestamp': datetime.now().isoformat(),
            'memory_usage': self.memory_usage[-1] if self.memory_usage else 0,
            'cpu_usage': self.cpu_usage[-1] if self.cpu_usage else 0
        })
        
        if self.error_count >= self.max_consecutive_errors:
            self.user_paused = True
            raise RuntimeError("Too many consecutive errors")
            
    def _validate_data(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> bool:
        """Validate input data"""
        if X is None or X.shape[0] < self.input_shape[0]:
            raise ValueError("Insufficient data points")
            
        if y is not None and len(X) != len(y):
            raise ValueError("X and y must have same length")
            
        if not self._check_memory_usage():
            raise RuntimeError("Memory limit exceeded")
            
        return True
        
    def build_model(self):
        """Build LSTM model with safety measures"""
        try:
            if self.user_paused:
                raise RuntimeError("Model is paused by user")
                
            if not self._check_memory_usage():
                raise RuntimeError("Memory limit exceeded")
                
            self.is_training = True
            self.last_training_start = time.time()
            self._log_model_state('building')
            
            # Build model with safety layers
            model = Sequential()
            model.add(LSTM(128, return_sequences=True, input_shape=self.input_shape))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))
            
            model.add(LSTM(64, return_sequences=True))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))
            
            model.add(LSTM(32))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))
            
            model.add(Dense(16, activation='relu'))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))
            
            model.add(Dense(1, activation='linear'))
            
            optimizer = Adam(learning_rate=self.learning_rate)
            model.compile(optimizer=optimizer, loss='mse')
            
            self.model = model
            self._log_model_state('built')
            
        except Exception as e:
            self._handle_error(e, 'build')
            raise
            
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None) -> None:
        """Train LSTM model with safety measures"""
        try:
            if self.user_paused:
                raise RuntimeError("Model is paused by user")
                
            if not self._validate_data(X_train, y_train):
                raise ValueError("Invalid training data")
                
            if not self._check_training_time(time.time()):
                raise RuntimeError("Training time limit exceeded")
                
            self.is_training = True
            self.last_training_start = time.time()
            self._log_model_state('training')
            
            # Prepare data
            X_train = self.scaler.fit_transform(X_train.reshape(-1, X_train.shape[-1]))
            X_train = X_train.reshape(X_train.shape[0], self.input_shape[0], self.input_shape[1])
            
            if X_val is not None:
                X_val = self.scaler.transform(X_val.reshape(-1, X_val.shape[-1]))
                X_val = X_val.reshape(X_val.shape[0], self.input_shape[0], self.input_shape[1])
            
            # Train model with early stopping
            early_stopping = EarlyStopping(
                monitor='val_loss',
                patience=self.patience,
                restore_best_weights=True
            )
            
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val) if X_val is not None else None,
                batch_size=self.batch_size,
                epochs=self.epochs,
                callbacks=[early_stopping],
                verbose=self.verbose
            )
            
            # Update metrics
            for metric in ['loss', 'val_loss']:
                if metric in history.history:
                    self.metrics[metric].extend(history.history[metric])
            
            self.is_training = False
            self.last_update = datetime.now()
            self._log_model_state('trained')
            
        except Exception as e:
            self._handle_error(e, 'train')
            raise
            
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions with safety measures"""
        try:
            if self.user_paused:
                raise RuntimeError("Model is paused by user")
                
            if not self.model:
                raise ValueError("Model not trained yet")
                
            if not self._validate_data(X):
                raise ValueError("Invalid prediction data")
                
            if not self._check_prediction_time(time.time()):
                raise RuntimeError("Prediction time limit exceeded")
                
            self.last_prediction_start = time.time()
            self._log_model_state('predicting')
            
            # Prepare data
            X = self.scaler.transform(X.reshape(-1, X.shape[-1]))
            X = X.reshape(X.shape[0], self.input_shape[0], self.input_shape[1])
            
            # Make prediction
            predictions = self.model.predict(X)
            
            # Validate prediction
            if np.isnan(predictions).any():
                raise ValueError("Invalid predictions")
                
            self._log_model_state('predicted')
            return predictions
            
        except Exception as e:
            self._handle_error(e, 'predict')
            raise

    def prepare_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for LSTM input"""
        try:
            # Scale features
            scaled_data = self.scaler.fit_transform(data.values)
            
            # Create sequences
            X, y = [], []
            for i in range(len(data) - self.input_shape[0]):
                X.append(scaled_data[i:i + self.input_shape[0]])
                y.append(scaled_data[i + self.input_shape[0], 0])  # Predict next price
                
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise

    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None) -> None:
        """Train the LSTM model"""
        try:
            if self.model is None:
                self.build_model()
                
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val) if X_val is not None else None,
                batch_size=self.batch_size,
                epochs=self.epochs,
                callbacks=self.callbacks,
                verbose=self.verbose
            )
            
            # Store metrics
            for metric in ['loss', 'accuracy']:
                self.metrics[metric].extend(history.history[metric])
                if X_val is not None:
                    self.metrics[f'val_{metric}'].extend(history.history[f'val_{metric}'])
                    
            self.last_update = datetime.now()
            logger.info("LSTM model training completed successfully")
            
        except Exception as e:
            logger.error(f"Error during training: {str(e)}")
            raise

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions using the trained model"""
        try:
            if self.model is None:
                raise ValueError("Model not trained yet")
                
            predictions = self.model.predict(X)
            return predictions
            
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}")
            raise

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance"""
        try:
            if self.model is None:
                raise ValueError("Model not trained yet")
                
            loss, accuracy = self.model.evaluate(X_test, y_test, verbose=0)
            return {
                'loss': loss,
                'accuracy': accuracy,
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            
        except Exception as e:
            logger.error(f"Error during evaluation: {str(e)}")
            raise

    def save_model(self, path: str) -> None:
        """Save the trained model"""
        try:
            self.model.save(path)
            logger.info(f"Model saved to {path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise

    def load_model(self, path: str) -> None:
        """Load a pre-trained model"""
        try:
            self.model = tf.keras.models.load_model(path)
            logger.info(f"Model loaded from {path}")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def get_metrics(self) -> Dict[str, List[float]]:
        """Get training metrics history"""
        return self.metrics

    def get_model_summary(self) -> str:
        """Get model architecture summary"""
        if self.model is None:
            return "Model not built yet"
            
        string_list = []
        self.model.summary(print_fn=lambda x: string_list.append(x))
        return "\n".join(string_list)

# Initialize global instance with sensible defaults
lstm = LSTMModel(
    input_shape=(60, 10),  # 60 timesteps, 10 features
    dropout_rate=0.2,
    learning_rate=0.001,
    batch_size=32,
    epochs=100,
    patience=10
)
