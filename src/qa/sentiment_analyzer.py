"""Sentiment analysis for call interactions"""

from typing import Dict, Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from src.utils.logging import get_logger

logger = get_logger(__name__)


class SentimentAnalyzer:
    """Sentiment analysis using VADER"""

    def __init__(self):
        """Initialize sentiment analyzer"""
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores and label
        """
        try:
            scores = self.analyzer.polarity_scores(text)

            # Determine label
            compound = scores["compound"]
            if compound >= 0.05:
                label = "positive"
            elif compound <= -0.05:
                label = "negative"
            else:
                label = "neutral"

            return {
                "score": compound,  # -1 to 1
                "positive": scores["pos"],
                "neutral": scores["neu"],
                "negative": scores["neg"],
                "label": label,
            }

        except Exception as e:
            logger.error("sentiment_analysis_error", error=str(e))
            return {
                "score": 0.0,
                "positive": 0.0,
                "neutral": 1.0,
                "negative": 0.0,
                "label": "neutral",
            }

