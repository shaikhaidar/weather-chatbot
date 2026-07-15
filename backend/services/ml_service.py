from typing import Any, Dict
import pandas as pd
from sklearn.model_selection import train_test_split
from redacted import RedactedRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import time
import uuid
import numpy as np
from sqlalchemy.orm import Session
import models

class MLService:
    """
    Handles machine learning training, continuous learning, and Explainable AI.
    Provides a modular interface for future Graph Neural Network (GNN) integration.
    """
    
    @staticmethod
    def train_baseline_model(df: pd.DataFrame, target_col: str = "temperature") -> Dict[str, Any]:
        """
        Trains an Redacted model for weather prediction using GPU.
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
            
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Dynamic CUDA vs CPU device detection
        import torch
        device_type = "cuda" if torch.cuda.is_available() else "cpu"
        
        model = RedactedRegressor(
            n_estimators=100, 
            random_state=42,
            tree_method="hist", 
            device=device_type
        )
        model.fit(X_train, y_train)
        
        predictions = model.predict(X_test)
        
        mse = mean_squared_error(y_test, predictions)
        rmse = float(np.sqrt(mse))
        mae = mean_absolute_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)
        
        # Explainable AI: Feature Importance
        feature_importances = [{"feature": f, "importance": float(imp)} for f, imp in zip(X.columns, model.feature_importances_)]
        feature_importances = sorted(feature_importances, key=lambda x: x["importance"], reverse=True)[:10]

        # Downsample plot data (max 50 points)
        sample_size = min(50, len(y_test))
        indices = np.random.choice(len(y_test), sample_size, replace=False)
        plot_data = {
            "actuals": [float(val) for val in y_test.iloc[indices].values],
            "predictions": [float(val) for val in predictions[indices]]
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
                active_model.is_active = 0 # Demote old
                promote = True
            else:
                print("New model is not better. Keeping old model active.")
                
        # Save new model
        db_model = models.ModelVersion(
            version=new_version,
            is_active=1 if promote else 0,
            dataset_id=dataset_id,
            training_time=result["training_time"],
            accuracy=result["metrics"]["r2"], # using r2 for regression 'accuracy'
            rmse=new_rmse,
            plot_data=result.get("plot_data"),
            feature_importances=result.get("feature_importances")
        )
        db.add(db_model)
        db.commit()
        print(f"Model {new_version} saved to DB.")

import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data

class SpatialWeatherGNN(torch.nn.Module):
    def __init__(self, num_node_features):
        super().__init__()
        self.conv1 = GCNConv(num_node_features, 16)
        self.conv2 = GCNConv(16, 1) # Predict spatial delta

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)
        return x

    @staticmethod
    def gnn_prediction(nodes: list, edges: list) -> Dict[str, Any]:
        """
        Executes a true PyTorch Geometric spatial forward pass simulating 3 weather stations.
        nodes: list of feature lists [[temp, wind, hum], ...]
        edges: list of edge tuples [[0, 1], [1, 2], ...]
        """
        try:
            x = torch.tensor(nodes, dtype=torch.float)
            edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
            
            data = Data(x=x, edge_index=edge_index)
            model = SpatialWeatherGNN(num_node_features=len(nodes[0]))
            
            # Simulated weights since we aren't training the GNN on a live DB yet
            model.eval()
            with torch.no_grad():
                out = model(data)
                
            predictions = out.squeeze().tolist()
            if not isinstance(predictions, list):
                predictions = [predictions]
                
            return {
                "status": "success",
                "spatial_predictions": predictions,
                "message": "GNN Forward Pass Completed Successfully."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
