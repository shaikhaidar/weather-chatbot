import re
import os

filepath = r"e:\weatherBOT\backend\services\ml_service.py"
with open(filepath, "r") as f:
    code = f.read()

# 1. Add imports and remove xgboost
code = code.replace("from xgboost import XGBRegressor", """import torch
import torch.nn as nn
import torch.optim as optim
from functools import lru_cache
import hashlib""")

# 2. Inject LSTM class after imports
lstm_code = """
class WeatherLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2, bidirectional=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1) # Add sequence dimension (batch, 1, features)
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])
"""
code = code.replace("class MLService:", lstm_code + "\nclass MLService:")

# 3. Replace XGBoost training in train_baseline_model
xgb_train_code = """        model = XGBRegressor(
            n_estimators=100, 
            random_state=42,
            tree_method="hist", 
            device=device_type
        )
        model.fit(X_train, y_train)
        
        predictions = model.predict(X_test)"""

lstm_train_code = """        model = WeatherLSTM(input_dim=X_train.shape[1]).to(device_type)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.01)
        
        X_train_tensor = torch.tensor(X_train.values, dtype=torch.float32).to(device_type)
        y_train_tensor = torch.tensor(y_train.values, dtype=torch.float32).view(-1, 1).to(device_type)
        X_test_tensor = torch.tensor(X_test.values, dtype=torch.float32).to(device_type)
        
        model.train()
        for epoch in range(50):
            optimizer.zero_grad()
            outputs = model(X_train_tensor)
            loss = criterion(outputs, y_train_tensor)
            loss.backward()
            optimizer.step()
            
        model.eval()
        with torch.no_grad():
            predictions = model(X_test_tensor).cpu().numpy().flatten()
            
        # Mock feature importances for LSTM (absolute weight sums of first layer)
        with torch.no_grad():
            w = model.lstm.weight_ih_l0.cpu().numpy()
            imp = np.abs(w).sum(axis=0)
            imp = imp / np.sum(imp)
            model.feature_importances_ = imp"""
            
code = code.replace(xgb_train_code, lstm_train_code)

# 4. Add Caching to predict_weather_for_date (using a wrapper to handle DataFrame hashing)
wrapper_code = """    @staticmethod
    def predict_weather_for_date(df: pd.DataFrame, day: int, month: int) -> Dict[str, Any]:
        df_hash = hashlib.md5(pd.util.hash_pandas_object(df, index=True).values).hexdigest()
        return MLService._predict_cached(df_hash, df, day, month)

    @staticmethod
    @lru_cache(maxsize=32)
    def _predict_cached(df_hash: str, df: pd.DataFrame, day: int, month: int) -> Dict[str, Any]:"""
    
code = code.replace("    @staticmethod\n    def predict_weather_for_date(df: pd.DataFrame, day: int, month: int) -> Dict[str, Any]:", wrapper_code)

# 5. Replace XGBoost in predict_weather_for_date with LSTM
xgb_predict_code = """                # Latency Optimization: Reduce n_estimators to 25 and max_depth to 3 for instant training
                reg = XGBRegressor(n_estimators=25, max_depth=3, random_state=42, tree_method="hist", device=device_type)
                reg.fit(X_mat, y_mat)
                pred_val = float(reg.predict(target_X)[0])"""
                
lstm_predict_code = """                reg = WeatherLSTM(input_dim=X_mat.shape[1]).to(device_type)
                opt = optim.Adam(reg.parameters(), lr=0.01)
                crit = nn.MSELoss()
                X_t = torch.tensor(X_mat.values, dtype=torch.float32).to(device_type)
                y_t = torch.tensor(y_mat.values, dtype=torch.float32).view(-1, 1).to(device_type)
                
                reg.train()
                for _ in range(30):
                    opt.zero_grad()
                    loss = crit(reg(X_t), y_t)
                    loss.backward()
                    opt.step()
                    
                reg.eval()
                with torch.no_grad():
                    tx = torch.tensor(target_X.values, dtype=torch.float32).to(device_type)
                    pred_val = float(reg(tx).cpu().item())"""

code = code.replace(xgb_predict_code, lstm_predict_code)

# 6. Remove the duplicated PyG code at the bottom of the file
import re
code = re.sub(r'import torch\nimport torch\.nn\.functional as F\n\ntry:\n    from torch_geometric.*?return torch\.zeros\(\(data\.x\.size\(0\), 1\)\).*?return \{\n\s+"status": "error",\n\s+"message": str\(e\)\n\s+\}', '', code, flags=re.DOTALL)


with open(filepath, "w") as f:
    f.write(code)
print("Successfully refactored ml_service.py!")
