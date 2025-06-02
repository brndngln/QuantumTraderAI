from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from pydantic import BaseModel
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import cross_val_score
import torch
from torch import nn
import torch.nn.functional as F

class ModelConfig(BaseModel):
    model_type: str
    params: Dict
    weight: float
    score: float = 0.0

class EnsembleLearning:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = []
        self.model_weights = {}
        self.current_model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def add_model(self, config: ModelConfig) -> None:
        """
        Add a model to the ensemble
        """
        try:
            model = self._create_model(config.model_type, config.params)
            self.models.append((model, config.weight))
            self.model_weights[config.model_type] = config.weight
            self.logger.info(f"Added model {config.model_type} with weight {config.weight}")
        except Exception as e:
            self.logger.error(f"Error adding model: {str(e)}")
    
    def _create_model(self, model_type: str, params: Dict) -> Any:
        """
        Create a model instance
        """
        if model_type == "random_forest":
            return RandomForestClassifier(**params)
        elif model_type == "gradient_boosting":
            return GradientBoostingClassifier(**params)
        elif model_type == "logistic_regression":
            return LogisticRegression(**params)
        elif model_type == "svm":
            return SVC(**params)
        elif model_type == "neural_network":
            return MLPClassifier(**params)
        elif model_type == "deep_learning":
            return self._create_deep_learning_model(params)
        raise ValueError(f"Unknown model type: {model_type}")
    
    def _create_deep_learning_model(self, params: Dict) -> nn.Module:
        """
        Create a deep learning model
        """
        class TradingModel(nn.Module):
            def __init__(self, input_size: int, hidden_size: int, num_layers: int):
                super().__init__()
                self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
                self.fc = nn.Linear(hidden_size, 1)
                self.dropout = nn.Dropout(0.2)
                
            def forward(self, x):
                lstm_out, _ = self.lstm(x)
                x = self.dropout(lstm_out[:, -1, :])
                x = self.fc(x)
                return torch.sigmoid(x)
        
        return TradingModel(
            params.get('input_size', 10),
            params.get('hidden_size', 64),
            params.get('num_layers', 2)
        ).to(self.device)
    
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Train all models in the ensemble
        """
        try:
            for model, _ in self.models:
                if isinstance(model, nn.Module):
                    self._train_deep_learning(model, X, y)
                else:
                    model.fit(X, y)
            
            # Update model scores
            self._update_model_scores(X, y)
            
            # Select best model
            self.current_model = self._select_best_model()
            
        except Exception as e:
            self.logger.error(f"Error during training: {str(e)}")
    
    def _train_deep_learning(self, model: nn.Module, X: np.ndarray, y: np.ndarray) -> None:
        """
        Train deep learning model
        """
        X = torch.tensor(X, dtype=torch.float32).to(self.device)
        y = torch.tensor(y, dtype=torch.float32).unsqueeze(1).to(self.device)
        
        optimizer = torch.optim.Adam(model.parameters())
        criterion = nn.BCELoss()
        
        model.train()
        for epoch in range(100):
            optimizer.zero_grad()
            outputs = model(X)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()
    
    def _update_model_scores(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Update model scores based on performance
        """
        for model, weight in self.models:
            if isinstance(model, nn.Module):
                score = self._evaluate_deep_learning(model, X, y)
            else:
                score = np.mean(cross_val_score(model, X, y, cv=5))
            
            self.model_weights[type(model).__name__] = score
    
    def _evaluate_deep_learning(self, model: nn.Module, X: np.ndarray, y: np.ndarray) -> float:
        """
        Evaluate deep learning model
        """
        X = torch.tensor(X, dtype=torch.float32).to(self.device)
        y = torch.tensor(y, dtype=torch.float32).unsqueeze(1).to(self.device)
        
        model.eval()
        with torch.no_grad():
            outputs = model(X)
            predictions = (outputs > 0.5).float()
            accuracy = (predictions == y).float().mean().item()
        
        return accuracy
    
    def _select_best_model(self) -> Any:
        """
        Select best performing model
        """
        best_model = None
        best_score = 0.0
        
        for model, weight in self.models:
            score = self.model_weights.get(type(model).__name__, 0.0)
            if score > best_score:
                best_model = model
                best_score = score
        
        return best_model
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using weighted ensemble
        """
        if not self.models:
            raise ValueError("No models have been trained")
            
        predictions = []
        total_weight = sum(weight for _, weight in self.models)
        
        for model, weight in self.models:
            if isinstance(model, nn.Module):
                pred = self._predict_deep_learning(model, X)
            else:
                pred = model.predict(X)
            
            predictions.append(pred * (weight / total_weight))
        
        return np.sum(predictions, axis=0)
    
    def _predict_deep_learning(self, model: nn.Module, X: np.ndarray) -> np.ndarray:
        """
        Make predictions with deep learning model
        """
        X = torch.tensor(X, dtype=torch.float32).to(self.device)
        
        model.eval()
        with torch.no_grad():
            outputs = model(X)
            predictions = (outputs > 0.5).float().cpu().numpy()
        
        return predictions
    
    def transfer_learning(self, source_model: Any, target_data: Dict) -> None:
        """
        Apply transfer learning from source model
        """
        if isinstance(source_model, nn.Module):
            # Copy weights from source model
            for target_param, source_param in zip(
                self.current_model.parameters(),
                source_model.parameters()
            ):
                target_param.data.copy_(source_param.data)
                
            # Fine-tune on target data
            self._train_deep_learning(
                self.current_model,
                target_data['X'],
                target_data['y']
            )
    
    def self_learning(self, new_data: Dict) -> None:
        """
        Update model with new data
        """
        if not self.current_model:
            raise ValueError("No model has been trained")
            
        if isinstance(self.current_model, nn.Module):
            self._train_deep_learning(
                self.current_model,
                new_data['X'],
                new_data['y']
            )
        else:
            self.current_model.fit(
                new_data['X'],
                new_data['y']
            )
