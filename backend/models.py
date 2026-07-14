from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import datetime
from database import Base

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    total_rows = Column(Integer)
    total_columns = Column(Integer)
    time_span = Column(String)
    sampling_frequency = Column(String)
    missing_values = Column(Integer)
    duplicate_values = Column(Integer)
    detected_sensors = Column(JSON) # Store list of detected sensors
    data_quality_score = Column(Float)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)

class ConversationSession(Base):
    __tablename__ = "conversation_sessions"
    id = Column(String, primary_key=True, index=True) # UUID
    title = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    messages = relationship("Message", back_populates="session")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("conversation_sessions.id"))
    role = Column(String) # user or assistant
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    graphs = Column(JSON, nullable=True) # Any generated graphs data
    
    session = relationship("ConversationSession", back_populates="messages")

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, unique=True, index=True)
    is_active = Column(Integer, default=0) # 1 for active, 0 for inactive
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    training_time = Column(Float)
    accuracy = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    plot_data = Column(JSON, nullable=True) # Downsampled actuals vs predictions
    feature_importances = Column(JSON, nullable=True) # Feature importance list
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
