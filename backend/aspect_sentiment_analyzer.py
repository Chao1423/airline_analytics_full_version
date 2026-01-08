#!/usr/bin/env python3
"""
Aspect-based Sentiment Analysis
Uses existing sentiment pipeline and keyword matching to identify sentiment for different aspects
"""

import re
from typing import Dict, List, Tuple
from sentModel import sentModel

class AspectSentimentAnalyzer:
    """Aspect-based sentiment analyzer"""
    
    def __init__(self):
        self.sent_model = sentModel()
        
        # Define keywords for each aspect
        self.aspect_keywords = {
            'Seat Comfort': [
                'seat', 'sitting', 'comfortable', 'legroom', 'space', 'cushion', 
                'recline', 'width', 'padding', 'ergonomic', 'uncomfortable', 'cramped'
            ],
            'Cabin Staff & Service': [
                'staff', 'crew', 'attendant', 'service', 'friendly', 'helpful',
                'professional', 'courteous', 'polite', 'rude', 'unhelpful', 'smile'
            ],
            'Food & Beverages': [
                'food', 'meal', 'dinner', 'lunch', 'breakfast', 'beverage', 'drink',
                'taste', 'delicious', 'tasty', 'quality', 'menu', 'catering', 'snack'
            ],
            'Inflight Entertainment': [
                'entertainment', 'movie', 'tv', 'screen', 'music', 'games', 'wifi',
                'film', 'show', 'program', 'channel', 'selection', 'headphone'
            ],
            'Ground Service': [
                'ground', 'check-in', 'boarding', 'gate', 'luggage', 'baggage',
                'terminal', 'queue', 'wait', 'delay', 'efficient', 'slow'
            ],
            'Wifi Connectivity': [
                'wifi', 'internet', 'connection', 'connectivity', 'network', 'signal',
                'online', 'streaming', 'download', 'speed', 'free', 'paid'
            ],
            'Value for Money': [
                'price', 'cost', 'value', 'money', 'expensive', 'cheap', 'worth',
                'affordable', 'budget', 'pricing', 'fee', 'charge', 'reasonable'
            ]
        }
    
    def extract_aspect_sentences(self, text: str) -> Dict[str, List[str]]:
        """
        Extract sentences related to each aspect from text
        
        Args:
            text: Review text
            
        Returns:
            Dictionary with aspect names as keys and related sentences as values
        """
        # Clean text
        text = text.lower()
        
        # Split by sentences (simple implementation)
        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        aspect_sentences = {aspect: [] for aspect in self.aspect_keywords.keys()}
        
        for sentence in sentences:
            for aspect, keywords in self.aspect_keywords.items():
                # Check if sentence contains keywords for this aspect
                if any(keyword in sentence for keyword in keywords):
                    aspect_sentences[aspect].append(sentence)
        
        return aspect_sentences
    
    def analyze_aspect_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment scores for each aspect
        
        Args:
            text: Review text
            
        Returns:
            Dictionary with aspect names as keys and sentiment scores (-1.0 to 1.0) as values
        """
        aspect_sentences = self.extract_aspect_sentences(text)
        aspect_scores = {}
        
        for aspect, sentences in aspect_sentences.items():
            if not sentences:
                # If no related sentences found, return None
                aspect_scores[aspect] = None
                continue
            
            # Merge all related sentences
            aspect_text = ' '.join(sentences)
            
            # Use sentiment model for analysis
            try:
                score, _, _, _ = self.sent_model.run_score(aspect_text, num_features=10)
                aspect_scores[aspect] = float(score)
            except Exception as e:
                print(f"Error analyzing aspect {aspect}: {e}")
                aspect_scores[aspect] = None
        
        return aspect_scores
    
    def analyze_batch(self, texts: List[str]) -> Dict[str, List[float]]:
        """
        Batch analyze aspect sentiment for multiple reviews
        
        Args:
            texts: List of review texts
            
        Returns:
            Dictionary with aspect names as keys and lists of all scores for that aspect as values
        """
        all_aspect_scores = {aspect: [] for aspect in self.aspect_keywords.keys()}
        
        for text in texts:
            aspect_scores = self.analyze_aspect_sentiment(text)
            for aspect, score in aspect_scores.items():
                if score is not None:
                    all_aspect_scores[aspect].append(score)
        
        return all_aspect_scores
    
    def get_average_aspect_scores(self, texts: List[str]) -> Dict[str, float]:
        """
        Get average aspect sentiment scores for multiple reviews
        
        Args:
            texts: List of review texts
            
        Returns:
            Dictionary with aspect names as keys and average scores (-1.0 to 1.0, converted to 0-5 scale) as values
        """
        all_aspect_scores = self.analyze_batch(texts)
        
        # Calculate average and convert to 0-5 scale
        # sentiment_score: -1.0 (negative) to 1.0 (positive)
        # Convert to: 0 (worst) to 5 (best)
        # Formula: (sentiment_score + 1) / 2 * 5
        average_scores = {}
        
        for aspect, scores in all_aspect_scores.items():
            if scores:
                avg_sentiment = sum(scores) / len(scores)
                # Convert to 0-5 scale
                avg_score = (avg_sentiment + 1) / 2 * 5
                average_scores[aspect] = round(avg_score, 2)
            else:
                average_scores[aspect] = None
        
        return average_scores

