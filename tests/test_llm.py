"""
Unit tests for LLM managers
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.llm import LLMManager
from app.llm_simple import SimpleLLMManager
from app.schemas import ResearchPlan, SourceSummary, ContextSummary, FinalBrief, SourceMetadata


class TestLLMManager:
    """Test the main LLM manager."""
    
    @pytest.fixture
    def llm_manager(self):
        """Create LLM manager instance for testing."""
        return LLMManager()
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI response object."""
        mock_response = Mock()
        mock_response.content = '{"topic": "test", "depth": 3, "steps": [], "focus_areas": []}'
        mock_response.usage_metadata = {"total_tokens": 100, "input_tokens": 50, "output_tokens": 50}
        return mock_response
    
    @pytest.mark.asyncio
    async def test_generate_research_plan(self, llm_manager, mock_openai_response):
        """Test research plan generation."""
        with patch('app.llm.ChatOpenAI.ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_openai_response
            
            token_usage = {}
            result = await llm_manager.generate_research_plan(
                topic="test topic",
                depth=3,
                token_usage=token_usage
            )
            
            assert isinstance(result, ResearchPlan)
            assert result.topic == "test"
            assert result.depth == 3
            assert token_usage["planning"] == 100
    
    @pytest.mark.asyncio
    async def test_summarize_context(self, llm_manager, mock_openai_response):
        """Test context summarization."""
        with patch('app.llm.ChatOpenAI.ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_response = Mock()
            mock_response.content = '{"user_id": "test", "previous_topics": [], "key_themes": [], "preferred_depth": 3, "context_relevance_score": 0.8}'
            mock_response.usage_metadata = {"total_tokens": 80}
            mock_invoke.return_value = mock_response
            
            token_usage = {}
            result = await llm_manager.summarize_context(
                user_id="test",
                previous_briefs=[],
                current_topic="test topic",
                token_usage=token_usage
            )
            
            assert isinstance(result, ContextSummary)
            assert result.user_id == "test"
            assert token_usage["context"] == 80


class TestSimpleLLMManager:
    """Test the simplified LLM manager."""
    
    @pytest.fixture
    def simple_llm_manager(self):
        """Create SimpleLLMManager instance for testing."""
        return SimpleLLMManager()
    
    @pytest.fixture
    def mock_research_plan_response(self):
        """Mock research plan JSON response."""
        return {
            "topic": "artificial intelligence",
            "depth": 3,
            "steps": [
                {
                    "step_id": 1,
                    "title": "AI fundamentals",
                    "description": "Research AI basics",
                    "priority": 5,
                    "estimated_time": 30,
                    "keywords": ["AI", "basics"]
                }
            ],
            "total_estimated_time": 30,
            "focus_areas": ["AI", "technology"]
        }
    
    @pytest.mark.asyncio
    async def test_generate_research_plan_success(self, simple_llm_manager, mock_research_plan_response):
        """Test successful research plan generation."""
        with patch('app.llm_simple.ChatOpenAI.ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_response = Mock()
            mock_response.content = str(mock_research_plan_response).replace("'", '"')
            mock_invoke.return_value = mock_response
            
            token_usage = {}
            result = await simple_llm_manager.generate_research_plan(
                topic="artificial intelligence",
                depth=3,
                token_usage=token_usage
            )
            
            assert isinstance(result, ResearchPlan)
            assert result.topic == "artificial intelligence"
            assert result.depth == 3
            assert len(result.steps) == 1
            assert token_usage["planning"] > 0
    
    @pytest.mark.asyncio
    async def test_generate_research_plan_fallback(self, simple_llm_manager):
        """Test research plan generation with invalid JSON fallback."""
        with patch('app.llm_simple.ChatOpenAI.ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_response = Mock()
            mock_response.content = "invalid json response"
            mock_invoke.return_value = mock_response
            
            result = await simple_llm_manager.generate_research_plan(
                topic="test topic",
                depth=3
            )
            
            # Should return fallback plan
            assert isinstance(result, ResearchPlan)
            assert result.topic == "test topic"
            assert result.depth == 3
    
    @pytest.mark.asyncio
    async def test_summarize_source_with_content(self, simple_llm_manager):
        """Test source summarization with full content."""
        with patch('app.llm_simple.ChatOpenAI.ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_response = Mock()
            mock_response.content = '''{"summary": "Test summary", "key_points": ["Point 1"], "relevance_score": 0.8, "credibility_score": 0.7}'''
            mock_invoke.return_value = mock_response
            
            result = await simple_llm_manager.summarize_source(
                source_content="Long article content about AI...",
                source_url="https://example.com",
                topic="artificial intelligence"
            )
            
            assert isinstance(result, SourceSummary)
            assert result.summary == "Test summary"
            assert result.relevance_score == 0.8
    
    @pytest.mark.asyncio
    async def test_synthesize_brief_with_context(self, simple_llm_manager):
        """Test brief synthesis with user context."""
        # Create mock context
        context = ContextSummary(
            user_id="test",
            previous_topics=["machine learning"],
            key_themes=["AI", "technology"],
            preferred_depth=3,
            last_interaction=datetime.utcnow(),
            context_relevance_score=0.8
        )
        
        # Create mock research plan
        plan = ResearchPlan(
            topic="AI applications",
            depth=3,
            steps=[],
            focus_areas=["AI"]
        )
        
        with patch('app.llm_simple.ChatOpenAI.ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_response = Mock()
            mock_response.content = '''{"summary": "AI applications brief", "key_findings": ["Finding 1"], "methodology": "Web research", "recommendations": ["Rec 1"], "limitations": ["Limit 1"]}'''
            mock_invoke.return_value = mock_response
            
            result = await simple_llm_manager.synthesize_brief(
                topic="AI applications",
                source_summaries=[],
                research_plan=plan,
                context_summary=context
            )
            
            assert isinstance(result, FinalBrief)
            assert result.topic == "AI applications"
            
            # Verify context was included in the prompt
            mock_invoke.assert_called_once()
            call_args = mock_invoke.call_args[0][0]
            assert "machine learning" in call_args  # Previous topic should be in prompt
            assert "AI" in call_args  # Key theme should be in prompt