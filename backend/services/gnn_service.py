"""
GNN Service — Promoted from ml_service.py
Full spatial weather prediction using PyTorch Geometric Graph Neural Network.
"""
from typing import Any, Dict, List
import torch
import torch.nn.functional as F

try:
    from torch_geometric.nn import GCNConv
    from torch_geometric.data import Data
    TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    TORCH_GEOMETRIC_AVAILABLE = False


class SpatialWeatherGNN(torch.nn.Module):
    """3-layer GCN for multi-node spatial weather prediction."""
    def __init__(self, num_node_features: int):
        super().__init__()
        if TORCH_GEOMETRIC_AVAILABLE:
            self.conv1 = GCNConv(num_node_features, 32)
            self.conv2 = GCNConv(32, 16)
            self.conv3 = GCNConv(16, 1)

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=0.1, training=self.training)
        x = F.relu(self.conv2(x, edge_index))
        x = self.conv3(x, edge_index)
        return x


class GNNService:
    """High-level GNN inference service."""

    @staticmethod
    def predict(nodes: List[List[float]], edges: List[List[int]]) -> Dict[str, Any]:
        """
        Run a GCN forward pass on sensor node data.
        nodes: [[temperature, wind_speed, humidity], ...]
        edges: [[src, dst], ...]
        """
        if not TORCH_GEOMETRIC_AVAILABLE:
            return {"status": "error", "message": "torch_geometric not installed."}
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
