"""
Unit tests for database operations
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import json

from app.database import DatabaseManager, BriefRecord, UserContext
from app.schemas import FinalBrief, ContextSummary, SourceSummary, SourceMetadata


class TestDatabaseManager:
    """Test database manager functionality."""
    
    @pytest.fixture
    def db_manager(self):
        """Create database manager for testing."""
        return DatabaseManager()
    
    @pytest.fixture
    def sample_brief(self):
        """Create sample brief for testing."""
        return FinalBrief(
            brief_id="test_brief_123",
            topic="test topic",
            summary="Test summary",
            key_findings=["Finding 1", "Finding 2"],
            methodology="Test methodology",
            recommendations=["Recommendation 1"],
            limitations=["Limitation 1"],
            sources=[],
            generated_at=datetime.utcnow(),
            execution_time=30.0,
            token_usage={"planning": 100, "synthesis": 200},
            cost_estimate=0.015
        )
    
    @pytest.fixture
    def sample_context(self):
        """Create sample context for testing."""
        return ContextSummary(
            user_id="test_user",
            previous_topics=["topic1", "topic2"],
            key_themes=["theme1", "theme2"],
            preferred_depth=3,
            last_interaction=datetime.utcnow(),
            context_relevance_score=0.8
        )
    
    def test_database_initialization(self, db_manager):
        """Test database manager initializes correctly."""
        assert db_manager.engine is not None
        assert db_manager.SessionLocal is not None
    
    @patch('app.database.DatabaseManager.get_session')
    def test_save_brief(self, mock_session, db_manager, sample_brief):
        """Test saving a brief to database."""
        mock_session_instance = Mock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        
        db_manager.save_brief(sample_brief, "test_user")
        
        # Verify session operations
        mock_session_instance.add.assert_called_once()
        mock_session_instance.commit.assert_called_once()
        
        # Verify brief record was created correctly
        call_args = mock_session_instance.add.call_args[0][0]
        assert isinstance(call_args, BriefRecord)
        assert call_args.brief_id == "test_brief_123"
        assert call_args.topic == "test topic"
        assert call_args.user_id == "test_user"
    
    @patch('app.database.DatabaseManager.get_session')
    def test_get_brief(self, mock_session, db_manager):
        """Test retrieving a brief from database."""
        # Mock database record
        mock_record = Mock()
        mock_record.brief_id = "test_brief_123"
        mock_record.topic = "test topic"
        mock_record.summary = "Test summary"
        mock_record.key_findings = '["Finding 1"]'
        mock_record.methodology = "Test methodology"
        mock_record.recommendations = '["Rec 1"]'
        mock_record.limitations = '["Limit 1"]'
        mock_record.sources = '[]'
        mock_record.generated_at = datetime.utcnow()
        mock_record.execution_time = 30.0
        mock_record.token_usage = '{"total": 300}'
        mock_record.cost_estimate = 0.015
        mock_record.user_id = "test_user"
        
        mock_session_instance = Mock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        mock_session_instance.query.return_value.filter_by.return_value.first.return_value = mock_record
        
        result = db_manager.get_brief("test_brief_123")
        
        assert isinstance(result, FinalBrief)
        assert result.brief_id == "test_brief_123"
        assert result.topic == "test topic"
    
    @patch('app.database.DatabaseManager.get_session')
    def test_get_user_briefs(self, mock_session, db_manager):
        """Test retrieving user briefs from database."""
        # Mock multiple records with all required fields
        mock_record_1 = Mock()
        mock_record_1.brief_id = "brief_1"
        mock_record_1.topic = "topic_1"
        mock_record_1.summary = "summary_1"
        mock_record_1.key_findings = '["Finding 1"]'
        mock_record_1.methodology = "methodology_1"
        mock_record_1.sources = '[]'
        mock_record_1.recommendations = '["Rec 1"]'
        mock_record_1.limitations = '["Limit 1"]'
        mock_record_1.generated_at = datetime.utcnow()
        mock_record_1.execution_time = 30.0
        mock_record_1.token_usage = '{"total": 300}'
        mock_record_1.cost_estimate = 0.015

        mock_record_2 = Mock()
        mock_record_2.brief_id = "brief_2"
        mock_record_2.topic = "topic_2"
        mock_record_2.summary = "summary_2"
        mock_record_2.key_findings = '["Finding 2"]'
        mock_record_2.methodology = "methodology_2"
        mock_record_2.sources = '[]'
        mock_record_2.recommendations = '["Rec 2"]'
        mock_record_2.limitations = '["Limit 2"]'
        mock_record_2.generated_at = datetime.utcnow()
        mock_record_2.execution_time = 25.0
        mock_record_2.token_usage = '{"total": 250}'
        mock_record_2.cost_estimate = 0.012

        mock_records = [mock_record_1, mock_record_2]
        
        mock_session_instance = Mock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        mock_session_instance.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_records
        
        result = db_manager.get_user_briefs("test_user", limit=2)
        
        assert len(result) == 2
        assert result[0].brief_id == "brief_1"
        assert result[1].brief_id == "brief_2"
    
    @patch('app.database.DatabaseManager.get_session')
    def test_save_user_context(self, mock_session, db_manager, sample_context):
        """Test saving user context to database."""
        mock_session_instance = Mock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        # Mock query to return None (no existing context)
        mock_session_instance.query.return_value.filter.return_value.first.return_value = None
        
        db_manager.save_user_context(sample_context)
        
        # Verify session operations  
        mock_session_instance.add.assert_called_once()
        mock_session_instance.commit.assert_called_once()
        
        # Verify context record was created correctly
        call_args = mock_session_instance.add.call_args[0][0]
        assert isinstance(call_args, UserContext)
        assert call_args.user_id == "test_user"
        assert call_args.preferred_depth == 3
    
    @patch('app.database.DatabaseManager.get_session')
    def test_get_user_context_exists(self, mock_session, db_manager):
        """Test retrieving existing user context."""
        # Mock database record
        mock_record = Mock()
        mock_record.user_id = "test_user"
        mock_record.previous_topics = '["topic1", "topic2"]'
        mock_record.key_themes = '["theme1", "theme2"]'
        mock_record.preferred_depth = 3
        mock_record.last_interaction = datetime.utcnow()
        mock_record.context_relevance_score = 0.8
        
        mock_session_instance = Mock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        mock_session_instance.query.return_value.filter.return_value.first.return_value = mock_record
        
        result = db_manager.get_user_context("test_user")
        
        assert isinstance(result, ContextSummary)
        assert result.user_id == "test_user"
        assert result.previous_topics == ["topic1", "topic2"]
        assert result.preferred_depth == 3
    
    @patch('app.database.DatabaseManager.get_session')
    def test_get_user_context_not_exists(self, mock_session, db_manager):
        """Test retrieving non-existent user context."""
        mock_session_instance = Mock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        mock_session_instance.query.return_value.filter.return_value.first.return_value = None
        
        result = db_manager.get_user_context("nonexistent_user")
        
        assert result is None
    
    @patch('app.database.DatabaseManager.get_session')
    def test_update_user_context_existing(self, mock_session, db_manager):
        """Test updating existing user context."""
        # Mock existing record
        mock_record = Mock()
        mock_record.previous_topics = '["old_topic"]'
        mock_record.preferred_depth = 2
        
        mock_session_instance = Mock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        mock_session_instance.query.return_value.filter.return_value.first.return_value = mock_record
        
        db_manager.update_user_context("test_user", "new_topic", 3)
        
        # Verify topic was added and depth updated
        updated_topics = json.loads(mock_record.previous_topics)
        assert "new_topic" in updated_topics
        assert mock_record.preferred_depth == 3
        mock_session_instance.commit.assert_called_once()
    
    @patch('app.database.DatabaseManager.get_session')
    def test_update_user_context_new(self, mock_session, db_manager):
        """Test creating new user context."""
        mock_session_instance = Mock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        mock_session_instance.query.return_value.filter.return_value.first.return_value = None
        
        db_manager.update_user_context("new_user", "first_topic", 3)
        
        # Verify new context was created
        mock_session_instance.add.assert_called_once()
        mock_session_instance.commit.assert_called_once()
        
        call_args = mock_session_instance.add.call_args[0][0]
        assert isinstance(call_args, UserContext)
        assert call_args.user_id == "new_user"
        assert '"first_topic"' in call_args.previous_topics