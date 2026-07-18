import sys
import os
import pandas as pd

# Add backend to path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import SessionLocal
from backend.services.dataset_service import DatasetService
from backend.services.ml_service import MLService
from backend import models

def main():
    csv_path = r"e:\weatherBOT\data\weather.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    # Read the file bytes
    with open(csv_path, "rb") as f:
        file_bytes = f.read()

    filename = "weather.csv"
    print(f"Processing {filename}...")
    
    db = SessionLocal()
    try:
        # 1. Process dataset stats
        stats = DatasetService.process_csv(file_bytes, filename)
        
        # 2. Save Dataset to DB
        db_dataset = models.Dataset(
            filename=stats["filename"],
            total_rows=stats["total_rows"],
            total_columns=stats["total_columns"],
            time_span=stats["time_span"],
            sampling_frequency=stats["sampling_frequency"],
            missing_values=stats["missing_values"],
            duplicate_values=stats["duplicate_values"],
            detected_sensors=stats["detected_sensors"],
            data_quality_score=stats["data_quality_score"],
            status="COMPLETED"
        )
        db.add(db_dataset)
        db.commit()
        db.refresh(db_dataset)
        print(f"Dataset saved to DB with ID: {db_dataset.id}")
        
        # 3. Train the model
        print("Starting ML training pipeline...")
        df = pd.read_csv(csv_path)
        MLService.evaluate_and_promote(db, df, db_dataset.id)
        print("Training complete! Model promoted successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
