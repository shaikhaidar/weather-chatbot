"""
Research Engine — Statistical analysis, correlation, outlier detection, trend analysis.
"""
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from scipy import stats
from utils.logger import logger


class ResearchEngine:
    """
    Performs deep statistical analysis on weather datasets.
    Returns structured dicts that can be passed to NLGService or CSV charts.
    """

    @staticmethod
    def descriptive_stats(df: pd.DataFrame) -> Dict[str, Any]:
        numeric = df.select_dtypes(include="number")
        result = {}
        for col in numeric.columns:
            s = numeric[col].dropna()
            if len(s) == 0:
                continue
            result[col] = {
                "mean": round(float(s.mean()), 4),
                "median": round(float(s.median()), 4),
                "std": round(float(s.std()), 4),
                "min": round(float(s.min()), 4),
                "max": round(float(s.max()), 4),
                "skewness": round(float(s.skew()), 4),
                "kurtosis": round(float(s.kurtosis()), 4),
            }
        return result

    @staticmethod
    def correlation_analysis(df: pd.DataFrame) -> Dict[str, Any]:
        """Pearson correlation matrix + top correlated pairs."""
        numeric = df.select_dtypes(include="number").dropna()
        if numeric.shape[1] < 2:
            return {"error": "Not enough numeric columns"}
        corr = numeric.corr(method="pearson")
        # Find top 5 strongest absolute correlations (excluding self)
        pairs = []
        for i in range(len(corr.columns)):
            for j in range(i + 1, len(corr.columns)):
                col_a = corr.columns[i]
                col_b = corr.columns[j]
                val = corr.iloc[i, j]
                pairs.append({"feature_a": col_a, "feature_b": col_b, "correlation": round(float(val), 4)})
        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        return {
            "matrix": {col: {r: round(float(corr[col][r]), 4) for r in corr.index} for col in corr.columns},
            "top_pairs": pairs[:5],
        }

    @staticmethod
    def detect_outliers(df: pd.DataFrame, z_threshold: float = 3.0) -> Dict[str, Any]:
        """Z-score based outlier detection per column."""
        numeric = df.select_dtypes(include="number")
        result = {}
        for col in numeric.columns:
            s = numeric[col].dropna()
            z_scores = np.abs(stats.zscore(s))
            outlier_indices = list(np.where(z_scores > z_threshold)[0])
            result[col] = {
                "outlier_count": len(outlier_indices),
                "outlier_pct": round(len(outlier_indices) / len(s) * 100, 2),
                "sample_outlier_values": [round(float(s.iloc[i]), 4) for i in outlier_indices[:5]],
            }
        return result

    @staticmethod
    def trend_analysis(df: pd.DataFrame, col: str) -> Dict[str, Any]:
        """Linear trend (slope, direction) for a single sensor column."""
        if col not in df.columns:
            return {"error": f"Column '{col}' not found"}
        s = df[col].dropna()
        if len(s) < 3:
            return {"error": "Not enough data points"}
        x = np.arange(len(s))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, s.values)
        direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
        return {
            "column": col,
            "slope": round(float(slope), 6),
            "direction": direction,
            "r_squared": round(float(r_value ** 2), 4),
            "p_value": round(float(p_value), 6),
            "significant": bool(p_value < 0.05),
        }

    @staticmethod
    def full_report(df: pd.DataFrame) -> Dict[str, Any]:
        """Run all analyses and return a comprehensive research report."""
        logger.info("Running full statistical research report...")
        return {
            "descriptive_stats": ResearchEngine.descriptive_stats(df),
            "correlation_analysis": ResearchEngine.correlation_analysis(df),
            "outlier_detection": ResearchEngine.detect_outliers(df),
        }
