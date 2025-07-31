"""
Pytest configuration and fixtures for testing
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from app.schemas import (
    ResearchStep, ResearchPlan, SourceMetadata, SourceSummary,
    ContextSummary, FinalBrief, GraphState
)


@pytest.fixture
def sample_research_step():
    """Sample research step for testing."""
    return ResearchStep(
        step_id=1,
        title="Literature Review",
        description="Review existing research on the topic",
        priority=5,
        estimated_time=30,
        keywords=["literature", "review", "research"]
    )


@pytest.fixture
def sample_research_plan(sample_research_step):
    """Sample research plan for testing."""
    return ResearchPlan(
        topic="Test Topic",
        depth=3,
        steps=[sample_research_step],
        focus_areas=["area1", "area2"]
    )


@pytest.fixture
def sample_source_metadata():
    """Sample source metadata for testing."""
    return SourceMetadata(
        url="https://example.com",
        title="Example Article",
        author="John Doe",
        publication_date="2023-01-01",
        domain="example.com"
    )


@pytest.fixture
def sample_source_summary(sample_source_metadata):
    """Sample source summary for testing."""
    return SourceSummary(
        source_id="src_123",
        metadata=sample_source_metadata,
        summary="This is a summary of the source content.",
        key_points=["Point 1", "Point 2"],
        relevance_score=8.5,
        credibility_score=7.0,
        extraction_method="web_scraping"
    )


@pytest.fixture
def sample_context_summary():
    """Sample context summary for testing."""
    return ContextSummary(
        user_id="user_123",
        previous_topics=["Topic 1", "Topic 2"],
        key_themes=["Theme 1", "Theme 2"],
        preferred_depth=3,
        context_relevance_score=0.8
    )


@pytest.fixture
def sample_final_brief(sample_source_summary):
    """Sample final brief for testing."""
    return FinalBrief(
        brief_id="brief_123",
        topic="Test Topic",
        summary="This is a comprehensive summary of the research.",
        key_findings=["Finding 1", "Finding 2"],
        methodology="This research used a systematic approach.",
        sources=[sample_source_summary],
        recommendations=["Recommendation 1", "Recommendation 2"],
        limitations="This research has some limitations.",
        generated_at=datetime.now(),
        execution_time=120.5,
        token_usage={"input": 1000, "output": 500},
        cost_estimate=0.05
    )


@pytest.fixture
def sample_graph_state():
    """Sample graph state for testing."""
    return GraphState(
        topic="Test Topic",
        depth=3,
        user_id="user_123",
        follow_up=False,
        current_step="planning"
    )


@pytest.fixture
def mock_llm_manager():
    """Mock LLM manager for testing."""
    mock = Mock()
    mock.generate_research_plan = AsyncMock()
    mock.summarize_context = AsyncMock()
    mock.summarize_source = AsyncMock()
    mock.synthesize_brief = AsyncMock()
    return mock


@pytest.fixture
def mock_research_search_tool():
    """Mock research search tool for testing."""
    mock = Mock()
    mock._arun = AsyncMock()
    return mock


@pytest.fixture
def mock_db_manager():
    """Mock database manager for testing."""
    mock = Mock()
    mock.save_brief = Mock()
    mock.get_user_briefs = Mock()
    mock.save_user_context = Mock()
    mock.get_user_context = Mock()
    mock.update_user_context = Mock()
    return mock


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 