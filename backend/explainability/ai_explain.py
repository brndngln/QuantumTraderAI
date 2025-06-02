from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel
import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM
import json
from datetime import datetime
import torch
from enum import Enum
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

# Initialize explanation models
EXPLANATION_PIPELINE = pipeline(
    "text-classification",
    model="distilbert-base-uncased-finetuned-sst-2-english",
    return_all_scores=True
)

FACTOR_ANALYSIS_MODEL = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased-finetuned-sst-2-english"
)
FACTOR_ANALYSIS_TOKENIZER = AutoTokenizer.from_pretrained(
    "distilbert-base-uncased-finetuned-sst-2-english"
)

# Initialize counterfactual generation model
COUNTERFACTUAL_MODEL = AutoModelForCausalLM.from_pretrained("gpt2")
COUNTERFACTUAL_TOKENIZER = AutoTokenizer.from_pretrained("gpt2")

class SentimentType(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ExplanationType(Enum):
    CAUSAL = "causal"
    COUNTERFACTUAL = "counterfactual"
    TEMPORAL = "temporal"
    UNCERTAINTY = "uncertainty"

class TradeExplanation(BaseModel):
    trade_id: str
    strategy_name: str
    confidence: float
    confidence_level: ConfidenceLevel
    factors: Dict[str, float]
    sentiment: SentimentType
    timestamp: datetime
    explanation: str
    factor_analysis: Dict[str, Any]
    risk_factors: Dict[str, float]
    market_context: Dict[str, Any]
    causal_analysis: Dict[str, Any]
    counterfactual_analysis: Dict[str, Any]
    temporal_analysis: Dict[str, Any]
    uncertainty_analysis: Dict[str, Any]
    language_analysis: Dict[str, Any]
    performance_metrics: Dict[str, Any]

class AIExplainability:
    def __init__(self):
        self.explanations = {}
        self.sentiment_thresholds = {
            SentimentType.POSITIVE: 0.7,
            SentimentType.NEUTRAL: 0.5,
            SentimentType.NEGATIVE: 0.3
        }
        self.confidence_thresholds = {
            ConfidenceLevel.HIGH: 0.8,
            ConfidenceLevel.MEDIUM: 0.5,
            ConfidenceLevel.LOW: 0.3
        }
        self.performance_metrics = {
            'accuracy': 0.0,
            'consistency': 0.0,
            'reliability': 0.0
        }
        
    async def explain_trade(self, trade_data: Dict) -> TradeExplanation:
        """
        Generate AI-powered explanation for a trade
        
        Args:
            trade_data: Trade data containing:
                - trade_id: str
                - strategy_name: str
                - factors: Dict of contributing factors
                - market_data: Market conditions
                - risk_metrics: Risk assessment
                - context: Additional context
                - historical_data: Historical trade data
            
        Returns:
            TradeExplanation: Structured explanation
        """
        try:
            # Extract features
            features = self._extract_features(trade_data)
            
            # Generate explanation
            explanation = self._generate_explanation(features)
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(explanation)
            
            # Analyze factors
            factor_analysis = self._analyze_factors(features)
            
            # Calculate confidence
            confidence = self._calculate_confidence(features)
            
            # Perform advanced analyses
            causal_analysis = self._analyze_causal_relationships(features)
            counterfactual_analysis = self._generate_counterfactuals(features)
            temporal_analysis = self._analyze_temporal_patterns(features, trade_data.get('historical_data', []))
            uncertainty_analysis = self._analyze_uncertainty(features)
            language_analysis = self._analyze_language(explanation)
            
            # Update performance metrics
            self._update_performance_metrics(explanation)
            
            # Create explanation object
            trade_explanation = TradeExplanation(
                trade_id=trade_data['trade_id'],
                strategy_name=trade_data['strategy_name'],
                confidence=confidence,
                confidence_level=self._get_confidence_level(confidence),
                factors=self._normalize_factors(trade_data['factors']),
                sentiment=sentiment,
                timestamp=datetime.now(),
                explanation=explanation,
                factor_analysis=factor_analysis,
                risk_factors=trade_data.get('risk_metrics', {}).get('factors', {}),
                market_context=trade_data.get('market_data', {}).get('context', {}),
                causal_analysis=causal_analysis,
                counterfactual_analysis=counterfactual_analysis,
                temporal_analysis=temporal_analysis,
                uncertainty_analysis=uncertainty_analysis,
                language_analysis=language_analysis,
                performance_metrics=self.performance_metrics
            )
            
            # Store in memory
            self.explanations[trade_data['trade_id']] = trade_explanation
            
            return trade_explanation
            
        except Exception as e:
            logger.error(f"Error explaining trade: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error explaining trade: {str(e)}"
            )
            
    def _extract_features(self, trade_data: Dict) -> Dict:
        """
        Extract relevant features for explanation
        """
        features = {
            'market_trend': trade_data['market_data'].get('trend', 'unknown'),
            'volatility': trade_data['market_data'].get('volatility', 0.0),
            'risk_score': trade_data.get('risk_metrics', {}).get('score', 0.0),
            'confidence': trade_data.get('strategy_metrics', {}).get('confidence', 0.0),
            'sentiment': trade_data['market_data'].get('sentiment', 0.0),
            'volume': trade_data['market_data'].get('volume', 0.0),
            'liquidity': trade_data['market_data'].get('liquidity', 0.0),
            'market_cap': trade_data['market_data'].get('market_cap', 0.0),
            'sector': trade_data['market_data'].get('sector', 'unknown'),
            'industry': trade_data['market_data'].get('industry', 'unknown'),
            'geography': trade_data['market_data'].get('geography', 'unknown'),
            'macro_factors': trade_data['market_data'].get('macro_factors', {})
        }
        return features
        
    def _generate_explanation(self, features: Dict) -> str:
        """
        Generate natural language explanation
        """
        # Use AI to generate more detailed explanation
        prompt = f"""
        Analyze this trade:
        Market trend: {features['market_trend']}
        Volatility: {features['volatility']:.2f}
        Risk score: {features['risk_score']:.2f}
        Confidence: {features['confidence']:.2f}
        Volume: {features['volume']:.2f}
        Liquidity: {features['liquidity']:.2f}
        Market cap: {features['market_cap']:.2f}
        Sector: {features['sector']}
        Industry: {features['industry']}
        Geography: {features['geography']}
        Macro factors: {features['macro_factors']}
        
        Generate a detailed explanation including:
        1. Market conditions analysis
        2. Risk assessment
        3. Trading strategy justification
        4. Potential outcomes
        5. Sector/industry analysis
        6. Geographical impact
        7. Macroeconomic factors
        """
        
        # Use transformer model to generate explanation
        inputs = EXPLANATION_PIPELINE.tokenizer(
            prompt,
            return_tensors="pt",
            max_length=1024,
            truncation=True
        )
        
        outputs = EXPLANATION_PIPELINE.model(**inputs)
        explanation = EXPLANATION_PIPELINE.tokenizer.decode(
            outputs.logits.argmax(dim=-1),
            skip_special_tokens=True
        )
        
        return explanation
        
    def _analyze_sentiment(self, text: str) -> SentimentType:
        """
        Analyze sentiment of explanation text
        """
        # Use multiple models for sentiment analysis
        results = EXPLANATION_PIPELINE(text)[0]
        max_score = max(results, key=lambda x: x['score'])
        
        # Apply sentiment thresholds
        if max_score['score'] >= self.sentiment_thresholds[SentimentType.POSITIVE]:
            return SentimentType.POSITIVE
        elif max_score['score'] >= self.sentiment_thresholds[SentimentType.NEUTRAL]:
            return SentimentType.NEUTRAL
        return SentimentType.NEGATIVE

    def _analyze_factors(self, features: Dict) -> Dict:
        """
        Analyze contributing factors using transformer model
        """
        # Create factor analysis prompt
        factor_text = "\n".join([
            f"{k}: {v:.2f}" for k, v in features.items()
        ])
        
        # Use multiple models for analysis
        inputs = FACTOR_ANALYSIS_TOKENIZER(
            factor_text,
            return_tensors="pt",
            max_length=512,
            truncation=True
        )
        
        outputs = FACTOR_ANALYSIS_MODEL(**inputs)
        
        # Get factor importance scores
        importance_scores = torch.softmax(outputs.logits, dim=-1).squeeze().tolist()
        
        # Create comprehensive factor analysis
        analysis = {
            'importance': {
                k: float(v) for k, v in zip(features.keys(), importance_scores)
            },
            'correlations': self._calculate_correlations(features),
            'impact_factors': self._identify_impact_factors(features),
            'temporal_patterns': self._analyze_temporal_patterns(features, []),
            'causal_relationships': self._analyze_causal_relationships(features),
            'uncertainty': self._analyze_uncertainty(features)
        }
        
        return analysis

    def _analyze_causal_relationships(self, features: Dict) -> Dict:
        """
        Analyze causal relationships between factors
        """
        # Create factor pairs
        factor_pairs = []
        for i, f1 in enumerate(features):
            for j, f2 in enumerate(features):
                if i < j:
                    factor_pairs.append((f1, f2))
        
        # Analyze causal relationships
        causal_analysis = {}
        for f1, f2 in factor_pairs:
            # Calculate correlation
            corr = spearmanr(features[f1], features[f2])[0]
            
            # Generate causal explanation
            prompt = f"""
            Analyze causal relationship between {f1} and {f2}:
            Correlation: {corr:.2f}
            
            Explain potential causal relationship
            """
            
            inputs = EXPLANATION_PIPELINE.tokenizer(
                prompt,
                return_tensors="pt",
                max_length=512,
                truncation=True
            )
            
            outputs = EXPLANATION_PIPELINE.model(**inputs)
            explanation = EXPLANATION_PIPELINE.tokenizer.decode(
                outputs.logits.argmax(dim=-1),
                skip_special_tokens=True
            )
            
            causal_analysis[f"{f1}_{f2}"] = {
                'correlation': float(corr),
                'explanation': explanation,
                'confidence': float(torch.softmax(outputs.logits, dim=-1)[0][1])
            }
        
        return causal_analysis
        
    def _generate_counterfactuals(self, features: Dict) -> Dict:
        """
        Generate counterfactual scenarios
        """
        counterfactuals = {}
        
        # Generate scenarios for key factors
        for factor in features:
            if isinstance(features[factor], (int, float)):
                # Create counterfactual prompt
                prompt = f"""
                Current trade scenario:
                {factor}: {features[factor]}
                
                Generate counterfactual scenarios:
                1. What if {factor} was 20% higher?
                2. What if {factor} was 20% lower?
                """
                
                # Generate counterfactuals
                inputs = COUNTERFACTUAL_TOKENIZER(
                    prompt,
                    return_tensors="pt",
                    max_length=512,
                    truncation=True
                )
                
                outputs = COUNTERFACTUAL_MODEL.generate(
                    **inputs,
                    max_length=1024,
                    num_return_sequences=2
                )
                
                scenarios = []
                for output in outputs:
                    scenario = COUNTERFACTUAL_TOKENIZER.decode(
                        output,
                        skip_special_tokens=True
                    )
                    scenarios.append(scenario)
                
                counterfactuals[factor] = {
                    'scenarios': scenarios,
                    'impact_analysis': self._analyze_impact(scenarios)
                }
        
        return counterfactuals

    def _calculate_correlations(self, features: Dict) -> Dict:
        """
        Calculate correlations between factors
        """
        # Use multiple correlation methods
        values = np.array(list(features.values()))
        correlations = {}
        
        for i, key1 in enumerate(features):
            for j, key2 in enumerate(features):
                if i < j:
                    # Calculate different types of correlations
                    pearson = np.corrcoef(values[i], values[j])[0, 1]
                    spearman = spearmanr(values[i], values[j])[0]
                    
                    correlations[f"{key1}_{key2}"] = {
                        'pearson': float(pearson),
                        'spearman': float(spearman),
                        'confidence': float((pearson + spearman) / 2)
                    }
        
        return correlations

    def _identify_impact_factors(self, features: Dict) -> List[str]:
        """
        Identify most impactful factors
        """
        # Use multiple impact analysis methods
        impact_factors = []
        
        # Calculate factor importance
        for factor, value in features.items():
            if isinstance(value, (int, float)):
                # Calculate impact score
                impact_score = abs(value) * (1 + np.std([value]))
                
                # Check if significant impact
                if impact_score >= 0.8:
                    impact_factors.append(factor)
        
        return impact_factors

    def _calculate_confidence(self, features: Dict) -> float:
        """
        Calculate overall confidence score
        """
        # Use multiple factors for confidence calculation
        weights = {
            'risk_score': 0.3,
            'confidence': 0.4,
            'sentiment': 0.2,
            'volume': 0.1,
            'liquidity': 0.1,
            'market_cap': 0.1
        }
        
        # Calculate weighted confidence
        confidence = sum(
            features.get(k, 0.0) * weights[k] for k in weights
        )
        
        # Apply uncertainty adjustment
        uncertainty = self._analyze_uncertainty(features)
        confidence *= (1 - uncertainty['prediction_uncertainty']['std'])
        
        return float(np.clip(confidence, 0.0, 1.0))

    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """
        Convert confidence score to level
        """
        # Use dynamic thresholds based on market conditions
        thresholds = self._get_dynamic_thresholds()
        
        if confidence >= thresholds[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif confidence >= thresholds[ConfidenceLevel.MEDIUM]:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def _get_dynamic_thresholds(self) -> Dict[ConfidenceLevel, float]:
        """
        Get dynamic confidence thresholds based on market conditions
        """
        # Example: Adjust thresholds based on volatility
        volatility = self._get_market_volatility()
        
        # Adjust thresholds based on volatility
        base_thresholds = {
            ConfidenceLevel.HIGH: 0.8,
            ConfidenceLevel.MEDIUM: 0.5,
            ConfidenceLevel.LOW: 0.3
        }
        
        # Apply volatility adjustment
        volatility_factor = 1.0 + (volatility - 1.0) * 0.2
        
        return {
            level: base_thresholds[level] * volatility_factor
            for level in base_thresholds
        }

    def _get_market_volatility(self) -> float:
        """
        Get current market volatility
        """
        # Example implementation
        return 1.0  # Default volatility

    async def get_trade_explanation(self, trade_id: str) -> TradeExplanation:
        """
        Get trade explanation by ID
        """
        try:
            return self.explanations.get(trade_id)
        except Exception as e:
            logger.error(f"Error getting explanation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting explanation: {str(e)}"
            )
            
    async def get_recent_explanations(self, limit: int = 10) -> List[TradeExplanation]:
        """
        Get recent trade explanations
        """
        try:
            return list(self.explanations.values())[-limit:]
        except Exception as e:
            logger.error(f"Error getting recent explanations: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting explanations: {str(e)}"
            )
            
    async def analyze_explanation_quality(self, trade_id: str) -> Dict:
        """
        Analyze quality of a trade explanation
        """
        try:
            explanation = await self.get_trade_explanation(trade_id)
            if not explanation:
                raise HTTPException(
                    status_code=404,
                    detail="Explanation not found"
                )
                
            # Analyze explanation components
            quality = {
                'completeness': self._analyze_completeness(explanation),
                'consistency': self._analyze_consistency(explanation),
                'clarity': self._analyze_clarity(explanation),
                'confidence': explanation.confidence,
                'sentiment': explanation.sentiment.value,
                'timestamp': datetime.now().isoformat()
            }
            
            return quality
            
        except Exception as e:
            logger.error(f"Error analyzing explanation quality: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing explanation quality: {str(e)}"
            )
            
    def _analyze_completeness(self, explanation: TradeExplanation) -> float:
        """
        Analyze completeness of explanation
        """
        components = [
            'market_context' in explanation.dict(),
            'risk_factors' in explanation.dict(),
            'factor_analysis' in explanation.dict(),
            len(explanation.factors) > 0,
            len(explanation.explanation) > 50
        ]
        
        return float(np.mean(components))
        
    def _analyze_consistency(self, explanation: TradeExplanation) -> float:
        """
        Analyze consistency of explanation
        """
        # Check if sentiment matches confidence
        sentiment_score = 1.0 if explanation.sentiment == SentimentType.POSITIVE else 0.5
        confidence_score = 1.0 if explanation.confidence_level == ConfidenceLevel.HIGH else 0.5
        
        return float((sentiment_score + confidence_score) / 2)
        
    def _analyze_clarity(self, explanation: TradeExplanation) -> float:
        """
        Analyze clarity of explanation
        """
        # Use AI to analyze clarity
        prompt = f"""
        Analyze this explanation for clarity:
        {explanation.explanation}
        
        Rate clarity on scale of 0-1
        """
        
        inputs = EXPLANATION_PIPELINE.tokenizer(
            prompt,
            return_tensors="pt",
            max_length=512,
            truncation=True
        )
        
        outputs = EXPLANATION_PIPELINE.model(**inputs)
        clarity_score = float(torch.softmax(outputs.logits, dim=-1)[0][1])
        
        return clarity_score
