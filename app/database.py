"""
Database models and storage layer for the Research Brief Generator.
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

from app.config import settings
from app.schemas import FinalBrief, ContextSummary, SourceSummary

Base = declarative_base()


class BriefRecord(Base):
    """Database model for storing research briefs."""
    __tablename__ = "briefs"
    
    brief_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    topic = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    key_findings = Column(Text, nullable=False)  # JSON string
    methodology = Column(Text, nullable=False)
    sources = Column(Text, nullable=False)  # JSON string
    recommendations = Column(Text, nullable=False)  # JSON string
    limitations = Column(Text, nullable=False)  # JSON string
    generated_at = Column(DateTime, default=func.now())
    execution_time = Column(Float, nullable=False)
    token_usage = Column(Text, nullable=False)  # JSON string
    cost_estimate = Column(Float, nullable=False)


class UserContext(Base):
    """Database model for storing user context and history."""
    __tablename__ = "user_contexts"
    
    user_id = Column(String, primary_key=True)
    previous_topics = Column(Text, nullable=False)  # JSON string
    key_themes = Column(Text, nullable=False)  # JSON string
    preferred_depth = Column(Integer, default=3)
    last_interaction = Column(DateTime, default=func.now())
    context_relevance_score = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DatabaseManager:
    """Database manager for handling storage operations."""
    
    def __init__(self):
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def save_brief(self, brief: FinalBrief, user_id: str) -> None:
        """Save a research brief to the database."""
        with self.get_session() as session:
            brief_record = BriefRecord(
                brief_id=brief.brief_id,
                user_id=user_id,
                topic=brief.topic,
                summary=brief.summary,
                key_findings=json.dumps(brief.key_findings),
                methodology=brief.methodology,
                sources=json.dumps([source.model_dump(mode='json') for source in brief.sources]),
                recommendations=json.dumps(brief.recommendations),
                limitations=json.dumps(brief.limitations),
                generated_at=brief.generated_at,
                execution_time=brief.execution_time,
                token_usage=json.dumps(brief.token_usage),
                cost_estimate=brief.cost_estimate
            )
            session.add(brief_record)
            session.commit()
    
    def get_brief(self, brief_id: str) -> Optional[FinalBrief]:
        """Get a specific brief by ID."""
        with self.get_session() as session:
            record = session.query(BriefRecord).filter_by(brief_id=brief_id).first()
            if not record:
                return None
            
            return FinalBrief(
                brief_id=record.brief_id,
                topic=record.topic,
                summary=record.summary,
                key_findings=json.loads(record.key_findings),
                methodology=record.methodology,
                sources=[SourceSummary.model_validate(source) for source in json.loads(record.sources)],
                recommendations=json.loads(record.recommendations),
                limitations=json.loads(record.limitations),
                generated_at=record.generated_at,
                execution_time=record.execution_time,
                token_usage=json.loads(record.token_usage),
                cost_estimate=record.cost_estimate
            )
    
    def get_user_briefs(self, user_id: str, limit: int = 10) -> List[FinalBrief]:
        """Get recent briefs for a user."""
        with self.get_session() as session:
            records = session.query(BriefRecord)\
                .filter(BriefRecord.user_id == user_id)\
                .order_by(BriefRecord.generated_at.desc())\
                .limit(limit)\
                .all()
            
            briefs = []
            for record in records:
                brief = FinalBrief(
                    brief_id=record.brief_id,
                    topic=record.topic,
                    summary=record.summary,
                    key_findings=json.loads(record.key_findings),
                    methodology=record.methodology,
                    sources=[SourceSummary.model_validate(source) for source in json.loads(record.sources)],
                    recommendations=json.loads(record.recommendations),
                    limitations=json.loads(record.limitations),
                    generated_at=record.generated_at,
                    execution_time=record.execution_time,
                    token_usage=json.loads(record.token_usage),
                    cost_estimate=record.cost_estimate
                )
                briefs.append(brief)
            
            return briefs
    
    def save_user_context(self, context: ContextSummary) -> None:
        """Save or update user context."""
        with self.get_session() as session:
            existing = session.query(UserContext).filter(UserContext.user_id == context.user_id).first()
            
            if existing:
                existing.previous_topics = json.dumps(context.previous_topics)
                existing.key_themes = json.dumps(context.key_themes)
                existing.preferred_depth = context.preferred_depth
                existing.last_interaction = context.last_interaction or datetime.utcnow()
                existing.context_relevance_score = context.context_relevance_score
            else:
                new_context = UserContext(
                    user_id=context.user_id,
                    previous_topics=json.dumps(context.previous_topics),
                    key_themes=json.dumps(context.key_themes),
                    preferred_depth=context.preferred_depth,
                    last_interaction=context.last_interaction or datetime.utcnow(),
                    context_relevance_score=context.context_relevance_score
                )
                session.add(new_context)
            
            session.commit()
    
    def get_user_context(self, user_id: str) -> Optional[ContextSummary]:
        """Get user context from database."""
        with self.get_session() as session:
            record = session.query(UserContext).filter(UserContext.user_id == user_id).first()
            
            if record:
                return ContextSummary(
                    user_id=record.user_id,
                    previous_topics=json.loads(record.previous_topics),
                    key_themes=json.loads(record.key_themes),
                    preferred_depth=record.preferred_depth,
                    last_interaction=record.last_interaction,
                    context_relevance_score=record.context_relevance_score
                )
            
            return None
    
    def update_user_context(self, user_id: str, topic: str, depth: int) -> None:
        """Update user context with new interaction."""
        with self.get_session() as session:
            record = session.query(UserContext).filter(UserContext.user_id == user_id).first()
            
            if record:
                previous_topics = json.loads(record.previous_topics)
                if topic not in previous_topics:
                    previous_topics.append(topic)
                
                record.previous_topics = json.dumps(previous_topics[-10:])  # Keep last 10
                record.preferred_depth = depth
                record.last_interaction = datetime.utcnow()
            else:
                new_context = UserContext(
                    user_id=user_id,
                    previous_topics=json.dumps([topic]),
                    key_themes=json.dumps([]),
                    preferred_depth=depth,
                    last_interaction=datetime.utcnow(),
                    context_relevance_score=0.0
                )
                session.add(new_context)
            
            session.commit()


# Global database manager instance
db_manager = DatabaseManager() 