"""Tests for QA components"""

import pytest

from src.qa.sentiment_analyzer import SentimentAnalyzer


def test_sentiment_analyzer():
    """Test sentiment analysis"""
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("I am very happy with the service!")
    assert "score" in result
    assert "label" in result
    assert result["label"] in ["positive", "neutral", "negative"]

