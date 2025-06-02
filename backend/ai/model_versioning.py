from typing import Dict, List, Optional, Any
import logging
import json
import os
from datetime import datetime
from pydantic import BaseModel
import torch
import numpy as np

class ModelVersion(BaseModel):
    version: str
    created_at: datetime
    metrics: Dict[str, float]
    parameters: Dict[str, Any]
    status: str = "active"
    notes: Optional[str] = None

class ModelVersioning:
    def __init__(self, model_dir: str):
        self.logger = logging.getLogger(__name__)
        self.model_dir = model_dir
        self.versions = []
        self.current_version = None
        self._load_versions()
    
    def _load_versions(self) -> None:
        """
        Load existing model versions
        """
        try:
            if os.path.exists(os.path.join(self.model_dir, "versions.json")):
                with open(os.path.join(self.model_dir, "versions.json"), "r") as f:
                    versions_data = json.load(f)
                    self.versions = [ModelVersion(**v) for v in versions_data]
                    self.current_version = max(
                        self.versions,
                        key=lambda v: datetime.strptime(v.created_at, "%Y-%m-%d %H:%M:%S")
                    ).version if self.versions else None
        except Exception as e:
            self.logger.error(f"Error loading versions: {str(e)}")
    
    def create_version(self, 
                      model: Any, 
                      metrics: Dict[str, float],
                      parameters: Dict[str, Any],
                      notes: Optional[str] = None) -> str:
        """
        Create a new model version
        """
        try:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save model
            model_path = os.path.join(self.model_dir, f"model_{version}.pth")
            if isinstance(model, torch.nn.Module):
                torch.save(model.state_dict(), model_path)
            else:
                with open(model_path, "wb") as f:
                    pickle.dump(model, f)
            
            # Create version record
            version_record = ModelVersion(
                version=version,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                metrics=metrics,
                parameters=parameters,
                notes=notes
            )
            
            self.versions.append(version_record)
            self.current_version = version
            
            # Update versions file
            self._save_versions()
            
            return version
            
        except Exception as e:
            self.logger.error(f"Error creating version: {str(e)}")
            raise
    
    def _save_versions(self) -> None:
        """
        Save versions to file
        """
        try:
            versions_data = [v.dict() for v in self.versions]
            with open(os.path.join(self.model_dir, "versions.json"), "w") as f:
                json.dump(versions_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving versions: {str(e)}")
    
    def load_version(self, version: str) -> Any:
        """
        Load a specific model version
        """
        try:
            version_record = next((v for v in self.versions if v.version == version), None)
            if not version_record:
                raise ValueError(f"Version {version} not found")
                
            model_path = os.path.join(self.model_dir, f"model_{version}.pth")
            if not os.path.exists(model_path):
                raise ValueError(f"Model file for version {version} not found")
                
            if isinstance(version_record.parameters, dict) and \
               version_record.parameters.get('model_type') == 'torch':
                model = self._create_torch_model(version_record.parameters)
                model.load_state_dict(torch.load(model_path))
            else:
                with open(model_path, "rb") as f:
                    model = pickle.load(f)
            
            return model
            
        except Exception as e:
            self.logger.error(f"Error loading version {version}: {str(e)}")
            raise
    
    def _create_torch_model(self, params: Dict) -> torch.nn.Module:
        """
        Create a torch model from parameters
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
        )
    
    def compare_versions(self, version1: str, version2: str) -> Dict:
        """
        Compare two model versions
        """
        try:
            v1 = next((v for v in self.versions if v.version == version1), None)
            v2 = next((v for v in self.versions if v.version == version2), None)
            
            if not v1 or not v2:
                raise ValueError("One or both versions not found")
                
            comparison = {
                'version1': v1.version,
                'version2': v2.version,
                'metric_comparison': {},
                'parameter_differences': {}
            }
            
            # Compare metrics
            for metric in set(v1.metrics.keys()).union(v2.metrics.keys()):
                v1_val = v1.metrics.get(metric, 0)
                v2_val = v2.metrics.get(metric, 0)
                comparison['metric_comparison'][metric] = {
                    'v1': v1_val,
                    'v2': v2_val,
                    'difference': v2_val - v1_val,
                    'improvement': (v2_val - v1_val) / v1_val if v1_val != 0 else 0
                }
            
            # Compare parameters
            for param in set(v1.parameters.keys()).union(v2.parameters.keys()):
                v1_val = v1.parameters.get(param)
                v2_val = v2.parameters.get(param)
                if v1_val != v2_val:
                    comparison['parameter_differences'][param] = {
                        'v1': v1_val,
                        'v2': v2_val
                    }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing versions: {str(e)}")
            raise
    
    def rollback_to_version(self, version: str) -> None:
        """
        Rollback to a specific version
        """
        try:
            version_record = next((v for v in self.versions if v.version == version), None)
            if not version_record:
                raise ValueError(f"Version {version} not found")
                
            # Update current version
            self.current_version = version
            
            # Mark other versions as inactive
            for v in self.versions:
                v.status = "inactive" if v.version != version else "active"
            
            # Save changes
            self._save_versions()
            
        except Exception as e:
            self.logger.error(f"Error rolling back to version {version}: {str(e)}")
            raise
    
    def get_version_history(self) -> List[Dict]:
        """
        Get complete version history
        """
        return [v.dict() for v in sorted(
            self.versions,
            key=lambda v: datetime.strptime(v.created_at, "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )]
