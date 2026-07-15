"""
Model Manager — Model registry: list versions, promote/demote, compare metrics.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
import models
from utils.logger import logger


class ModelManager:

    @staticmethod
    def list_versions(db: Session) -> List[models.ModelVersion]:
        return db.query(models.ModelVersion).order_by(models.ModelVersion.created_at.desc()).all()

    @staticmethod
    def get_active(db: Session) -> Optional[models.ModelVersion]:
        return db.query(models.ModelVersion).filter(models.ModelVersion.is_active == 1).first()

    @staticmethod
    def get_by_id(db: Session, model_id: int) -> Optional[models.ModelVersion]:
        return db.query(models.ModelVersion).filter(models.ModelVersion.id == model_id).first()

    @staticmethod
    def promote(db: Session, model_id: int) -> bool:
        """Promote a specific model version and demote all others."""
        target = ModelManager.get_by_id(db, model_id)
        if not target:
            return False
        db.query(models.ModelVersion).update({"is_active": 0})
        target.is_active = 1
        db.commit()
        logger.info(f"Promoted model {target.version} (id={model_id}) to active.")
        return True

    @staticmethod
    def demote_all(db: Session) -> None:
        db.query(models.ModelVersion).update({"is_active": 0})
        db.commit()

    @staticmethod
    def delete(db: Session, model_id: int) -> bool:
        model = ModelManager.get_by_id(db, model_id)
        if not model:
            return False
        db.delete(model)
        db.commit()
        logger.info(f"Deleted model version id={model_id}")
        return True

    @staticmethod
    def compare_versions(db: Session) -> List[Dict[str, Any]]:
        """Return all versions sorted by RMSE for easy comparison."""
        versions = db.query(models.ModelVersion).all()
        return sorted(
            [
                {
                    "id": v.id,
                    "version": v.version,
                    "rmse": v.rmse,
                    "r2": v.accuracy,
                    "training_time": v.training_time,
                    "is_active": bool(v.is_active),
                    "created_at": v.created_at.isoformat(),
                    "dataset_id": v.dataset_id,
                }
                for v in versions
            ],
            key=lambda x: (x["rmse"] or float("inf")),
        )

    @staticmethod
    def get_registry_summary(db: Session) -> Dict[str, Any]:
        versions = db.query(models.ModelVersion).all()
        active = next((v for v in versions if v.is_active), None)
        return {
            "total_versions": len(versions),
            "active_version": active.version if active else None,
            "active_rmse": active.rmse if active else None,
            "active_r2": active.accuracy if active else None,
            "best_rmse": min((v.rmse for v in versions if v.rmse), default=None),
        }
