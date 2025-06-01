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
        """Handle model errors with enhanced safety measures"""
        try:
            self.error_count += 1
            self.last_error = error
            self.last_error_timestamp = datetime.now()
            
            # Log detailed error information
            error_data = {
                'type': 'model_error',
                'operation': operation,
                'error': str(error),
                'timestamp': datetime.now().isoformat(),
                'memory_usage': self.memory_usage[-1] if self.memory_usage else 0,
                'cpu_usage': self.cpu_usage[-1] if self.cpu_usage else 0,
                'gpu_usage': self.gpu_usage[-1] if self.gpu_usage else 0,
                'stack_trace': traceback.format_exc(),
                'error_count': self.error_count,
                'consecutive_errors': self.error_count,
                'model_state': {
                    'is_training': self.is_training,
                    'is_predicting': self.is_predicting,
                    'last_update': str(self.last_update)
                }
            }
            
            # Log to file
            error_file = METRICS_DIR / f"{self.__class__.__name__}_errors.log"
            with open(error_file, 'a') as f:
                f.write(json.dumps(error_data) + '\n')
            
            # Log to console
            self.logger.error(error_data)
            
            # Send alert if enabled
            if self.user_config.get('send_alerts'):
                self._send_alert(
                    'error',
                    f"Error in {operation}: {str(error)}"
                )
            
            # Check for consecutive errors
            if self.error_count >= self.max_consecutive_errors:
                self.user_paused = True
                self.logger.error(f"Maximum consecutive errors ({self.max_consecutive_errors}) reached")
                raise RuntimeError("Too many consecutive errors")
                
            # Save metrics
            self._save_metrics()
            
        except Exception as e:
            self.logger.error(f"Error handling failed: {str(e)}")
            raise
            
    def _validate_data(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> bool:
        """Validate input data with enhanced checks"""
        try:
            # Check data existence
            if X is None:
                raise ValueError("Input data cannot be None")
                
            # Check data dimensions
            if len(X.shape) != 2:
                raise ValueError(f"Input data must be 2D array, got {len(X.shape)} dimensions")
                
            # Check minimum data points
            if X.shape[0] < self.input_shape[0]:
                raise ValueError(f"Insufficient data points: {X.shape[0]} < {self.input_shape[0]}")
                
            # Check feature count
            if X.shape[1] != self.input_shape[1]:
                raise ValueError(f"Feature count mismatch: {X.shape[1]} != {self.input_shape[1]}")
                
            # Check target data if provided
            if y is not None:
                if len(y.shape) != 1:
                    raise ValueError(f"Target data must be 1D array, got {len(y.shape)} dimensions")
                    
                if len(X) != len(y):
                    raise ValueError(f"X and y length mismatch: {len(X)} != {len(y)}")
                    
            # Check data types
            if not np.issubdtype(X.dtype, np.number):
                raise ValueError(f"Input data must be numeric, got {X.dtype}")
                
            # Check for NaN values
            if np.isnan(X).any():
                raise ValueError("Input data contains NaN values")
                
            # Check memory usage
            if not self._check_memory_usage():
                raise RuntimeError("Memory limit exceeded")
                
            # Log validation success
            self._log_model_state('data_validation', {
                'data_shape': X.shape,
                'target_shape': y.shape if y is not None else None,
                'memory_usage': self.memory_usage[-1]
            })
            
            return True
            
        except Exception as e:
            self._handle_error(e, 'data_validation')
            return False
        
    def build_model(self):
        """Build enhanced LSTM model with safety measures"""
        try:
            if self.user_paused:
                raise RuntimeError("Model is paused by user")
                
            if not self._check_memory_usage():
                raise RuntimeError("Memory limit exceeded")
                
            if not self._check_cpu_usage():
                raise RuntimeError("CPU usage too high")
                
            self.is_training = True
            self.last_training_start = time.time()
            self._log_model_state('building')
            
            # Build enhanced model architecture
            model = Sequential()
            
            # First LSTM layer with attention
            model.add(LSTM(128, return_sequences=True, input_shape=self.input_shape))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))
            
            # Second LSTM layer with attention
            model.add(LSTM(64, return_sequences=True))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))
            
            # Third LSTM layer
            model.add(LSTM(32))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))
            
            # Dense layers with regularization
            model.add(Dense(64, activation='relu', kernel_regularizer='l2'))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))
            
            model.add(Dense(32, activation='relu', kernel_regularizer='l2'))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))
            
            # Output layer
            model.add(Dense(1, activation='linear'))
            
            # Optimizer with learning rate schedule
            optimizer = Adam(
                learning_rate=self.learning_rate,
                beta_1=0.9,
                beta_2=0.999,
                epsilon=1e-07
            )
            
            # Compile model with multiple metrics
            model.compile(
                optimizer=optimizer,
                loss='mse',
                metrics=['mae', 'mse', tf.keras.metrics.RootMeanSquaredError()]
            )
            
            # Save model configuration
            self.model_config = {
                'architecture': model.to_json(),
                'optimizer': str(optimizer)
            }
            
            # Log model details
            self._log_model_state('built', {
                'architecture': model.to_json(),
                'optimizer': str(optimizer),
                'metrics': model.metrics_names
            })
            
            self.model = model
            
        except Exception as e:
            self._handle_error(e, 'build')
            raise
            
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None) -> None:
        """Train LSTM model with enhanced safety and monitoring"""
        try:
            if self.user_paused:
                raise RuntimeError("Model is paused by user")
                
            if not self._validate_data(X_train, y_train):
                raise ValueError("Invalid training data")
                
            if not self._check_training_time(time.time()):
                raise RuntimeError("Training time limit exceeded")
                
            if not self._check_memory_usage():
                raise RuntimeError("Memory limit exceeded")
                
            if not self._check_cpu_usage():
                raise RuntimeError("CPU usage too high")
                
            self.is_training = True
            self.last_training_start = time.time()
            self._log_model_state('training')
            
            # Prepare data with safety checks
            try:
                X_train = self.scaler.fit_transform(X_train.reshape(-1, X_train.shape[-1]))
                X_train = X_train.reshape(X_train.shape[0], self.input_shape[0], self.input_shape[1])
                
                if X_val is not None:
                    X_val = self.scaler.transform(X_val.reshape(-1, X_val.shape[-1]))
                    X_val = X_val.reshape(X_val.shape[0], self.input_shape[0], self.input_shape[1])
                
                # Validate prepared data
                if X_train.shape[0] < self.batch_size:
                    raise ValueError(f"Not enough data for batch size: {X_train.shape[0]} < {self.batch_size}")
                
            except Exception as e:
                self._handle_error(e, 'data_preparation')
                raise
            
            # Create callbacks with enhanced monitoring
            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=self.patience,
                    restore_best_weights=True,
                    verbose=1
                ),
                ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.1,
                    patience=int(self.patience/2),
                    min_lr=1e-6,
                    verbose=1
                )
            ]
            
            # Train model with enhanced monitoring
            start_time = time.time()
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val) if X_val is not None else None,
                batch_size=self.batch_size,
                epochs=self.epochs,
                callbacks=callbacks,
                verbose=self.verbose,
                use_multiprocessing=True,
                workers=4
            )
            
            # Calculate training time
            training_time = time.time() - start_time
            self.training_times.append(training_time)
            self.metrics['training_time'].append(training_time)
            
            # Update metrics
            for metric in ['loss', 'val_loss', 'mae', 'mse', 'root_mean_squared_error']:
                if metric in history.history:
                    self.metrics[metric].extend(history.history[metric])
                    self.train_metrics[metric].extend(history.history[metric])
            
            # Save model configuration
            self._save_model_config()
            
            # Log training completion
            self._log_model_state('trained', {
                'training_time': training_time,
                'final_loss': history.history['loss'][-1],
                'final_val_loss': history.history['val_loss'][-1] if 'val_loss' in history.history else None,
                'epochs_completed': len(history.history['loss'])
            })
            
            # Save metrics
            self._save_metrics()
            
            # Checkpoint management
            self.last_checkpoint = datetime.now()
            
            self.is_training = False
            self.last_update = datetime.now()
            
        except Exception as e:
            self._handle_error(e, 'train')
            raise
            
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions with enhanced safety and monitoring"""
        try:
            if self.user_paused:
                raise RuntimeError("Model is paused by user")
                
            if not self._validate_data(X):
                raise ValueError("Invalid prediction data")
                
            if not self._check_prediction_time(time.time()):
                raise RuntimeError("Prediction time limit exceeded")
                
            if not self._check_memory_usage():
                raise RuntimeError("Memory limit exceeded")
                
            if not self._check_cpu_usage():
                raise RuntimeError("CPU usage too high")
                
            self.is_predicting = True
            self.last_prediction_start = time.time()
            self._log_model_state('predicting')
            
            # Prepare data with safety checks
            try:
                X = self.scaler.transform(X.reshape(-1, X.shape[-1]))
                X = X.reshape(X.shape[0], self.input_shape[0], self.input_shape[1])
                
                # Validate prepared data
                if X.shape[0] < 1:
                    raise ValueError("No data points for prediction")
                    
            except Exception as e:
                self._handle_error(e, 'data_preparation')
                raise
            
            # Make predictions with monitoring
            start_time = time.time()
            predictions = self.model.predict(
                X,
                batch_size=self.batch_size,
                verbose=0,
                use_multiprocessing=True,
                workers=4
            )
            prediction_time = time.time() - start_time
            
            # Update metrics
            self.prediction_times.append(prediction_time)
            self.metrics['prediction_time'].append(prediction_time)
            
            # Log prediction details
            self._log_model_state('predicted', {
                'prediction_time': prediction_time,
                'num_predictions': len(predictions),
                'memory_usage': self.memory_usage[-1],
                'cpu_usage': self.cpu_usage[-1]
            })
            
            # Save metrics
            self._save_metrics()
            
            self.is_predicting = False
            self.last_update = datetime.now()
            
            return predictions
            
        except Exception as e:
            self._handle_error(e, 'predict')
            raise

    def _save_metrics(self):
        """Save comprehensive metrics with enhanced monitoring"""
        try:
            metrics_file = METRICS_DIR / f"{self.__class__.__name__}_metrics.json"
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'metrics': self.metrics,
                'system_metrics': {
                    'memory_usage': self.memory_usage,
                    'cpu_usage': self.cpu_usage
                },
                'model_state': {
                    'is_training': self.is_training,
                    'is_predicting': self.is_predicting,
                    'last_training_start': str(self.last_training_start),
                    'last_prediction_start': str(self.last_prediction_start),
                    'last_update': str(self.last_update),
                    'error_count': self.error_count,
                    'consecutive_errors': self.error_count,
                    'last_error': str(self.last_error)
                },
                'user_config': self.user_config,
                'model_config': self.model_config
            }
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=4)
                
            self.logger.info(f"Metrics saved to {metrics_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving metrics: {str(e)}")
            self._handle_error(e, 'save_metrics')

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
