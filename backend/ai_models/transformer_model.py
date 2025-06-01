import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Layer, Dense, Dropout, LayerNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class MultiHeadSelfAttention(Layer):
    def __init__(self, embed_dim, num_heads=8):
        super(MultiHeadSelfAttention, self).__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        if embed_dim % num_heads != 0:
            raise ValueError(f"Embedding dimension {embed_dim} should be divisible by number of heads {num_heads}")
        self.projection_dim = embed_dim // num_heads
        self.query_dense = Dense(embed_dim)
        self.key_dense = Dense(embed_dim)
        self.value_dense = Dense(embed_dim)
        self.combine_heads = Dense(embed_dim)

    def attention(self, query, key, value):
        score = tf.matmul(query, key, transpose_b=True)
        dim_key = tf.cast(tf.shape(key)[-1], tf.float32)
        scaled_score = score / tf.math.sqrt(dim_key)
        weights = tf.nn.softmax(scaled_score, axis=-1)
        output = tf.matmul(weights, value)
        return output, weights

    def separate_heads(self, x, batch_size):
        x = tf.reshape(x, (batch_size, -1, self.num_heads, self.projection_dim))
        return tf.transpose(x, perm=[0, 2, 1, 3])

    def call(self, inputs):
        batch_size = tf.shape(inputs)[0]
        query = self.query_dense(inputs)
        key = self.key_dense(inputs)
        value = self.value_dense(inputs)
        query = self.separate_heads(query, batch_size)
        key = self.separate_heads(key, batch_size)
        value = self.separate_heads(value, batch_size)
        attention, weights = self.attention(query, key, value)
        attention = tf.transpose(attention, perm=[0, 2, 1, 3])
        concat_attention = tf.reshape(attention, (batch_size, -1, self.embed_dim))
        output = self.combine_heads(concat_attention)
        return output

class TransformerBlock(Layer):
    def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1):
        super(TransformerBlock, self).__init__()
        self.att = MultiHeadSelfAttention(embed_dim, num_heads)
        self.ffn = tf.keras.Sequential([
            Dense(ff_dim, activation="relu"),
            Dense(embed_dim),
        ])
        self.layernorm1 = LayerNormalization(epsilon=1e-6)
        self.layernorm2 = LayerNormalization(epsilon=1e-6)
        self.dropout1 = Dropout(rate)
        self.dropout2 = Dropout(rate)

    def call(self, inputs, training):
        attn_output = self.att(inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)

class TransformerModel:
    def __init__(self,
                 input_shape: Tuple[int, int] = (60, 10),
                 embed_dim: int = 64,
                 num_heads: int = 4,
                 ff_dim: int = 32,
                 num_transformer_blocks: int = 3,
                 dropout_rate: float = 0.2,
                 learning_rate: float = 0.001,
                 batch_size: int = 32,
                 epochs: int = 100,
                 patience: int = 10,
                 verbose: int = 1):
        """
        Initialize Transformer model for trading predictions
        
        Args:
            input_shape: Shape of input data (timesteps, features)
            embed_dim: Dimension of the embedding space
            num_heads: Number of attention heads
            ff_dim: Dimension of the feed-forward network
            num_transformer_blocks: Number of transformer blocks
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for optimizer
            batch_size: Batch size for training
            epochs: Maximum number of epochs
            patience: Patience for early stopping
            verbose: Verbosity level
        """
        self.input_shape = input_shape
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.num_transformer_blocks = num_transformer_blocks
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.patience = patience
        self.verbose = verbose
        self.model = None
        self.scaler = StandardScaler()
        self.callbacks = self._create_callbacks()
        self.last_update: Optional[datetime] = None
        self.metrics = {
            'accuracy': [],
            'loss': [],
            'val_accuracy': [],
            'val_loss': []
        }

    def _create_callbacks(self) -> List[tf.keras.callbacks.Callback]:
        """Create callbacks for training"""
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=self.patience,
            restore_best_weights=True,
            verbose=1
        )
        
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.2,
            patience=int(self.patience/2),
            min_lr=1e-6,
            verbose=1
        )
        
        return [early_stopping, reduce_lr]

    def build_model(self) -> None:
        """Build the Transformer model architecture"""
        inputs = tf.keras.Input(shape=self.input_shape)
        x = inputs
        
        # Positional encoding
        positions = tf.range(start=0, limit=self.input_shape[0], delta=1)
        positions = tf.expand_dims(positions, axis=-1)
        x = tf.concat([x, positions], axis=-1)
        
        # Transformer blocks
        for _ in range(self.num_transformer_blocks):
            x = TransformerBlock(self.embed_dim, self.num_heads, self.ff_dim, self.dropout_rate)(x)
        
        # Global average pooling
        x = tf.keras.layers.GlobalAveragePooling1D()(x)
        
        # Dense layers with dropout
        x = Dense(64, activation='relu')(x)
        x = Dropout(self.dropout_rate)(x)
        x = Dense(32, activation='relu')(x)
        x = Dropout(self.dropout_rate)(x)
        
        # Output layer
        outputs = Dense(1, activation='sigmoid')(x)
        
        self.model = Model(inputs=inputs, outputs=outputs)
        self.model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info("Transformer model built successfully")

    def prepare_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for Transformer input"""
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
        """Train the Transformer model"""
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
            logger.info("Transformer model training completed successfully")
            
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
transformer = TransformerModel(
    input_shape=(60, 10),  # 60 timesteps, 10 features
    embed_dim=64,
    num_heads=4,
    ff_dim=32,
    num_transformer_blocks=3,
    dropout_rate=0.2,
    learning_rate=0.001,
    batch_size=32,
    epochs=100,
    patience=10
)
