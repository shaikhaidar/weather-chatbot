from typing import Any, Dict
import pandas as pd
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from functools import lru_cache
import hashlib
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import time
import uuid
import numpy as np
from sqlalchemy.orm import Session
import models

try:
    from torch_geometric.nn import GATConv, knn_graph
    from torch_geometric.data import Data
    TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    TORCH_GEOMETRIC_AVAILABLE = False


class TabularGAT(nn.Module):
    """
    Graph Attention Network for Tabular Data.
    Treats each row as a node. Edges are drawn using KNN based on feature similarity.
    """
    def __init__(self, in_channels, out_channels=1, hidden_channels=32):
        super().__init__()
        if TORCH_GEOMETRIC_AVAILABLE:
            self.conv1 = GATConv(in_channels, hidden_channels, heads=4, concat=False)
            self.conv2 = GATConv(hidden_channels, out_channels, heads=1, concat=False)
        else:
            # Fallback MLP when PyG is unavailable (still uses PyTorch)
            self.fc1 = nn.Linear(in_channels, hidden_channels)
            self.fc2 = nn.Linear(hidden_channels, out_channels)

    def forward(self, x, edge_index=None):
        if TORCH_GEOMETRIC_AVAILABLE and edge_index is not None:
            x = self.conv1(x, edge_index)
            x = F.elu(x)
            x = F.dropout(x, p=0.2, training=self.training)
            x = self.conv2(x, edge_index)
            return x
        else:
            x = F.elu(self.fc1(x))
            return self.fc2(x)


class MLService:
    """
    Handles machine learning training, continuous learning, and Explainable AI.
    100% GNN-based (Graph Neural Networks). Natively adapts to any generic weather dataset.
    """
    
    @staticmethod
    def train_baseline_model(df: pd.DataFrame, target_col: str = "temperature") -> Dict[str, Any]:
        """
        Trains a GAT model on a dynamically generated KNN graph of the tabular data.
        Returns evaluation metrics, feature importances, and a downsampled sample of actual vs predicted.
        """
        start_time = time.time()
        
        # Preprocessing: Clean infinite values and select numeric features
        df_numeric = df.select_dtypes(include=['number']).replace([np.inf, -np.inf], np.nan)
        
        # Intelligent target matching using temperature aliases if target_col not directly present
        if target_col not in df_numeric.columns:
            from services.dataset_service import DatasetService
            temp_aliases = DatasetService.SENSOR_ALIASES.get("temperature", [])
            matched_target = None
            for col in df_numeric.columns:
                if any(alias in col.lower() for alias in temp_aliases):
                    matched_target = col
                    break
            if matched_target:
                target_col = matched_target
            elif len(df_numeric.columns) > 0:
                target_col = df_numeric.columns[-1]
            else:
                return {"error": "No valid numeric columns found for training."}
            
        # Clean NaNs specifically from the target column before fitting
        df_numeric = df_numeric.dropna(subset=[target_col])
        if len(df_numeric) < 10:
            return {"error": "Dataset has fewer than 10 valid non-NaN target rows for training."}
            
        # Fill remaining feature NaNs with mean values
        df_numeric = df_numeric.fillna(df_numeric.mean())
            
        X = df_numeric.drop(columns=[target_col])
        y = df_numeric[target_col]
        
        if len(X) < 10:
            return {"error": "Dataset too small for training."}

        device_type = "cuda" if torch.cuda.is_available() else "cpu"
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(device_type)
        y_tensor = torch.tensor(y.values, dtype=torch.float32).view(-1, 1).to(device_type)
        
        if TORCH_GEOMETRIC_AVAILABLE:
            edge_index = knn_graph(X_tensor, k=5, loop=True)
        else:
            edge_index = None

        num_nodes = X_tensor.size(0)
        indices = np.random.permutation(num_nodes)
        split = int(0.8 * num_nodes)
        train_idx = torch.tensor(indices[:split], dtype=torch.long)
        test_idx = torch.tensor(indices[split:], dtype=torch.long)
        
        model = TabularGAT(in_channels=X_tensor.size(1), out_channels=1).to(device_type)
        optimizer = optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
        criterion = nn.MSELoss()
        
        model.train()
        for epoch in range(50):
            optimizer.zero_grad()
            out = model(X_tensor, edge_index)
            loss = criterion(out[train_idx], y_tensor[train_idx])
            loss.backward()
            optimizer.step()
            
        model.eval()
        with torch.no_grad():
            out = model(X_tensor, edge_index)
            predictions = out[test_idx].cpu().numpy().flatten()
            y_test_np = y_tensor[test_idx].cpu().numpy().flatten()
            
        if TORCH_GEOMETRIC_AVAILABLE:
            w = model.conv1.lin.weight.detach().cpu().numpy()
        else:
            w = model.fc1.weight.detach().cpu().numpy()
            
        imp = np.abs(w).sum(axis=0)
        imp = imp / (np.sum(imp) + 1e-9)
        feature_importances_ = imp
        
        mse = mean_squared_error(y_test_np, predictions)
        rmse = float(np.sqrt(mse))
        mae = mean_absolute_error(y_test_np, predictions)
        r2 = r2_score(y_test_np, predictions)
        
        # Explainable AI: Feature Importance
        feature_importances = [{"feature": f, "importance": float(i)} for f, i in zip(X.columns, feature_importances_)]
        feature_importances = sorted(feature_importances, key=lambda x: x["importance"], reverse=True)[:10]

        sample_size = min(50, len(y_test_np))
        plot_data = {
            "actuals": [float(val) for val in y_test_np[:sample_size]],
            "predictions": [float(val) for val in predictions[:sample_size]]
        }
        
        training_time = time.time() - start_time
        version = f"v1.0.0-{str(uuid.uuid4())[:8]}"
        
        return {
            "version": version,
            "metrics": {
                "rmse": float(rmse),
                "mae": float(mae),
                "r2": float(r2)
            },
            "training_time": float(training_time),
            "plot_data": plot_data,
            "feature_importances": feature_importances,
            "status": "success"
        }

    @staticmethod
    def predict_weather_for_date(df: pd.DataFrame, day: int, month: int) -> Dict[str, Any]:
        df_hash = hashlib.md5(pd.util.hash_pandas_object(df, index=True).values).hexdigest()
        return MLService._predict_cached(df_hash, df, day, month)

    @staticmethod
    @lru_cache(maxsize=32)
    def _predict_cached(df_hash: str, df: pd.DataFrame, day: int, month: int) -> Dict[str, Any]:
        """
        Dynamically builds a KNN graph and trains a multi-feature GNN transductively 
        to forecast all generic numeric weather columns.
        """
        try:
            date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
            df_work = df.copy()
            
            # Universal Adaptability: If no explicit date column exists, infer sequential daily dates
            if not date_cols:
                df_work['parsed_date'] = pd.date_range(start='1/1/2020', periods=len(df_work), freq='D')
            else:
                df_work['parsed_date'] = pd.to_datetime(df_work[date_cols[0]], format='mixed', dayfirst=True, errors='coerce')
                
            df_work = df_work.dropna(subset=['parsed_date'])

            if df_work.empty:
                return {}

            # Feature Engineering: Temporal Cyclical Features
            df_work['day_of_year'] = df_work['parsed_date'].dt.dayofyear
            df_work['month_val'] = df_work['parsed_date'].dt.month
            df_work['sin_day'] = np.sin(2 * np.pi * df_work['day_of_year'] / 365.25)
            df_work['cos_day'] = np.cos(2 * np.pi * df_work['day_of_year'] / 365.25)

            feature_cols = ['day_of_year', 'month_val', 'sin_day', 'cos_day']
            numeric_weather_cols = list(df_work.select_dtypes(include=['number']).columns)
            numeric_weather_cols = [c for c in numeric_weather_cols if c not in feature_cols]

            # Universal Adaptability: Process ALL numeric features.
            # To avoid high latency, we cap it to the top 8 most variable columns
            if len(numeric_weather_cols) > 8:
                variances = df_work[numeric_weather_cols].var().sort_values(ascending=False)
                numeric_weather_cols = list(variances.head(8).index)

            if not numeric_weather_cols:
                return {}

            import datetime
            ref_date = datetime.date(2025, month, day)
            target_doy = ref_date.timetuple().tm_yday
            sin_target = np.sin(2 * np.pi * target_doy / 365.25)
            cos_target = np.cos(2 * np.pi * target_doy / 365.25)

            target_X = pd.DataFrame([{
                'day_of_year': target_doy,
                'month_val': month,
                'sin_day': sin_target,
                'cos_day': cos_target
            }])

            forecasts = {}
            device_type = "cuda" if torch.cuda.is_available() else "cpu"
            for col in numeric_weather_cols:
                clean_series = df_work.dropna(subset=[col])
                if len(clean_series) < 10:
                    continue
                    
                X_mat = clean_series[feature_cols]
                y_mat = clean_series[col]

                X_combined = pd.concat([X_mat, target_X], ignore_index=True)
                X_tensor = torch.tensor(X_combined.values, dtype=torch.float32).to(device_type)
                y_tensor = torch.tensor(y_mat.values, dtype=torch.float32).view(-1, 1).to(device_type)
                
                if TORCH_GEOMETRIC_AVAILABLE:
                    edge_index = knn_graph(X_tensor, k=3, loop=True)
                else:
                    edge_index = None

                model = TabularGAT(in_channels=X_tensor.size(1), out_channels=1).to(device_type)
                optimizer = optim.Adam(model.parameters(), lr=0.02)
                criterion = nn.MSELoss()
                
                train_idx = torch.arange(0, len(X_mat), dtype=torch.long)
                target_idx = len(X_mat)
                
                model.train()
                for _ in range(30):
                    optimizer.zero_grad()
                    out = model(X_tensor, edge_index)
                    loss = criterion(out[train_idx], y_tensor)
                    loss.backward()
                    optimizer.step()
                    
                model.eval()
                with torch.no_grad():
                    out = model(X_tensor, edge_index)
                    pred_val = float(out[target_idx].cpu().item())
                    
                forecasts[col] = round(pred_val, 2)

            return {
                "target_date": f"{day:02d}/{month:02d}",
                "forecasted_features": forecasts,
                "status": "success"
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def evaluate_and_promote(db: Session, df: pd.DataFrame, dataset_id: int):
        """
        Self-learning loop: trains a new model, compares against the active model, and promotes if better.
        """
        print(f"Starting self-learning loop for dataset {dataset_id}...")
        result = MLService.train_baseline_model(df)
        
        if result.get("status") != "success":
            error_reason = result.get('error', 'Unknown training failure')
            print(f"Training failed: {error_reason}")
            raise RuntimeError(error_reason)
            
        new_rmse = result["metrics"]["rmse"]
        new_version = result["version"]
        
        # Fetch current active model
        active_model = db.query(models.ModelVersion).filter(models.ModelVersion.is_active == 1).first()
        
        promote = False
        if not active_model:
            print("No active model found. Promoting new model as active.")
            promote = True
        else:
            print(f"Comparing new RMSE {new_rmse:.4f} vs active RMSE {active_model.rmse:.4f}")
            if new_rmse < active_model.rmse:
                print("New model is better. Promoting.")
                active_model.is_active = 0
                promote = True
            else:
                print("New model is not better. Keeping old model active.")
                
        # Save new model
        db_model = models.ModelVersion(
            version=new_version,
            is_active=1 if promote else 0,
            dataset_id=dataset_id,
            training_time=result["training_time"],
            accuracy=result["metrics"]["r2"],
            rmse=new_rmse,
            plot_data=result.get("plot_data"),
            feature_importances=result.get("feature_importances")
        )
        db.add(db_model)
        db.commit()
        print(f"Model {new_version} saved to DB.")
