"""
Test Gemini integration
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.llm import LLMManager
from app.config import settings


class TestGeminiIntegration:
    """Test Gemini LLM integration."""
    
    @pytest.fixture
    def mock_gemini_llm(self):
        """Mock Gemini LLM for testing."""
        mock = Mock()
        mock.ainvoke = AsyncMock()
        return mock
    
    def test_gemini_initialization(self):
        """Test that Gemini LLM is initialized correctly."""
        with patch('app.llm.ChatGoogleGenerativeAI') as mock_gemini_class:
            mock_gemini_class.return_value = Mock()
            
            # Mock settings to include Google API key
            with patch('app.config.settings.google_api_key', 'test_key'):
                with patch('app.config.settings.summarization_model', 'gemini-1.5-pro'):
                    llm_manager = LLMManager()
                    
                    # Verify Gemini LLM was created
                    mock_gemini_class.assert_called_once_with(
                        model='gemini-1.5-pro',
                        temperature=settings.temperature,
                        max_output_tokens=settings.max_tokens,
                        google_api_key='test_key'
                    )
    
    def test_gemini_fallback_to_openai(self):
        """Test that system falls back to OpenAI when Gemini is not available."""
        with patch('app.config.settings.google_api_key', None):
            llm_manager = LLMManager()
            
            # Should return OpenAI LLM for summarization when Gemini is not available
            llm = llm_manager.get_llm_for_task("summarization")
            assert llm == llm_manager.openai_llm
    
    def test_gemini_used_for_summarization(self):
        """Test that Gemini is used for summarization tasks when available."""
        with patch('app.config.settings.google_api_key', 'test_key'):
            with patch('app.llm.ChatGoogleGenerativeAI') as mock_gemini_class:
                mock_gemini = Mock()
                mock_gemini_class.return_value = mock_gemini
                
                llm_manager = LLMManager()
                
                # Should return Gemini LLM for summarization
                llm = llm_manager.get_llm_for_task("summarization")
                assert llm == llm_manager.gemini_llm
    
    @pytest.mark.asyncio
    async def test_gemini_summarization_call(self):
        """Test that Gemini is called for source summarization."""
        with patch('app.config.settings.google_api_key', 'test_key'):
            with patch('app.llm.ChatGoogleGenerativeAI') as mock_gemini_class:
                mock_gemini = Mock()
                mock_gemini.ainvoke = AsyncMock()
                mock_gemini_class.return_value = mock_gemini
                
                llm_manager = LLMManager()
                
                # Mock the parser and chain
                with patch('app.llm.PydanticOutputParser') as mock_parser_class:
                    mock_parser = Mock()
                    mock_parser_class.return_value = mock_parser
                    mock_parser.get_format_instructions.return_value = "test instructions"
                    
                    # Mock the chain
                    with patch('app.llm.ChatPromptTemplate.from_messages') as mock_prompt:
                        mock_chain = Mock()
                        mock_prompt.return_value.__or__ = Mock(return_value=mock_chain)
                        mock_chain.__or__ = Mock(return_value=mock_chain)
                        mock_chain.ainvoke = AsyncMock()
                        
                        # Call summarize_source
                        await llm_manager.summarize_source(
                            source_content="Test content",
                            source_url="https://example.com",
                            topic="Test topic"
                        )
                        
                        # Verify Gemini was used
                        assert mock_gemini.ainvoke.called 