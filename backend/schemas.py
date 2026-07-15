from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class DatasetBase(BaseModel):
    filename: str
    total_rows: int
    total_columns: int
    time_span: str
    sampling_frequency: str
    missing_values: int
    duplicate_values: int
    detected_sensors: List[str]
    data_quality_score: float
    status: Optional[str] = "PROCESSING"
    error_message: Optional[str] = None

class DatasetCreate(DatasetBase):
    pass

class DatasetResponse(DatasetBase):
    id: int
    upload_date: datetime

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    role: str
    content: str
    graphs: Optional[Dict[str, Any]] = None

class MessageCreate(MessageBase):
    is_online: bool = False
    system_mode: str = "Prime"

class MessageResponse(MessageBase):
    id: int
    session_id: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ConversationSessionBase(BaseModel):
    title: str

class ConversationSessionCreate(ConversationSessionBase):
    id: str

class ConversationSessionResponse(ConversationSessionBase):
    id: str
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class ModelVersionBase(BaseModel):
    version: str
    is_active: int
    dataset_id: int
    training_time: float
    accuracy: Optional[float] = None
    rmse: Optional[float] = None

class ModelVersionResponse(ModelVersionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
