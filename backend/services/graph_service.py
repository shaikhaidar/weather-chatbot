"""
Graph Service — Knowledge graph builder from weather sensor data.
Builds node-edge knowledge graphs representing sensor relationships
and exports them as Plotly network visualizations.
"""
from typing import Any, Dict, List, Optional
import numpy as np


class GraphService:
    """
    Constructs knowledge graphs showing correlations and spatial relationships
    between weather sensors/features and returns Plotly scatter+edge configs.
    """

    @staticmethod
    def build_correlation_graph(
        feature_importances: List[Dict[str, Any]],
        threshold: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Build a network graph from Redacted feature importances.
        Each feature = node; edges connect features above the importance threshold to 'temperature'.
        Returns a Plotly figure config.
        """
        if not feature_importances:
            return {}

        features = [f["feature"] for f in feature_importances]
        importances = [f["importance"] for f in feature_importances]

        # Place nodes in a circle
        n = len(features)
        angles = [2 * np.pi * i / n for i in range(n)]
        x_nodes = [np.cos(a) for a in angles]
        y_nodes = [np.sin(a) for a in angles]

        # Build edges: connect each feature to the most important one
        hub_idx = 0
        edge_x, edge_y = [], []
        for i in range(1, n):
            if importances[i] > threshold:
                edge_x += [x_nodes[hub_idx], x_nodes[i], None]
                edge_y += [y_nodes[hub_idx], y_nodes[i], None]

        # Scale node sizes by importance
        max_imp = max(importances) if importances else 1
        node_sizes = [10 + 40 * (imp / max_imp) for imp in importances]
        node_colors = importances

        return {
            "data": [
                {   # Edges
                    "x": edge_x, "y": edge_y,
                    "mode": "lines",
                    "type": "scatter",
                    "line": {"width": 1, "color": "#4b5563"},
                    "hoverinfo": "none",
                    "name": "Connections",
                },
                {   # Nodes
                    "x": x_nodes, "y": y_nodes,
                    "mode": "markers+text",
                    "type": "scatter",
                    "text": features,
                    "textposition": "top center",
                    "marker": {
                        "size": node_sizes,
                        "color": node_colors,
                        "colorscale": "Viridis",
                        "showscale": True,
                        "colorbar": {"title": "Importance"},
                    },
                    "name": "Features",
                    "hovertemplate": "<b>%{text}</b><br>Importance: %{marker.color:.4f}<extra></extra>",
                },
            ],
            "layout": {
                "title": "Feature Knowledge Graph",
                "showlegend": False,
                "xaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
                "yaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
                "template": "plotly_dark",
                "margin": {"l": 20, "r": 20, "t": 50, "b": 20},
            },
        }

    @staticmethod
    def build_spatial_node_graph(node_readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Visualize multi-node spatial weather station layout.
        Each node = a sensor station; size = temperature value.
        """
        if not node_readings:
            return {}

        n = len(node_readings)
        x_pos = list(range(n))
        y_pos = [0] * n
        labels = [f"Station {r['node_id']}" for r in node_readings]
        temps = [r.get("temperature", 0) for r in node_readings]
        humidities = [r.get("humidity", 0) for r in node_readings]

        # Draw edges between adjacent nodes
        edge_x, edge_y = [], []
        for i in range(n - 1):
            edge_x += [x_pos[i], x_pos[i + 1], None]
            edge_y += [y_pos[i], y_pos[i + 1], None]

        return {
            "data": [
                {
                    "x": edge_x, "y": edge_y,
                    "mode": "lines",
                    "type": "scatter",
                    "line": {"width": 2, "color": "#6366f1"},
                    "hoverinfo": "none",
                    "name": "Links",
                },
                {
                    "x": x_pos, "y": y_pos,
                    "mode": "markers+text",
                    "type": "scatter",
                    "text": labels,
                    "textposition": "top center",
                    "marker": {
                        "size": [20 + t for t in temps],
                        "color": humidities,
                        "colorscale": "Blues",
                        "showscale": True,
                        "colorbar": {"title": "Humidity %"},
                    },
                    "customdata": list(zip(temps, humidities)),
                    "hovertemplate": "<b>%{text}</b><br>Temp: %{customdata[0]}°C<br>Humidity: %{customdata[1]}%<extra></extra>",
                    "name": "Stations",
                },
            ],
            "layout": {
                "title": "Spatial Weather Station Network",
                "xaxis": {"title": "Station Index", "showgrid": False},
                "yaxis": {"showgrid": False, "showticklabels": False},
                "template": "plotly_dark",
            },
        }
