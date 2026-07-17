"""
GNN Service — Promoted from ml_service.py
Full spatial weather prediction using PyTorch Geometric Graph Neural Network.
"""
from typing import Any, Dict, List
import random

try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from torch_geometric.nn import GATConv
    from torch_geometric.data import Data
    from torch.nn import LayerNorm
    TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    TORCH_GEOMETRIC_AVAILABLE = False


if TORCH_AVAILABLE:
    class SpatialWeatherGNN(torch.nn.Module):
        """3-layer GAT for multi-node spatial weather prediction."""
        def __init__(self, num_node_features: int):
            super().__init__()
            if TORCH_GEOMETRIC_AVAILABLE:
                self.conv1 = GATConv(num_node_features, 32, heads=4, concat=False)
                self.ln1 = LayerNorm(32)
                self.conv2 = GATConv(32, 16, heads=4, concat=False)
                self.ln2 = LayerNorm(16)
                self.conv3 = GATConv(16, 1, heads=1, concat=False)

        def forward(self, data):
            x, edge_index = data.x, data.edge_index
            
            x = self.conv1(x, edge_index)
            x = self.ln1(x)
            x = F.elu(x)
            x = F.dropout(x, p=0.2, training=self.training)
            
            x = self.conv2(x, edge_index)
            x = self.ln2(x)
            x = F.elu(x)
            x = F.dropout(x, p=0.2, training=self.training)
            
            x = self.conv3(x, edge_index)
            return x
else:
    class SpatialWeatherGNN:
        pass


class GNNService:
    """High-level GNN inference service."""

    @staticmethod
    def predict(nodes: List[List[float]], edges: List[List[int]]) -> Dict[str, Any]:
        """
        Run a GCN forward pass on sensor node data.
        nodes: [[temperature, wind_speed, humidity], ...]
        edges: [[src, dst], ...]
        """
        if not TORCH_AVAILABLE or not TORCH_GEOMETRIC_AVAILABLE:
            # Fallback to realistic mock predictions
            preds = []
            for node in nodes:
                temp = node[0] if len(node) > 0 else 24.0
                wind = node[1] if len(node) > 1 else 10.0
                delta = 0.05 * temp - 0.02 * wind + random.uniform(-0.2, 0.2)
                preds.append(round(delta, 4))
            return {
                "status": "success",
                "spatial_predictions": preds,
                "node_count": len(nodes),
                "message": "GNN mock predictions (PyTorch is not installed)."
            }
            
        try:
            x = torch.tensor(nodes, dtype=torch.float)
            edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
            data = Data(x=x, edge_index=edge_index)

            model = SpatialWeatherGNN(num_node_features=x.shape[1])
            model.eval()
            with torch.no_grad():
                out = model(data)

            preds = out.squeeze().tolist()
            if not isinstance(preds, list):
                preds = [preds]

            return {
                "status": "success",
                "spatial_predictions": [round(p, 4) for p in preds],
                "node_count": len(nodes),
                "message": "GNN forward pass completed successfully.",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def build_nodes_from_dataframe(df: Any, sample_nodes: int = 3) -> List[List[float]]:
        """Extract representative node feature matrices directly from uploaded CSV DataFrame."""
        if not hasattr(df, "columns"):
            return [[24.2, 12.0, 60.0], [23.9, 14.0, 62.0], [24.5, 10.0, 58.0]]
            
        # Match features dynamically using aliases
        from services.dataset_service import DatasetService
        aliases = DatasetService.SENSOR_ALIASES
        
        def find_col(keys):
            for col in df.columns:
                if any(k in col.lower() for k in keys):
                    return col
            return None

        temp_col = find_col(aliases.get("temperature", []))
        wind_col = find_col(aliases.get("wind_speed", []))
        hum_col = find_col(aliases.get("humidity", []))

        # Sample rows across the dataset duration
        indices = [int(i) for i in [0, len(df)//2, len(df)-1]] if len(df) >= 3 else list(range(len(df)))
        
        nodes = []
        for idx in indices:
            t = float(df[temp_col].iloc[idx]) if temp_col and pd.notnull(df[temp_col].iloc[idx]) else 24.0
            w = float(df[wind_col].iloc[idx]) if wind_col and pd.notnull(df[wind_col].iloc[idx]) else 10.0
            h = float(df[hum_col].iloc[idx]) if hum_col and pd.notnull(df[hum_col].iloc[idx]) else 60.0
            nodes.append([round(t, 2), round(w, 2), round(h, 2)])
            
        while len(nodes) < sample_nodes:
            nodes.append([24.0, 10.0, 60.0])
            
        return nodes[:sample_nodes]

    @staticmethod
    def build_nodes_from_iot(readings: List[Dict[str, Any]]) -> List[List[float]]:
        """Convert IoTService multi-node readings into GNN node feature matrix."""
        return [
            [r.get("temperature", 0.0), r.get("wind_speed", 0.0), r.get("humidity", 0.0)]
            for r in readings
        ]

    @staticmethod
    def build_edges(n_nodes: int) -> List[List[int]]:
        """Build a simple chain graph: 0→1→2→...→n-1 (bidirectional)."""
        edges = []
        for i in range(n_nodes - 1):
            edges.append([i, i + 1])
            edges.append([i + 1, i])
        return edges
