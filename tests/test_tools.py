"""
Unit tests for tools (search, content fetching)
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
import aiohttp

from app.tools import WebSearchTool, ContentFetcherTool, SearchAndFetchTool, ResearchSearchTool


class TestWebSearchTool:
    """Test web search functionality."""
    
    @pytest.fixture
    def search_tool(self):
        """Create search tool instance."""
        return WebSearchTool()
    
    def test_search_tool_initialization(self, search_tool):
        """Test search tool is properly initialized."""
        assert search_tool.name == "web_search"
        assert "search" in search_tool.description.lower()
    
    @patch('app.tools.DDGS')
    def test_search_success(self, mock_ddgs, search_tool):
        """Test successful search operation."""
        # Mock DDGS response
        mock_results = [
            {
                'href': 'https://example.com/1',
                'title': 'AI Article 1',
                'body': 'AI content summary 1'
            },
            {
                'href': 'https://example.com/2', 
                'title': 'AI Article 2',
                'body': 'AI content summary 2'
            }
        ]
        
        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.text.return_value = mock_results
        mock_ddgs_instance.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_instance.__exit__.return_value = None
        mock_ddgs.return_value = mock_ddgs_instance
        
        result = search_tool._run("artificial intelligence", max_results=2)
        
        assert len(result) == 2
        assert result[0].url == 'https://example.com/1'
        assert result[0].title == 'AI Article 1'
        assert result[0].snippet == 'AI content summary 1'
    
    @patch('app.tools.DDGS')
    def test_search_fallback(self, mock_ddgs, search_tool):
        """Test search fallback when DDGS fails."""
        # Mock DDGS to raise exception
        mock_ddgs.side_effect = Exception("Search API error")
        
        result = search_tool._run("test query", max_results=1)
        
        # Should return fallback result
        assert len(result) == 1
        assert "test query" in result[0].title.lower()
        assert "research information" in result[0].title.lower()


class TestContentFetcherTool:
    """Test content fetching functionality."""
    
    @pytest.fixture
    def content_tool(self):
        """Create content fetcher tool instance."""
        return ContentFetcherTool()
    
    def test_content_tool_initialization(self, content_tool):
        """Test content tool is properly initialized."""
        assert content_tool.name == "content_fetcher"
        assert "fetch" in content_tool.description.lower()
    
    @pytest.mark.asyncio
    async def test_fetch_content_success(self, content_tool):
        """Test successful content fetching."""
        mock_html = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <h1>Main Title</h1>
                <p>This is the main content of the article.</p>
                <p>More content here about AI and technology.</p>
            </body>
        </html>
        """
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = mock_html.encode('utf-8')
            mock_get.return_value = mock_response
            
            result = content_tool._run("https://example.com/article")
            
            assert result["success"] is True
            assert "Main Title" in result["content"]
            assert "main content" in result["content"]
    
    @pytest.mark.asyncio
    async def test_fetch_content_failure(self, content_tool):
        """Test content fetching failure handling."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = content_tool._run("https://example.com/notfound")
            
            assert result["success"] is False
            assert "error" in result["content"].lower()


class TestSearchAndFetchTool:
    """Test combined search and fetch functionality."""
    
    @pytest.fixture
    def search_fetch_tool(self):
        """Create search and fetch tool instance."""
        return SearchAndFetchTool()
    
    def test_tool_initialization(self, search_fetch_tool):
        """Test tool is properly initialized."""
        assert search_fetch_tool.name == "search_and_fetch"
        assert hasattr(search_fetch_tool, 'search_tool')
        assert hasattr(search_fetch_tool, 'fetch_tool')
    
    @patch('app.tools.WebSearchTool._run')
    @patch('app.tools.ContentFetcherTool._run')
    def test_search_and_fetch_success(self, mock_fetch, mock_search, search_fetch_tool):
        """Test successful search and fetch operation."""
        # Mock search results
        mock_search_result = Mock()
        mock_search_result.url = "https://example.com"
        mock_search_result.title = "AI Article"
        mock_search_result.snippet = "AI summary"
        mock_search_result.domain = "example.com"
        mock_search_result.model_dump.return_value = {
            "url": "https://example.com",
            "title": "AI Article",
            "snippet": "AI summary",
            "domain": "example.com"
        }
        mock_search.return_value = [mock_search_result]
        
        # Mock content fetch
        mock_fetch.return_value = {
            "success": True,
            "content": "Full article content about AI",
            "title": "AI Article",
            "meta_description": "Article about AI"
        }
        
        result = search_fetch_tool._run("artificial intelligence", max_results=1)
        
        assert len(result) == 1
        assert result[0]["search_result"]["url"] == "https://example.com"
        assert result[0]["content"]["success"] is True


class TestResearchSearchTool:
    """Test research-specific search tool."""
    
    @pytest.fixture
    def research_tool(self):
        """Create research search tool instance."""
        return ResearchSearchTool()
    
    def test_research_tool_initialization(self, research_tool):
        """Test research tool is properly initialized."""
        assert research_tool.name == "research_search"
        assert "research" in research_tool.description.lower()
    
    @pytest.mark.asyncio
    @patch('app.tools.SearchAndFetchTool._run')
    async def test_research_search(self, mock_search_fetch, research_tool):
        """Test research search functionality."""
        # Mock search and fetch results
        mock_results = [
            {
                "search_result": {
                    "url": "https://example.com/ai",
                    "title": "AI Research Paper",
                    "snippet": "Academic research on AI"
                },
                "content": {
                    "success": True,
                    "content": "Full research paper content"
                }
            }
        ]
        mock_search_fetch.return_value = mock_results
        
        result = await research_tool._arun(topic="artificial intelligence", depth=3)
        
        assert len(result) == 1
        assert result[0]["search_result"]["title"] == "AI Research Paper"
        
        # Verify search was called (multiple times due to depth=3)
        assert mock_search_fetch.call_count >= 1
        # Check that artificial intelligence was in one of the search calls
        call_found = False
        for call in mock_search_fetch.call_args_list:
            if "artificial intelligence" in str(call).lower():
                call_found = True
                break
        assert call_found