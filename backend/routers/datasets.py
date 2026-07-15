from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import models, schemas
from database import get_db, SessionLocal
from services.dataset_service import DatasetService
from services.ml_service import MLService
import traceback
import pandas as pd
import io

router = APIRouter()

def run_self_learning(file_bytes: bytes, dataset_id: int):
    # Need a fresh DB session for the background task
    db = SessionLocal()
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
        MLService.evaluate_and_promote(db, df, dataset_id)
        
        dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
        if dataset:
            dataset.status = "COMPLETED"
            db.commit()
    except Exception as e:
        err_msg = str(e)
        print(f"Error in background learning loop for dataset {dataset_id}: {err_msg}")
        dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
        if dataset:
            dataset.status = "FAILED"
            dataset.error_message = err_msg
            db.commit()
    finally:
        db.close()

@router.post("/upload", response_model=schemas.DatasetResponse)
async def upload_dataset(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    try:
        contents = await file.read()
        stats = DatasetService.process_csv(contents, file.filename)
        
        # Save to DB
        db_dataset = models.Dataset(**stats)
        db.add(db_dataset)
        db.commit()
        db.refresh(db_dataset)
        
        # Trigger background learning
        background_tasks.add_task(run_self_learning, contents, db_dataset.id)
        
        return db_dataset
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing dataset: {str(e)}")

@router.get("/", response_model=list[schemas.DatasetResponse])
def get_datasets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Dataset).offset(skip).limit(limit).all()

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    db.query(models.ModelVersion).filter(models.ModelVersion.dataset_id == dataset_id).delete()
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    db.delete(dataset)
    db.commit()
    return {"message": "Dataset and associated model versions deleted successfully"}
