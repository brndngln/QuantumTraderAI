from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from fastapi import HTTPException
import json
from enum import Enum
from scipy.stats import norm

logger = logging.getLogger(__name__)

# Define agent types
AGENT_TYPES = {
    'technical': {
        'weight': 0.4,
        'confidence_threshold': 0.7,
        'signal_weight': 0.8
    },
    'fundamental': {
        'weight': 0.3,
        'confidence_threshold': 0.6,
        'signal_weight': 0.7
    },
    'sentiment': {
        'weight': 0.2,
        'confidence_threshold': 0.5,
        'signal_weight': 0.6
    },
    'macro': {
        'weight': 0.1,
        'confidence_threshold': 0.4,
        'signal_weight': 0.5
    }
}

class AgentSignal(BaseModel):
    agent_type: str
    signal: float
    confidence: float
    timestamp: datetime
    metadata: Dict

class AgentVoting:
    def __init__(self):
        self.agents = {}
        self.votes = {}
        self.last_decision = None
        
    def process_agent_signal(self, signal: AgentSignal) -> Dict:
        """
        Process a signal from an agent
        
        Args:
            signal: AgentSignal object
            
        Returns:
            Dict containing vote breakdown
        """
        try:
            # Validate signal
            if signal.agent_type not in AGENT_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown agent type: {signal.agent_type}"
                )
                
            # Store signal
            if signal.agent_type not in self.agents:
                self.agents[signal.agent_type] = []
                
            self.agents[signal.agent_type].append(signal)
            
            # Calculate vote
            vote = self._calculate_vote(signal)
            
            # Store vote
            self.votes[signal.agent_type] = vote
            
            # Generate decision if enough votes
            decision = self._generate_decision()
            
            return {
                'agent_type': signal.agent_type,
                'vote': vote,
                'decision': decision,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing agent signal: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing agent signal: {str(e)}"
            )
            
    def _calculate_vote(self, signal: AgentSignal) -> float:
        """
        Calculate vote weight for an agent
        """
        try:
            # Get agent parameters
            params = AGENT_TYPES[signal.agent_type]
            
            # Calculate base vote
            base_vote = signal.signal * params['signal_weight']
            
            # Adjust based on confidence
            confidence_factor = min(1.0, max(0.0, (signal.confidence - params['confidence_threshold']) / 0.3))
            
            # Calculate final vote
            final_vote = base_vote * confidence_factor * params['weight']
            
            return float(np.clip(final_vote, -1, 1))
            
        except Exception as e:
            logger.error(f"Error calculating vote: {str(e)}")
            return 0.0
            
    def _generate_decision(self) -> Dict:
        """
        Generate final decision from votes
        
        Returns:
            Dict containing:
            - final_signal: Combined signal
            - confidence: Combined confidence
            - breakdown: Vote breakdown
        """
        try:
            if not self.votes:
                return {
                    'final_signal': 0.0,
                    'confidence': 0.0,
                    'breakdown': {}
                }
                
            # Calculate weighted average
            total_weight = sum(AGENT_TYPES[t]['weight'] for t in self.votes)
            
            final_signal = sum(
                v * AGENT_TYPES[t]['weight'] / total_weight
                for t, v in self.votes.items()
            )
            
            # Calculate confidence
            confidence = np.mean([
                abs(v) for v in self.votes.values()
            ])
            
            # Generate breakdown
            breakdown = {
                t: {
                    'vote': float(v),
                    'weight': float(AGENT_TYPES[t]['weight']),
                    'confidence': float(abs(v))
                }
                for t, v in self.votes.items()
            }
            
            return {
                'final_signal': float(final_signal),
                'confidence': float(confidence),
                'breakdown': breakdown,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating decision: {str(e)}")
            return {
                'final_signal': 0.0,
                'confidence': 0.0,
                'breakdown': {},
                'error': str(e)
            }
            
    def get_agent_stats(self, agent_type: str) -> Dict:
        """
        Get statistics for an agent type
        
        Returns:
            Dict containing:
            - signal_count: Number of signals
            - avg_signal: Average signal strength
            - avg_confidence: Average confidence
            - correlation: Signal correlation
        """
        try:
            if agent_type not in self.agents:
                return {
                    'signal_count': 0,
                    'avg_signal': 0.0,
                    'avg_confidence': 0.0,
                    'correlation': 0.0
                }
                
            signals = self.agents[agent_type]
            
            # Calculate statistics
            signal_strengths = [s.signal for s in signals]
            confidences = [s.confidence for s in signals]
            
            avg_signal = np.mean(signal_strengths)
            avg_confidence = np.mean(confidences)
            
            # Calculate correlation with final decisions
            if self.last_decision:
                correlation = np.corrcoef(
                    signal_strengths,
                    [self.last_decision['final_signal']] * len(signals)
                )[0, 1]
            else:
                correlation = 0.0
            
            return {
                'signal_count': len(signals),
                'avg_signal': float(avg_signal),
                'avg_confidence': float(avg_confidence),
                'correlation': float(correlation),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting agent stats: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting agent stats: {str(e)}"
            )
            
    def get_ensemble_metrics(self) -> Dict:
        """
        Get metrics for the entire ensemble
        
        Returns:
            Dict containing:
            - diversity: Ensemble diversity
            - correlation_matrix: Agent correlation matrix
            - signal_stability: Signal stability metrics
            - confidence_distribution: Confidence distribution
        """
        try:
            if not self.agents:
                return {
                    'diversity': 0.0,
                    'correlation_matrix': {},
                    'signal_stability': {},
                    'confidence_distribution': {}
                }
                
            # Calculate diversity
            signals = {
                t: [s.signal for s in self.agents[t]]
                for t in self.agents
            }
            
            # Calculate correlation matrix
            correlation_matrix = {}
            for t1 in signals:
                for t2 in signals:
                    if t1 != t2:
                        corr = np.corrcoef(signals[t1], signals[t2])[0, 1]
                        correlation_matrix[f"{t1}_{t2}"] = float(corr)
            
            # Calculate signal stability
            signal_stability = {
                t: {
                    'std': float(np.std(signals[t])),
                    'mean': float(np.mean(signals[t])),
                    'count': len(signals[t])
                }
                for t in signals
            }
            
            # Calculate confidence distribution
            confidences = {
                t: [s.confidence for s in self.agents[t]]
                for t in self.agents
            }
            
            confidence_distribution = {
                t: {
                    'mean': float(np.mean(confidences[t])),
                    'std': float(np.std(confidences[t])),
                    'count': len(confidences[t])
                }
                for t in confidences
            }
            
            return {
                'diversity': float(np.mean([1 - abs(c) for c in correlation_matrix.values()])),
                'correlation_matrix': correlation_matrix,
                'signal_stability': signal_stability,
                'confidence_distribution': confidence_distribution,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting ensemble metrics: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting ensemble metrics: {str(e)}"
            )
