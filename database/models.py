from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base

class Model(Base):
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    path = Column(String(500), nullable=False)
    model_type = Column(String(50), nullable=False)  # local, huggingface, api
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    evaluation_records = relationship("EvaluationRecord", back_populates="model")
    excellent_records = relationship("ExcellentRecord", back_populates="model")

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text)
    path = Column(String(500))
    dataset_type = Column(String(50), default="text")  # text, multiple_choice, etc.
    size = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    evaluation_records = relationship("EvaluationRecord", back_populates="dataset")

class EvaluationTask(Base):
    __tablename__ = "evaluation_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    task_type = Column(String(50), default="text_generation")  # text_generation, multiple_choice, etc.
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    priority = Column(Integer, default=0)
    config = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # 关系
    model = relationship("Model")
    dataset = relationship("Dataset")
    evaluation_record = relationship("EvaluationRecord", back_populates="task", uselist=False)

class EvaluationRecord(Base):
    __tablename__ = "evaluation_records"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("evaluation_tasks.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    
    # 测评结果
    score = Column(Float)
    metrics = Column(JSON)  # 存储详细指标
    results = Column(JSON)  # 存储详细结果
    execution_time = Column(Float)  # 执行时间（秒）
    memory_usage = Column(Float)  # 内存使用量（MB）
    
    # 兼容字段
    model_type = Column(String(50), default="local")  # local, api
    accuracy = Column(Float)  # 兼容字段
    loss = Column(Float)      # 兼容字段
    perplexity = Column(Float)  # 兼容字段
    custom_metrics = Column(JSON)  # 兼容字段
    config = Column(JSON)  # 兼容字段
    evaluation_time = Column(Float)  # 兼容字段
    
    # 状态
    status = Column(String(20), default="completed")  # completed, failed
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    task = relationship("EvaluationTask", back_populates="evaluation_record")
    model = relationship("Model", back_populates="evaluation_records")
    dataset = relationship("Dataset", back_populates="evaluation_records")

class ExcellentRecord(Base):
    __tablename__ = "excellent_records"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    record_id = Column(Integer, ForeignKey("evaluation_records.id"), nullable=False)
    reason = Column(Text)  # 选择为优秀记录的原因
    is_excellent = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    model = relationship("Model", back_populates="excellent_records")
    record = relationship("EvaluationRecord")

class GPUSnapshot(Base):
    __tablename__ = "gpu_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    gpu_info = Column(JSON)  # GPU 信息快照
    timestamp = Column(DateTime(timezone=True), server_default=func.now())