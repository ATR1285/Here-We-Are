import enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Boolean, Numeric, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class CycleStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class GoalStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    SELF_SUBMITTED = "SELF_SUBMITTED"
    MANAGER_REVIEW = "MANAGER_REVIEW"
    FINALIZED = "FINALIZED"

class PerformanceCycle(Base):
    __tablename__ = "performance_cycles"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    status = Column(Enum(CycleStatus), default=CycleStatus.DRAFT, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PerformanceGoal(Base):
    __tablename__ = "performance_goals"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False, index=True)
    cycle_id = Column(String, ForeignKey("performance_cycles.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_value = Column(String, nullable=True)
    measurement_unit = Column(String, nullable=True)
    progress_value = Column(Numeric(5, 2), default=0.00)
    weight = Column(Numeric(5, 2), default=0.00)
    status = Column(Enum(GoalStatus), default=GoalStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    employee = relationship("Employee")
    cycle = relationship("PerformanceCycle")

class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False, index=True)
    cycle_id = Column(String, ForeignKey("performance_cycles.id"), nullable=False, index=True)
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    self_rating = Column(Integer, nullable=True)
    manager_rating = Column(Integer, nullable=True)
    final_rating = Column(Numeric(3, 2), nullable=True)
    
    self_comments = Column(Text, nullable=True)
    manager_comments = Column(Text, nullable=True)
    
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    employee = relationship("Employee")
    cycle = relationship("PerformanceCycle")
    reviewer = relationship("User")
    history = relationship("PerformanceReviewHistory", back_populates="review")

class PerformanceReviewHistory(Base):
    __tablename__ = "performance_review_history"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    review_id = Column(String, ForeignKey("performance_reviews.id"), nullable=False, index=True)
    actor_id = Column(String, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    previous_state = Column(String, nullable=True)
    new_state = Column(String, nullable=True)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    review = relationship("PerformanceReview", back_populates="history")
    actor = relationship("User")
