"""
Dataset Manager — Full dataset lifecycle: validate, register, track status, archive/delete.
"""
import os
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
import models
from utils.logger import logger


class DatasetManager:

    @staticmethod
    def validate(filepath: str) -> Dict[str, Any]:
        """Validate file exists, is a CSV, and has readable content."""
        if not os.path.exists(filepath):
            return {"valid": False, "reason": "File not found"}
        if not filepath.lower().endswith(".csv"):
            return {"valid": False, "reason": "File must be a CSV"}
        try:
            import pandas as pd
            df = pd.read_csv(filepath, nrows=5)
            if df.empty:
                return {"valid": False, "reason": "CSV file is empty"}
            return {"valid": True, "columns": list(df.columns), "sample_rows": len(df)}
        except Exception as e:
            return {"valid": False, "reason": str(e)}

    @staticmethod
    def register(db: Session, dataset_data: Dict[str, Any]) -> models.Dataset:
        """Create a new Dataset record."""
        ds = models.Dataset(**dataset_data)
        db.add(ds)
        db.commit()
        db.refresh(ds)
        logger.info(f"Registered dataset: {ds.filename} (id={ds.id})")
        return ds

    @staticmethod
    def update_status(db: Session, dataset_id: int, status: str, error: Optional[str] = None) -> None:
        ds = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
        if ds:
            ds.status = status
            ds.error_message = error
            db.commit()
            logger.info(f"Dataset {dataset_id} status → {status}")

    @staticmethod
    def list_all(db: Session) -> List[models.Dataset]:
        return db.query(models.Dataset).order_by(models.Dataset.upload_date.desc()).all()

    @staticmethod
    def get_by_id(db: Session, dataset_id: int) -> Optional[models.Dataset]:
        return db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()

    @staticmethod
    def delete(db: Session, dataset_id: int) -> bool:
        ds = DatasetManager.get_by_id(db, dataset_id)
        if not ds:
            return False
        db.query(models.ModelVersion).filter(models.ModelVersion.dataset_id == dataset_id).delete()
        db.delete(ds)
        db.commit()
        logger.info(f"Deleted dataset {dataset_id} and related model versions.")
        return True

    @staticmethod
    def get_active_dataset(db: Session) -> Optional[models.Dataset]:
        """Returns the dataset linked to the currently active model."""
        active = db.query(models.ModelVersion).filter(models.ModelVersion.is_active == 1).first()
        if active:
            return DatasetManager.get_by_id(db, active.dataset_id)
        return db.query(models.Dataset).order_by(models.Dataset.upload_date.desc()).first()
