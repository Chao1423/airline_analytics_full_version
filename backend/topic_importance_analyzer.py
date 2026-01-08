#!/usr/bin/env python3
"""
Topic-based OLS Regression Analysis
Uses data from reviews_topics table for regression analysis to estimate the impact of topics on ratings
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from statsmodels.api import OLS, add_constant
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings
warnings.filterwarnings('ignore')


class TopicImportanceAnalyzer:
    """Topic Importance Analyzer"""
    
    def __init__(self):
        pass
    
    def pivot_topics_to_wide(self, reviews_topics_data: List[Tuple]) -> pd.DataFrame:
        """
        Convert topic data to wide format (one row per review, one column per topic)
        
        Args:
            reviews_topics_data: [(review_id, topic_id, topic_share), ...]
            
        Returns:
            DataFrame with columns: review_id, topic_1, topic_2, ..., topic_k
        """
        df = pd.DataFrame(reviews_topics_data, columns=['review_id', 'topic_id', 'topic_share'])
        
        # Pivot to wide format
        df_wide = df.pivot(index='review_id', columns='topic_id', values='topic_share')
        df_wide = df_wide.fillna(0)  # Fill missing values with 0
        df_wide.reset_index(inplace=True)
        
        # Rename columns
        df_wide.columns = ['review_id'] + [f'topic_{int(col)}' for col in df_wide.columns[1:]]
        
        return df_wide
    
    def fit_ols_regression(
        self, 
        X: pd.DataFrame, 
        y: pd.Series,
        min_samples: int = 10
    ) -> Dict:
        """
        Fit OLS regression model
        
        Args:
            X: Feature matrix (topic shares)
            y: Target variable (ratings)
            min_samples: Minimum number of samples
            
        Returns:
            Dictionary containing coefficients, standard errors, p-values, confidence intervals, etc.
        """
        if len(y) < min_samples:
            raise ValueError(f"Insufficient samples: {len(y)} < {min_samples}")
        
        # Remove intercept (topic shares sum to 1, causing multicollinearity)
        # Use all topics as features
        X_array = X.values
        
        # Fit OLS model
        model = OLS(y, X_array)
        results = model.fit()
        
        # Extract results
        coefficients = results.params
        std_errors = results.bse
        p_values = results.pvalues
        conf_int = results.conf_int(alpha=0.05)  # 95% confidence interval
        
        # Calculate R²
        r_squared = results.rsquared
        
        # Get feature names
        feature_names = X.columns.tolist()
        
        # Build results dictionary
        results_dict = {
            'coefficients': {feature_names[i]: float(coefficients[i]) for i in range(len(feature_names))},
            'std_errors': {feature_names[i]: float(std_errors[i]) for i in range(len(feature_names))},
            'p_values': {feature_names[i]: float(p_values[i]) for i in range(len(feature_names))},
            'ci_low': {feature_names[i]: float(conf_int.iloc[i, 0]) for i in range(len(feature_names))},
            'ci_high': {feature_names[i]: float(conf_int.iloc[i, 1]) for i in range(len(feature_names))},
            'r_squared': float(r_squared),
            'sample_size': len(y),
            'feature_names': feature_names
        }
        
        return results_dict
    
    def analyze_topic_importance(
        self,
        reviews_topics_data: List[Tuple],
        ratings_data: List[Tuple],
        min_samples: int = 10
    ) -> Dict:
        """
        Analyze topic importance
        
        Args:
            reviews_topics_data: [(review_id, topic_id, topic_share), ...]
            ratings_data: [(review_id, rating), ...]
            min_samples: Minimum number of samples
            
        Returns:
            Analysis results dictionary
        """
        # Convert to DataFrame
        topics_df = self.pivot_topics_to_wide(reviews_topics_data)
        ratings_df = pd.DataFrame(ratings_data, columns=['review_id', 'rating'])
        
        # Merge data
        merged_df = topics_df.merge(ratings_df, on='review_id', how='inner')
        
        if len(merged_df) < min_samples:
            raise ValueError(f"Insufficient samples after merge: {len(merged_df)} < {min_samples}")
        
        # Separate features and target
        feature_cols = [col for col in merged_df.columns if col.startswith('topic_')]
        X = merged_df[feature_cols]
        y = merged_df['rating']
        
        # Calculate average topic shares
        mean_topic_shares = X.mean().to_dict()
        
        # Fit OLS regression
        results = self.fit_ols_regression(X, y, min_samples)
        
        # Add average topic shares
        results['mean_topic_shares'] = mean_topic_shares
        
        return results
    
    def get_assumptions_and_limitations(self) -> Dict:
        """
        Return assumptions and limitations description
        
        Returns:
            Dictionary containing assumptions and limitations
        """
        return {
            'assumptions': [
                'Linear relationship: Assumes a linear relationship between topic shares and ratings',
                'Independence: Assumes reviews are independent of each other',
                'Homoscedasticity: Assumes constant variance of error terms',
                'Normality: Assumes error terms follow a normal distribution (approximately valid for large samples)',
                'No multicollinearity: Topic shares sum to 1, causing perfect multicollinearity (handled by removing intercept)'
            ],
            'limitations': [
                'Topic identification depends on text analysis quality',
                'Potential omitted variable bias (other factors affecting ratings not considered)',
                'Caution needed for causal inference (correlation does not equal causation)',
                'Sample size requirement: At least 30+ reviews recommended',
                'Number of topics: 3-20 topics recommended, too many may lead to overfitting'
            ]
        }


def create_sample_topics_data():
    """
    Create sample topic data (for testing)
    In practice, this should come from topic model output (e.g., LDA)
    """
    # Example: Assume 5 topics
    # topic_0: Service-related
    # topic_1: Seat comfort
    # topic_2: Food quality
    # topic_3: Entertainment facilities
    # topic_4: Price-value
    
    # Return empty list here, should be obtained from topic model in practice
    return []

