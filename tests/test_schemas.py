"""
Unit tests for Pydantic schemas
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas import (
    ResearchStep, ResearchPlan, SourceMetadata, SourceSummary,
    ContextSummary, FinalBrief, BriefRequest, BriefResponse,
    ErrorResponse, GraphState
)


class TestResearchStep:
    def test_valid_research_step(self):
        """Test creating a valid research step."""
        step = ResearchStep(
            step_id=1,
            title="Literature Review",
            description="Review existing research on the topic",
            priority=5,
            estimated_time=30,
            keywords=["literature", "review", "research"]
        )
        assert step.step_id == 1
        assert step.title == "Literature Review"
        assert step.priority == 5
        assert step.estimated_time == 30
        assert len(step.keywords) == 3

    def test_invalid_priority(self):
        """Test that priority must be between 1 and 5."""
        with pytest.raises(ValidationError):
            ResearchStep(
                step_id=1,
                title="Test Step",
                description="Test description",
                priority=6,  # Invalid priority
                estimated_time=30
            )

    def test_invalid_estimated_time(self):
        """Test that estimated time must be positive."""
        with pytest.raises(ValidationError):
            ResearchStep(
                step_id=1,
                title="Test Step",
                description="Test description",
                priority=3,
                estimated_time=0  # Invalid time
            )


class TestResearchPlan:
    def test_valid_research_plan(self):
        """Test creating a valid research plan."""
        steps = [
            ResearchStep(
                step_id=1,
                title="Step 1",
                description="First step",
                priority=5,
                estimated_time=30
            ),
            ResearchStep(
                step_id=2,
                title="Step 2",
                description="Second step",
                priority=3,
                estimated_time=20
            )
        ]
        
        plan = ResearchPlan(
            topic="Test Topic",
            depth=3,
            steps=steps,
            focus_areas=["area1", "area2"]
        )
        
        assert plan.topic == "Test Topic"
        assert plan.depth == 3
        assert len(plan.steps) == 2
        assert plan.total_estimated_time == 50  # 30 + 20
        assert len(plan.focus_areas) == 2

    def test_invalid_depth(self):
        """Test that depth must be between 1 and 5."""
        with pytest.raises(ValidationError):
            ResearchPlan(
                topic="Test Topic",
                depth=6,  # Invalid depth
                steps=[],
                focus_areas=[]
            )


class TestSourceSummary:
    def test_valid_source_summary(self):
        """Test creating a valid source summary."""
        metadata = SourceMetadata(
            url="https://example.com",
            title="Example Article",
            author="John Doe",
            publication_date=datetime(2023, 1, 1),
            domain="example.com",
            source_type="web_article"
        )
        
        summary = SourceSummary(
            source_id="src_123",
            metadata=metadata,
            summary="This is a summary of the source content.",
            key_points=["Point 1", "Point 2"],
            relevance_score=0.85,
            credibility_score=0.7,
            extraction_method="web_scraping"
        )
        
        assert summary.source_id == "src_123"
        assert str(summary.metadata.url) == "https://example.com/"  # HttpUrl adds trailing slash
        assert summary.relevance_score == 0.85
        assert len(summary.key_points) == 2

    def test_invalid_relevance_score(self):
        """Test that relevance score must be between 0 and 10."""
        metadata = SourceMetadata(
            url="https://example.com",
            title="Example Article",
            author="John Doe",
            publication_date=datetime(2023, 1, 1),
            domain="example.com",
            source_type="web_article"
        )
        
        with pytest.raises(ValidationError):
            SourceSummary(
                source_id="src_123",
                metadata=metadata,
                summary="Test summary",
                key_points=[],
                relevance_score=11.0,  # Invalid score
                credibility_score=7.0,
                extraction_method="web_scraping"
            )


class TestContextSummary:
    def test_valid_context_summary(self):
        """Test creating a valid context summary."""
        context = ContextSummary(
            user_id="user_123",
            previous_topics=["Topic 1", "Topic 2"],
            key_themes=["Theme 1", "Theme 2"],
            preferred_depth=3,
            context_relevance_score=0.8
        )
        
        assert context.user_id == "user_123"
        assert len(context.previous_topics) == 2
        assert context.preferred_depth == 3
        assert context.context_relevance_score == 0.8


class TestFinalBrief:
    def test_valid_final_brief(self):
        """Test creating a valid final brief."""
        metadata = SourceMetadata(
            url="https://example.com",
            title="Example Source",
            author="John Doe",
            publication_date=datetime(2023, 1, 1),
            domain="example.com",
            source_type="web_article"
        )
        
        source_summary = SourceSummary(
            source_id="src_123",
            metadata=metadata,
            summary="Source summary",
            key_points=["Point 1"],
            relevance_score=0.8,
            credibility_score=0.7,
            extraction_method="web_scraping"
        )
        
        brief = FinalBrief(
            brief_id="brief_123",
            topic="Test Topic",
            summary="This is a comprehensive summary of the research.",
            key_findings=["Finding 1", "Finding 2"],
            methodology="This research used a systematic approach.",
            sources=[source_summary],
            recommendations=["Recommendation 1", "Recommendation 2"],
            limitations=["This research has some limitations."],
            generated_at=datetime.now(),
            execution_time=120.5,
            token_usage={"input": 1000, "output": 500},
            cost_estimate=0.05
        )
        
        assert brief.brief_id == "brief_123"
        assert brief.topic == "Test Topic"
        assert len(brief.key_findings) == 2
        assert len(brief.sources) == 1
        assert brief.execution_time == 120.5
        assert brief.cost_estimate == 0.05


class TestBriefRequest:
    def test_valid_brief_request(self):
        """Test creating a valid brief request."""
        request = BriefRequest(
            topic="Test Topic",
            depth=3,
            follow_up=False,
            user_id="user_123"
        )
        
        assert request.topic == "Test Topic"
        assert request.depth == 3
        assert request.follow_up is False
        assert request.user_id == "user_123"


class TestBriefResponse:
    def test_valid_brief_response(self):
        """Test creating a valid brief response."""
        metadata = SourceMetadata(
            url="https://example.com",
            title="Example Source",
            author="John Doe",
            publication_date=datetime(2023, 1, 1),
            domain="example.com",
            source_type="web_article"
        )
        
        source_summary = SourceSummary(
            source_id="src_123",
            metadata=metadata,
            summary="Source summary",
            key_points=["Point 1"],
            relevance_score=0.8,
            credibility_score=0.7,
            extraction_method="web_scraping"
        )
        
        brief = FinalBrief(
            brief_id="brief_123",
            topic="Test Topic",
            summary="Test summary",
            key_findings=["Finding 1"],
            methodology="Test methodology",
            sources=[source_summary],
            recommendations=["Rec 1"],
            limitations=["Test limitations"],
            generated_at=datetime.now(),
            execution_time=60.0,
            token_usage={"input": 500, "output": 250},
            cost_estimate=0.025
        )
        
        response = BriefResponse(
            brief=brief,
            status="success",
            message="Brief generated successfully"
        )
        
        assert response.brief.brief_id == "brief_123"
        assert response.status == "success"
        assert response.message == "Brief generated successfully"


class TestGraphState:
    def test_valid_graph_state(self):
        """Test creating a valid graph state."""
        state = GraphState(
            topic="Test Topic",
            depth=3,
            user_id="user_123",
            follow_up=False,
            current_step="planning"
        )
        
        assert state.topic == "Test Topic"
        assert state.depth == 3
        assert state.user_id == "user_123"
        assert state.follow_up is False
        assert state.current_step == "planning"
        assert len(state.search_results) == 0
        assert len(state.source_summaries) == 0
        assert len(state.errors) == 0
        assert len(state.token_usage) == 0 