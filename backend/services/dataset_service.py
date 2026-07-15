import pandas as pd
import io
import datetime
from typing import Dict, Any, List

class DatasetService:
    """
    Service responsible for processing raw CSV datasets.
    Handles dynamic sensor detection, timestamp alignment, and dataset statistics.
    """
    
    # Common aliases for weather parameters
    SENSOR_ALIASES = {
        "temperature": ["temp", "t", "temperature", "temp_c", "temp_f"],
        "humidity": ["hum", "h", "humidity", "rh"],
        "pressure": ["press", "p", "pressure", "slp"],
        "wind_speed": ["ws", "windspeed", "wind_speed", "wind"],
        "wind_direction": ["wd", "winddir", "wind_direction"],
        "precipitation": ["precip", "rain", "rainfall", "snow", "snowfall"],
        "pm25": ["pm2.5", "pm25"],
        "pm10": ["pm10"],
        "aqi": ["aqi", "air_quality"],
        "co2": ["co2", "carbon_dioxide"]
    }

    @staticmethod
    def detect_sensors(columns: List[str]) -> List[str]:
        """Dynamically detects weather parameters based on aliases."""
        detected = []
        for col in columns:
            col_lower = col.lower().strip()
            for sensor, aliases in DatasetService.SENSOR_ALIASES.items():
                if any(alias in col_lower for alias in aliases):
                    if sensor not in detected:
                        detected.append(sensor)
            # If not matching any alias, keep it as a generic sensor
            if col_lower not in [alias for aliases in DatasetService.SENSOR_ALIASES.values() for alias in aliases]:
                 detected.append(col_lower)
        return list(set(detected))

    @staticmethod
    def process_csv(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Reads CSV, analyzes statistics, and detects features."""
        df = pd.read_csv(io.BytesIO(file_bytes))
        
        # Calculate stats
        total_rows = len(df)
        total_columns = len(df.columns)
        missing_values = int(df.isnull().sum().sum())
        duplicate_values = int(df.duplicated().sum())
        
        # Calculate basic quality score (0-100)
        quality_score = max(0.0, 100.0 - ((missing_values / (total_rows * total_columns)) * 100) - ((duplicate_values / total_rows) * 100))
        
        # Detect sensors
        detected_sensors = DatasetService.detect_sensors(list(df.columns))
        
        # Try to find a datetime column for time span
        time_span = "Unknown"
        sampling_frequency = "Unknown"
        
        # A simple heuristic for datetime columns
        datetime_cols = []
        for col in df.columns:
            if 'time' in col.lower() or 'date' in col.lower():
                datetime_cols.append(col)
                
        if datetime_cols:
            try:
                df[datetime_cols[0]] = pd.to_datetime(df[datetime_cols[0]], format='mixed', errors='coerce')
                valid_dates = df[datetime_cols[0]].dropna()
                if not valid_dates.empty:
                    min_time = valid_dates.min()
                    max_time = valid_dates.max()
                    time_span = f"{min_time} to {max_time}"
                    
                    # Estimate frequency
                    if len(valid_dates) > 1:
                        freq = valid_dates.diff().mode()
                        if not freq.empty:
                            sampling_frequency = str(freq[0])
            except Exception:
                pass # If parsing fails, just leave it as Unknown

        return {
            "filename": filename,
            "total_rows": total_rows,
            "total_columns": total_columns,
            "time_span": time_span,
            "sampling_frequency": sampling_frequency,
            "missing_values": missing_values,
            "duplicate_values": duplicate_values,
            "detected_sensors": detected_sensors,
            "data_quality_score": round(quality_score, 2)
        }
