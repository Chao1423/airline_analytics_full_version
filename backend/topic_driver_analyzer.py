#!/usr/bin/env python3
"""
Topic Driver Analyzer
Uses OLS regression analysis to explain how ratings are driven by topic shares
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from statsmodels.api import OLS, add_constant
import warnings
warnings.filterwarnings('ignore')


class TopicDriverAnalyzer:
    """Topic Driver Analyzer"""
    
    def __init__(self):
        pass
    
    def normalize_topic_scores_to_shares(self, reviews_topics_data: List[Tuple]) -> pd.DataFrame:
        """
        Normalize topic_score to topic shares (sum of topic scores per review equals 1)
        
        Args:
            reviews_topics_data: [(review_id, topic_id, topic_score), ...]
            
        Returns:
            DataFrame with columns: review_id, topic_id, topic_share
        """
        df = pd.DataFrame(reviews_topics_data, columns=['review_id', 'topic_id', 'topic_score'])
        
        # Group by review_id and calculate total topic_score for each review
        review_totals = df.groupby('review_id')['topic_score'].sum()
        
        # Normalize to shares (sum equals 1)
        df = df.merge(review_totals.rename('total_score'), left_on='review_id', right_index=True)
        df['topic_share'] = df['topic_score'] / df['total_score']
        
        # Return normalized data
        return df[['review_id', 'topic_id', 'topic_share']]
    
    def pivot_topics_to_wide(self, topics_df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert topic data to wide format (one row per review, one column per topic)
        
        Args:
            topics_df: DataFrame with columns: review_id, topic_id, topic_share
            
        Returns:
            DataFrame with columns: review_id, topic_1, topic_2, ..., topic_k
        """
        # Pivot to wide format
        df_wide = topics_df.pivot(index='review_id', columns='topic_id', values='topic_share')
        df_wide = df_wide.fillna(0)  # Fill missing values with 0
        df_wide.reset_index(inplace=True)
        
        # Rename columns
        df_wide.columns = ['review_id'] + [f'topic_{int(col)}' for col in df_wide.columns[1:]]
        
        return df_wide
    
    def fit_ols_regression(
        self, 
        X: pd.DataFrame, 
        y: pd.Series,
        min_samples: int = 30
    ) -> Dict:
        """
        Fit OLS regression model
        
        Note: Since topic shares sum to 1 (perfect collinearity), we need to:
        1. Add an intercept term
        2. Remove one topic as the reference category
        
        Args:
            X: Feature matrix (topic shares)
            y: Target variable (rating)
            min_samples: Minimum number of samples
            
        Returns:
            Dictionary containing coefficients, standard errors, p-values, confidence intervals, etc.
        """
        if len(y) < min_samples:
            raise ValueError(f"Insufficient samples: {len(y)} < {min_samples}")
        
        # Remove review_id column (if exists)
        if 'review_id' in X.columns:
            X_features = X.drop('review_id', axis=1)
        else:
            X_features = X
        
        # Since topic shares sum to 1, there is perfect collinearity
        # Solution: Remove the first topic as reference category, add intercept
        topic_columns = [col for col in X_features.columns if col.startswith('topic_')]
        
        if len(topic_columns) == 0:
            raise ValueError("No topic columns found in X")
        
        # Select reference category: use the first topic (sorted by topic_id)
        topic_ids = [int(col.replace('topic_', '')) for col in topic_columns]
        reference_topic_id = min(topic_ids)
        reference_column = f'topic_{reference_topic_id}'
        
        # Remove reference category, keep other topics
        X_without_reference = X_features.drop(columns=[reference_column], errors='ignore')
        
        # Ensure correct data types (convert to float)
        X_array = X_without_reference.values.astype(float)
        y_array = y.values.astype(float) if hasattr(y, 'values') else y.astype(float)
        
        # Get feature names (excluding intercept)
        feature_names_without_const = X_without_reference.columns.tolist()
        
        # Add intercept term (add_constant returns numpy array)
        X_with_intercept = add_constant(X_array, has_constant='add')
        
        # Build parameter names list (including intercept)
        param_names = ['const'] + feature_names_without_const
        
        # Fit OLS model
        model = OLS(y_array, X_with_intercept)
        results = model.fit()
        
        # Extract results
        coefficients = results.params
        std_errors = results.bse
        p_values = results.pvalues
        conf_int = results.conf_int(alpha=0.05)  # 95% confidence interval
        
        # Calculate R²
        r_squared = results.rsquared
        
        # Handle intercept
        # coefficients could be Series or numpy array
        if hasattr(coefficients, 'index'):
            # Series
            intercept = float(coefficients['const']) if 'const' in coefficients.index else 0.0
        else:
            # numpy array - const is the first parameter
            intercept = float(coefficients[0]) if len(coefficients) > 0 else 0.0
        
        # Handle conf_int (could be DataFrame or numpy array)
        ci_low_dict = {}
        ci_high_dict = {}
        
        if hasattr(conf_int, 'iloc'):
            # DataFrame
            for name in feature_names_without_const:
                if name in conf_int.index:
                    ci_low_dict[name] = float(conf_int.loc[name, 0])
                    ci_high_dict[name] = float(conf_int.loc[name, 1])
        else:
            # numpy array - need manual mapping (skip const, start from index 1)
            for i, name in enumerate(feature_names_without_const):
                idx = i + 1  # Skip const (index 0)
                if idx < len(conf_int):
                    ci_low_dict[name] = float(conf_int[idx, 0])
                    ci_high_dict[name] = float(conf_int[idx, 1])
        
        # In OLS regression, when we remove one topic as reference category and add intercept:
        # - Intercept represents the rating when all non-reference topics have share 0 (i.e., only reference topic)
        # - Other topics' coefficients represent: when that topic's share increases by 1 unit (while reference topic's share decreases by 1 unit), the change in rating
        # 
        # To uniformly represent all topics' coefficients, we need:
        # - Reference topic's coefficient = intercept (baseline rating)
        # - Other topics' coefficients = current coefficient (difference relative to reference topic, can be negative)
        # 
        # This way, coefficients can be directly interpreted as "difference relative to reference topic":
        # - Positive coefficient: this topic has greater impact on rating than reference topic
        # - Negative coefficient: this topic has lesser impact on rating than reference topic (or more negative)
        
        # Build results dictionary (including reference category)
        coefficients_dict = {}
        std_errors_dict = {}
        p_values_dict = {}
        
        # Add reference category (coefficient is intercept, representing baseline rating)
        reference_coef = intercept
        coefficients_dict[reference_column] = reference_coef
        # Reference category's standard error and p-value set to 0 (since it's the baseline, no standard error)
        std_errors_dict[reference_column] = 0.0
        p_values_dict[reference_column] = 1.0  # p-value set to 1.0 (no significance)
        # Reference category's confidence interval uses intercept's confidence interval
        if hasattr(conf_int, 'iloc'):
            ci_low_dict[reference_column] = float(conf_int.loc['const', 0]) if 'const' in conf_int.index else reference_coef
            ci_high_dict[reference_column] = float(conf_int.loc['const', 1]) if 'const' in conf_int.index else reference_coef
        else:
            ci_low_dict[reference_column] = float(conf_int[0, 0]) if len(conf_int) > 0 else reference_coef
            ci_high_dict[reference_column] = float(conf_int[0, 1]) if len(conf_int) > 0 else reference_coef
        
        # Add other topics (coefficient = current coefficient, can be negative)
        # Note: current coefficient represents difference relative to reference topic, can be negative
        for i, name in enumerate(feature_names_without_const):
            # In numpy array, const is index 0, other topics start from index 1
            if hasattr(coefficients, 'index'):
                # Series
                if name in coefficients.index:
                    # Coefficient = current coefficient (can be negative, indicating negative impact relative to reference topic)
                    coef_value = float(coefficients[name])
                    coefficients_dict[name] = coef_value
                    std_errors_dict[name] = float(std_errors[name])
                    p_values_dict[name] = float(p_values[name])
                    # Confidence interval doesn't need adjustment (already represents difference relative to reference topic)
                    if name in ci_low_dict:
                        pass  # Keep original value
            else:
                # numpy array - topics start from index 1 (index 0 is const)
                idx = i + 1
                if idx < len(coefficients):
                    # Coefficient = current coefficient (can be negative, indicating negative impact relative to reference topic)
                    coef_value = float(coefficients[idx])
                    coefficients_dict[name] = coef_value
                    std_errors_dict[name] = float(std_errors[idx])
                    p_values_dict[name] = float(p_values[idx])
                    # Confidence interval doesn't need adjustment (already represents difference relative to reference topic)
                    if name in ci_low_dict:
                        pass  # Keep original value
        
        # Build results dictionary
        all_feature_names = [reference_column] + feature_names_without_const
        results_dict = {
            'coefficients': coefficients_dict,
            'std_errors': std_errors_dict,
            'p_values': p_values_dict,
            'ci_low': ci_low_dict,
            'ci_high': ci_high_dict,
            'r_squared': float(r_squared),
            'sample_size': len(y),
            'feature_names': all_feature_names,
            'reference_topic': reference_column,  # Record reference category
            'intercept': intercept  # Record intercept
        }
        
        return results_dict
    
    def analyze_topic_drivers(
        self,
        reviews_topics_data: List[Tuple],
        ratings_data: List[Tuple],
        min_samples: int = 30
    ) -> Dict:
        """
        Analyze topic drivers (complete workflow)
        
        Args:
            reviews_topics_data: [(review_id, topic_id, topic_score), ...]
            ratings_data: [(review_id, rating), ...]
            min_samples: Minimum number of samples
            
        Returns:
            Analysis results dictionary
        """
        # Normalize topic scores to shares
        topics_df = self.normalize_topic_scores_to_shares(reviews_topics_data)
        
        # Convert to wide format
        topics_wide = self.pivot_topics_to_wide(topics_df)
        
        # Prepare rating data
        ratings_df = pd.DataFrame(ratings_data, columns=['review_id', 'rating'])
        
        # Merge data
        merged_df = topics_wide.merge(ratings_df, on='review_id', how='inner')
        
        if len(merged_df) < min_samples:
            raise ValueError(f"Insufficient samples after merge: {len(merged_df)} < {min_samples}")
        
        # Separate features and target variable
        X = merged_df.drop(['review_id', 'rating'], axis=1)
        y = merged_df['rating']
        
        # Fit OLS regression
        results = self.fit_ols_regression(X, y, min_samples=min_samples)
        
        # Add topic_id mapping
        topic_id_map = {}
        for col in X.columns:
            if col.startswith('topic_'):
                topic_id = int(col.replace('topic_', ''))
                topic_id_map[col] = topic_id
        
        results['topic_id_map'] = topic_id_map
        
        return results

