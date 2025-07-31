"""
End-to-end tests with mocked LLM and tool outputs
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import json

from app.graph import ResearchBriefGraph
from app.schemas import GraphState, FinalBrief, BriefRequest
from app.main import app
from httpx import AsyncClient, ASGITransport


class TestE2EWorkflow:
    """End-to-end workflow tests with mocked components."""
    
    @pytest.fixture
    def graph(self):
        """Create graph instance for testing."""
        return ResearchBriefGraph()
    
    @pytest.fixture
    def mock_search_results(self):
        """Mock search results."""
        return [
            {
                "search_result": {
                    "url": "https://example.com/ai1",
                    "title": "AI Fundamentals",
                    "snippet": "Introduction to artificial intelligence concepts",
                    "domain": "example.com"
                },
                "content": {
                    "success": True,
                    "content": "Artificial intelligence (AI) is a broad field of computer science focused on creating intelligent machines...",
                    "title": "AI Fundamentals",
                    "meta_description": "Comprehensive guide to AI"
                }
            },
            {
                "search_result": {
                    "url": "https://example.com/ai2", 
                    "title": "AI Applications",
                    "snippet": "Real-world applications of artificial intelligence",
                    "domain": "example.com"
                },
                "content": {
                    "success": True,
                    "content": "AI applications span across various industries including healthcare, finance, and transportation...",
                    "title": "AI Applications",
                    "meta_description": "AI use cases and applications"
                }
            }
        ]
    
    @pytest.fixture
    def mock_llm_responses(self):
        """Mock LLM responses for different stages."""
        return {
            "planning": {
                "topic": "artificial intelligence",
                "depth": 3,
                "steps": [
                    {
                        "step_id": 1,
                        "title": "AI Fundamentals Research",
                        "description": "Research basic AI concepts and definitions",
                        "priority": 5,
                        "estimated_time": 30,
                        "keywords": ["AI", "machine learning", "deep learning"]
                    },
                    {
                        "step_id": 2,
                        "title": "AI Applications Analysis",
                        "description": "Analyze current and potential AI applications",
                        "priority": 4,
                        "estimated_time": 25,
                        "keywords": ["applications", "use cases", "industry"]
                    }
                ],
                "total_estimated_time": 55,
                "focus_areas": ["AI basics", "applications", "technology"]
            },
            "summarization": {
                "summary": "Comprehensive overview of AI fundamentals and key concepts",
                "key_points": [
                    "AI involves creating intelligent machines",
                    "Machine learning is a subset of AI",
                    "Applications span multiple industries"
                ],
                "relevance_score": 0.9,
                "credibility_score": 0.8
            },
            "synthesis": {
                "summary": "Artificial Intelligence (AI) represents a transformative field in computer science focused on creating intelligent machines capable of performing tasks that typically require human intelligence. This comprehensive analysis explores AI fundamentals, current applications, and future implications across various industries.",
                "key_findings": [
                    "AI encompasses machine learning, deep learning, and neural networks as core technologies",
                    "Current applications include healthcare diagnostics, autonomous vehicles, and financial fraud detection",
                    "Future AI development focuses on general artificial intelligence and ethical AI frameworks",
                    "Industry adoption of AI continues to accelerate with significant investment in R&D"
                ],
                "methodology": "This research was conducted using web search and content analysis. Multiple authoritative sources were analyzed to provide a comprehensive understanding of artificial intelligence, including academic sources, industry reports, and expert opinions.",
                "recommendations": [
                    "Organizations should develop AI strategies aligned with business objectives",
                    "Investment in AI education and training is crucial for workforce adaptation",
                    "Ethical AI guidelines should be established before implementation"
                ],
                "limitations": [
                    "Research limited to publicly available sources",
                    "Rapidly evolving field may have newer developments not captured"
                ]
            }
        }
    
    @pytest.mark.asyncio
    async def test_complete_workflow_new_query(self, graph, mock_search_results, mock_llm_responses):
        """Test complete workflow for a new (non-follow-up) query."""
        with patch('app.llm_simple.SimpleLLMManager.generate_research_plan') as mock_planning, \
             patch('app.llm_simple.SimpleLLMManager.summarize_source') as mock_summarize, \
             patch('app.llm_simple.SimpleLLMManager.synthesize_brief') as mock_synthesis, \
             patch('app.tools.ResearchSearchTool._arun') as mock_search, \
             patch('app.database.DatabaseManager.save_brief') as mock_save, \
             patch('app.database.DatabaseManager.update_user_context') as mock_update, \
             patch('uuid.uuid4') as mock_uuid:
            
            # Setup mocks
            mock_search.return_value = mock_search_results
            mock_uuid.return_value.hex = "123456789abcdef"
            
            from app.schemas import ResearchPlan, SourceSummary, FinalBrief, SourceMetadata
            
            # Mock planning response
            mock_planning.return_value = ResearchPlan(**mock_llm_responses["planning"])
            
            # Mock source summarization
            mock_summarize.return_value = SourceSummary(
                source_id="test_source_1",
                metadata=SourceMetadata(
                    title="AI Fundamentals",
                    url="https://example.com/ai1",
                    domain="example.com",
                    published_date=None,
                    source_type="web_article"
                ),
                **mock_llm_responses["summarization"]
            )
            
            # Mock synthesis response
            mock_synthesis.return_value = FinalBrief(
                brief_id="test_brief_123",
                topic="artificial intelligence",
                generated_at=datetime.utcnow(),
                sources=[],
                execution_time=30.0,
                token_usage={"planning": 100, "summarization": 200, "synthesis": 150},
                cost_estimate=0.02,
                **mock_llm_responses["synthesis"]
            )
            
            # Run the workflow
            result = await graph.run(
                topic="artificial intelligence",
                depth=3,
                user_id="test_user",
                follow_up=False
            )
            
            # Verify workflow completed successfully
            assert isinstance(result, FinalBrief)
            assert result.topic == "artificial intelligence"
            assert result.brief_id == "brief_123456789abcdef"
            assert len(result.key_findings) == 4
            assert len(result.recommendations) == 3
            
            # Verify all components were called
            mock_search.assert_called_once()
            mock_planning.assert_called_once()
            mock_summarize.assert_called()
            mock_synthesis.assert_called_once()
            mock_save.assert_called_once()
            mock_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_workflow_follow_up_query(self, graph, mock_search_results, mock_llm_responses):
        """Test complete workflow for a follow-up query with context."""
        with patch('app.llm_simple.SimpleLLMManager.generate_research_plan') as mock_planning, \
             patch('app.llm_simple.SimpleLLMManager.summarize_context') as mock_context, \
             patch('app.llm_simple.SimpleLLMManager.summarize_source') as mock_summarize, \
             patch('app.llm_simple.SimpleLLMManager.synthesize_brief') as mock_synthesis, \
             patch('app.tools.ResearchSearchTool._arun') as mock_search, \
             patch('app.database.DatabaseManager.get_user_briefs') as mock_get_briefs, \
             patch('app.database.DatabaseManager.save_brief') as mock_save, \
             patch('app.database.DatabaseManager.update_user_context') as mock_update:
            
            from app.schemas import ResearchPlan, SourceSummary, FinalBrief, SourceMetadata, ContextSummary
            
            # Mock previous briefs
            mock_get_briefs.return_value = [
                Mock(topic="artificial intelligence basics", summary="Previous AI research")
            ]
            
            # Mock context summarization
            mock_context.return_value = ContextSummary(
                user_id="test_user",
                previous_topics=["artificial intelligence basics"],
                key_themes=["AI", "machine learning"],
                preferred_depth=3,
                last_interaction=datetime.utcnow(),
                context_relevance_score=0.8
            )
            
            # Setup other mocks (same as above)
            mock_search.return_value = mock_search_results
            mock_planning.return_value = ResearchPlan(**mock_llm_responses["planning"])
            mock_summarize.return_value = SourceSummary(
                source_id="test_source_1",
                metadata=SourceMetadata(
                    title="ML Applications", 
                    url="https://example.com/ml",
                    domain="example.com",
                    published_date=None,
                    source_type="web_article"
                ),
                **mock_llm_responses["summarization"]
            )
            mock_synthesis.return_value = FinalBrief(
                brief_id="test_brief_followup_123",
                topic="machine learning applications",
                generated_at=datetime.utcnow(),
                sources=[],
                execution_time=32.0,
                token_usage={"context": 50, "planning": 100, "summarization": 200, "synthesis": 150},
                cost_estimate=0.025,
                **mock_llm_responses["synthesis"]
            )
            
            # Run follow-up workflow
            result = await graph.run(
                topic="machine learning applications",
                depth=3,
                user_id="test_user",
                follow_up=True
            )
            
            # Verify follow-up workflow
            assert isinstance(result, FinalBrief)
            assert result.topic == "machine learning applications"
            
            # Verify context was processed
            mock_get_briefs.assert_called_once_with("test_user", limit=5)
            mock_context.assert_called_once()
            
            # Verify context was passed to synthesis
            synthesis_call = mock_synthesis.call_args
            assert synthesis_call is not None
            context_arg = synthesis_call[1].get('context_summary')
            assert context_arg is not None
            assert "artificial intelligence basics" in context_arg.previous_topics


class TestAPIEndpoints:
    """Test API endpoints with mocked components."""
    
    @pytest.mark.asyncio
    async def test_generate_brief_endpoint(self):
        """Test the /brief endpoint."""
        with patch('app.graph.research_graph.run') as mock_run:
            # Mock successful brief generation
            mock_brief = FinalBrief(
                brief_id="api_test_123",
                topic="test topic",
                summary="Test summary",
                key_findings=["Finding 1"],
                methodology="Test methodology", 
                recommendations=["Rec 1"],
                limitations=["Limit 1"],
                sources=[],
                generated_at=datetime.utcnow(),
                execution_time=25.0,
                token_usage={"total": 300},
                cost_estimate=0.015
            )
            mock_run.return_value = mock_brief
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/brief", json={
                    "topic": "test topic",
                    "depth": 3,
                    "follow_up": False,
                    "user_id": "api_test_user"
                })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["brief"]["topic"] == "test topic"
            assert data["brief"]["brief_id"] == "api_test_123"
    
    @pytest.mark.asyncio
    async def test_generate_brief_endpoint_follow_up(self):
        """Test the /brief endpoint with follow-up flag."""
        with patch('app.graph.research_graph.run') as mock_run:
            mock_brief = FinalBrief(
                brief_id="api_followup_123",
                topic="follow up topic",
                summary="Follow-up summary",
                key_findings=["Finding 1"],
                methodology="Follow-up methodology",
                recommendations=["Rec 1"],
                limitations=["Limit 1"],
                sources=[],
                generated_at=datetime.utcnow(),
                execution_time=28.0,
                token_usage={"context": 50, "total": 350},
                cost_estimate=0.018
            )
            mock_run.return_value = mock_brief
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/brief", json={
                    "topic": "follow up topic",
                    "depth": 3,
                    "follow_up": True,
                    "user_id": "api_test_user"
                })
            
            assert response.status_code == 200
            data = response.json()
            assert data["brief"]["topic"] == "follow up topic"
            
            # Verify follow_up flag was passed to workflow
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["follow_up"] is True
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test the health check endpoint."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data