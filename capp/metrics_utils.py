import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score
from collections import Counter

def calculate_statistics(values):
    if not values:
        return {
            'mean': 0,
            'median': 0,
            'mode': 0,
            'min': 0,
            'max': 0
        }
    
    values = np.array(values)
    mode_result = Counter(values).most_common(1)
    
    return {
        'mean': np.mean(values),
        'median': np.median(values),
        'mode': mode_result[0][0] if mode_result else 0,
        'min': np.min(values),
        'max': np.max(values)
    }

def calculate_wpm(text, time_seconds):
    words = len(text.split())
    minutes = time_seconds / 60
    return words / minutes if minutes > 0 else 0

def calculate_model_metrics(metrics_queryset):
    # Prepare data for sklearn metrics
    y_true = [1 if metric.success else 0 for metric in metrics_queryset]
    y_pred = [1 if metric.confidence_score and metric.confidence_score > 0.5 else 0 
              for metric in metrics_queryset]
    
    if not y_true or not y_pred:
        return {
            'f1': 0,
            'precision': 0,
            'recall': 0,
            'accuracy': 0
        }
    
    return {
        'f1': f1_score(y_true, y_pred, zero_division=0),
        'precision': precision_score(y_true, y_pred, zero_division=0),
        'recall': recall_score(y_true, y_pred, zero_division=0),
        'accuracy': accuracy_score(y_true, y_pred)
    } 