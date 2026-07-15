"""
CSV Service — Data processing, cleaning, normalization and Plotly visualization configs.
"""
import io
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from utils.logger import logger


class CSVService:
    """
    Handles all CSV-centric operations: profiling, cleaning, transformation,
    normalization, and generating Plotly.js chart configs for the frontend.
    """

    @staticmethod
    def load_dataframe(filepath: str) -> pd.DataFrame:
        return pd.read_csv(filepath)

    @staticmethod
    def clean(df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicates, drop all-NaN columns, ffill remaining NaNs."""
        df = df.drop_duplicates()
        df = df.dropna(axis=1, how="all")
        df = df.fillna(method="ffill").fillna(method="bfill")
        return df

    @staticmethod
    def normalize(df: pd.DataFrame) -> pd.DataFrame:
        """Min-max normalize all numeric columns to [0, 1]."""
        numeric_cols = df.select_dtypes(include="number").columns
        df[numeric_cols] = (df[numeric_cols] - df[numeric_cols].min()) / (
            df[numeric_cols].max() - df[numeric_cols].min() + 1e-9
        )
        return df

    @staticmethod
    def profile(df: pd.DataFrame) -> Dict[str, Any]:
        """Return a statistical profile of the dataframe."""
        numeric = df.select_dtypes(include="number")
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "numeric_columns": list(numeric.columns),
            "missing_values": int(df.isnull().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "stats": {
                col: {
                    "mean": round(float(numeric[col].mean()), 4),
                    "std": round(float(numeric[col].std()), 4),
                    "min": round(float(numeric[col].min()), 4),
                    "max": round(float(numeric[col].max()), 4),
                }
                for col in numeric.columns
            },
        }

    @staticmethod
    def generate_trend_chart(df: pd.DataFrame, col: str, max_points: int = 100) -> Dict[str, Any]:
        """Generate a Plotly line chart config for a single column trend."""
        if col not in df.columns:
            return {}
        series = df[col].dropna()
        step = max(1, len(series) // max_points)
        sampled = series.iloc[::step]
        return {
            "data": [{
                "x": list(range(len(sampled))),
                "y": [round(float(v), 4) for v in sampled.values],
                "type": "scatter",
                "mode": "lines",
                "name": col,
                "line": {"color": "#3b82f6", "width": 2},
            }],
            "layout": {
                "title": f"{col} Trend",
                "xaxis": {"title": "Time Index"},
                "yaxis": {"title": col},
                "template": "plotly_dark",
            },
        }

    @staticmethod
    def generate_correlation_heatmap(df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a Plotly heatmap config for the correlation matrix."""
        numeric = df.select_dtypes(include="number")
        corr = numeric.corr().round(3)
        cols = list(corr.columns)
        return {
            "data": [{
                "z": corr.values.tolist(),
                "x": cols,
                "y": cols,
                "type": "heatmap",
                "colorscale": "RdBu",
                "zmin": -1,
                "zmax": 1,
            }],
            "layout": {
                "title": "Sensor Correlation Matrix",
                "template": "plotly_dark",
            },
        }

    @staticmethod
    def generate_distribution_chart(df: pd.DataFrame, col: str) -> Dict[str, Any]:
        """Generate a histogram for a single column."""
        if col not in df.columns:
            return {}
        values = df[col].dropna().tolist()
        return {
            "data": [{
                "x": [round(float(v), 4) for v in values],
                "type": "histogram",
                "name": col,
                "marker": {"color": "#8b5cf6"},
                "nbinsx": 30,
            }],
            "layout": {
                "title": f"{col} Distribution",
                "xaxis": {"title": col},
                "yaxis": {"title": "Count"},
                "template": "plotly_dark",
            },
        }
