from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel
import logging
from datetime import datetime
import json
from enum import Enum
from transformers import pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

logger = logging.getLogger(__name__)

# Initialize fusion model
FUSION_MODEL = pipeline(
    "text-classification",
    model="distilbert-base-uncased-finetuned-sst-2-english",
    return_all_scores=True
)

class StrategyType(Enum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    MACRO = "macro"
    SENTIMENT = "sentiment"

class FusionSignal(BaseModel):
    symbol: str
    strategy_type: StrategyType
    signal_strength: float
    confidence: float
    timestamp: datetime
    metadata: Dict

class AIFusionLayer:
    def __init__(self):
        self.signals = []
        self.fusion_weights = {
            StrategyType.TECHNICAL: 0.4,
            StrategyType.FUNDAMENTAL: 0.3,
            StrategyType.MACRO: 0.2,
            StrategyType.SENTIMENT: 0.1
        }
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2)
        
    def process_signal(self, signal: FusionSignal) -> FusionSignal:
        """
        Process and normalize a fusion signal
        
        Args:
            signal: FusionSignal object
            
        Returns:
            Processed FusionSignal with normalized values
        """
        try:
            # Normalize signal strength
            signal.signal_strength = self._normalize_signal(signal.signal_strength)
            
            # Update confidence based on strategy type
            signal.confidence = self._adjust_confidence(signal)
            
            # Store signal
            self.signals.append(signal)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error processing signal: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing signal: {str(e)}"
            )
            
    def _normalize_signal(self, strength: float) -> float:
        """
        Normalize signal strength to 0-1 range
        """
        return float(np.clip(strength, 0, 1))
        
    def _adjust_confidence(self, signal: FusionSignal) -> float:
        """
        Adjust confidence based on strategy type and market conditions
        """
        base_confidence = signal.confidence
        
        # Apply strategy type weight
        strategy_weight = self.fusion_weights[signal.strategy_type]
        
        # Apply time-based decay
        time_decay = 1.0 - min(1.0, (datetime.now() - signal.timestamp).total_seconds() / 3600)
        
        # Calculate final confidence
        final_confidence = base_confidence * strategy_weight * time_decay
        
        return float(np.clip(final_confidence, 0, 1))
        
    def fuse_signals(self, symbol: str) -> Dict:
        """
        Fuse multiple signals into a single decision
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dict containing:
            - final_signal: Fused signal strength
            - confidence: Combined confidence
            - breakdown: Contribution breakdown
            - timestamp: Current timestamp
        """
        try:
            # Get relevant signals
            relevant_signals = [
                s for s in self.signals
                if s.symbol == symbol and
                (datetime.now() - s.timestamp) < timedelta(hours=24)
            ]
            
            if not relevant_signals:
                return {
                    'final_signal': 0.0,
                    'confidence': 0.0,
                    'breakdown': {},
                    'timestamp': datetime.now().isoformat()
                }
            
            # Prepare data for fusion
            signal_data = pd.DataFrame([
                {
                    'strength': s.signal_strength,
                    'confidence': s.confidence,
                    'type': s.strategy_type.value
                }
                for s in relevant_signals
            ])
            
            # Scale and transform data
            scaled_data = self.scaler.fit_transform(signal_data[['strength', 'confidence']])
            transformed_data = self.pca.fit_transform(scaled_data)
            
            # Calculate weighted average
            weights = np.array([
                self.fusion_weights[StrategyType(s['type'])] for s in signal_data.to_dict('records')
            ])
            
            final_signal = np.average(transformed_data[:, 0], weights=weights)
            final_confidence = np.average(signal_data['confidence'], weights=weights)
            
            # Generate breakdown
            breakdown = {
                signal.strategy_type.value: {
                    'signal': float(signal.signal_strength),
                    'confidence': float(signal.confidence),
                    'weight': float(self.fusion_weights[signal.strategy_type])
                }
                for signal in relevant_signals
            }
            
            return {
                'final_signal': float(final_signal),
                'confidence': float(final_confidence),
                'breakdown': breakdown,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fusing signals: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error fusing signals: {str(e)}"
            )
            
    def get_signal_correlation(self) -> Dict:
        """
        Get correlation between different signal types
        
        Returns:
            Dict containing correlation matrix
        """
        try:
            if not self.signals:
                return {}
                
            # Create correlation matrix
            correlation_matrix = {}
            
            # Calculate pairwise correlations
            for type1 in StrategyType:
                for type2 in StrategyType:
                    if type1 != type2:
                        signals1 = [
                            s.signal_strength for s in self.signals
                            if s.strategy_type == type1
                        ]
                        signals2 = [
                            s.signal_strength for s in self.signals
                            if s.strategy_type == type2
                        ]
                        
                        if signals1 and signals2:
                            correlation = np.corrcoef(signals1, signals2)[0, 1]
                            correlation_matrix[f"{type1.value}_{type2.value}"] = float(correlation)
            
            return correlation_matrix
            
        except Exception as e:
            logger.error(f"Error calculating correlations: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating correlations: {str(e)}"
            )
            
    def get_fusion_explanation(self, symbol: str) -> str:
        """
        Generate AI explanation for fusion decision
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Natural language explanation of fusion decision
        """
        try:
            # Get fusion result
            fusion_result = self.fuse_signals(symbol)
            
            # Generate explanation
            breakdown = fusion_result['breakdown']
            main_factors = sorted(
                breakdown.items(),
                key=lambda x: x[1]['weight'] * x[1]['confidence'],
                reverse=True
            )[:3]  # Top 3 factors
            
            explanation = f"Fusion decision for {symbol}:\n\n"
            explanation += f"Final signal: {fusion_result['final_signal']:.2f}\n"
            explanation += f"Confidence: {fusion_result['confidence']:.2f}\n\n"
            explanation += "Main contributing factors:\n"
            
            for factor in main_factors:
                explanation += f"- {factor[0]}: "
                explanation += f"Signal {factor[1]['signal']:.2f}, "
                explanation += f"Confidence {factor[1]['confidence']:.2f}, "
                explanation += f"Weight {factor[1]['weight']:.2f}\n"
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating explanation: {str(e)}"
            )
