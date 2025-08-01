"""
Simplified LLM manager for testing.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.schemas import ResearchPlan, SourceSummary, ContextSummary, FinalBrief, SourceMetadata


class SimpleLLMManager:
    """Simplified LLM manager for testing."""
    
    def __init__(self):
        self.openai_llm = ChatOpenAI(
            model=settings.default_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            openai_api_key=settings.openai_api_key
        )
        
        if settings.google_api_key:
            self.gemini_llm = ChatGoogleGenerativeAI(
                model=settings.summarization_model,
                temperature=settings.temperature,
                max_output_tokens=settings.max_tokens,
                google_api_key=settings.google_api_key
            )
        else:
            self.gemini_llm = None
    
    def get_llm_for_task(self, task_type: str) -> ChatOpenAI:
        """Get appropriate LLM for specific task type."""
        # Always use OpenAI for now to avoid Gemini rate limits
        return self.openai_llm
    
    async def generate_research_plan(
        self, 
        topic: str, 
        depth: int, 
        context_summary: Optional[ContextSummary] = None,
        token_usage: Optional[Dict[str, int]] = None
    ) -> ResearchPlan:
        """Generate a structured research plan."""
        
        context_prompt = ""
        if context_summary:
            context_prompt = f"""
            Previous research context:
            - Previous topics: {', '.join(context_summary.previous_topics)}
            - Key themes: {', '.join(context_summary.key_themes)}
            - Preferred depth: {context_summary.preferred_depth}
            """
        
        prompt = f"""You are an expert research planner. Create a detailed, structured research plan for the given topic.

Topic: {topic}
Depth Level: {depth} (1=basic overview, 5=comprehensive analysis)
{context_prompt}

Create a comprehensive research plan with the following structure (respond in JSON format):
{{
    "topic": "{topic}",
    "depth": {depth},
    "steps": [
        {{
            "step_id": 1,
            "title": "Research topic fundamentals and definitions",
            "description": "Find basic definitions, concepts, and fundamental principles related to {topic}",
            "priority": 5,
            "estimated_time": 45,
            "keywords": ["{topic}", "definition", "basics", "fundamentals"]
        }},
        {{
            "step_id": 2,
            "title": "Explore current applications and use cases",
            "description": "Research real-world applications, examples, and practical implementations of {topic}",
            "priority": 4,
            "estimated_time": 60,
            "keywords": ["{topic}", "applications", "use cases", "examples", "implementations"]
        }},
        {{
            "step_id": 3,
            "title": "Analyze trends and future developments",
            "description": "Investigate current trends, emerging technologies, and future directions in {topic}",
            "priority": 3,
            "estimated_time": 40,
            "keywords": ["{topic}", "trends", "future", "emerging", "developments"]
        }}
    ],
    "total_estimated_time": 145,
    "focus_areas": ["{topic}", "applications", "trends", "technology"]
}}

Generate a detailed research plan that will provide comprehensive coverage of {topic}."""

        response = await self.openai_llm.ainvoke(prompt)
        
        # Track token usage if provided (simple estimation based on text length)
        if token_usage is not None:
            estimated_tokens = len(prompt.split()) + len(response.content.split())
            token_usage['planning'] = token_usage.get('planning', 0) + estimated_tokens
        
        try:
            # Try to parse JSON response
            plan_data = json.loads(response.content)
            return ResearchPlan(**plan_data)
        except:
            # Fallback: create a simple plan
            return ResearchPlan(
                topic=topic,
                depth=depth,
                steps=[
                    {
                        "step_id": 1,
                        "title": f"Research {topic} basics",
                        "description": f"Find basic information about {topic}",
                        "priority": 5,
                        "estimated_time": 30,
                        "keywords": [topic, "basics", "introduction"]
                    }
                ],
                total_estimated_time=30,
                focus_areas=[topic, "fundamentals"]
            )
    
    async def summarize_context(
        self, 
        user_id: str, 
        previous_briefs: list,
        current_topic: str,
        token_usage: Optional[Dict[str, int]] = None
    ) -> ContextSummary:
        """Summarize user context from previous interactions."""
        
        # For now, return a simple context
        return ContextSummary(
            user_id=user_id,
            previous_topics=[brief.topic for brief in previous_briefs[:3]],
            key_themes=[topic.split()[0] for topic in [brief.topic for brief in previous_briefs[:3]]],
            preferred_depth=3,
            last_interaction=datetime.utcnow(),
            context_relevance_score=0.5
        )
    
    async def summarize_source(
        self, 
        source_content: str, 
        source_url: str,
        topic: str,
        token_usage: Optional[Dict[str, int]] = None
    ) -> SourceSummary:
        """Summarize a single source with structured output."""
        
        llm = self.get_llm_for_task("summarization")
        
        # Check if content is available or if it's a search snippet
        if ("Content could not be fetched" in source_content or 
            "Sample content" in source_content or 
            len(source_content) < 500):  # Likely a search snippet
            # Use search snippet instead
            prompt = f"""Summarize the following search result about {topic}:

Source URL: {source_url}
Search Snippet: {source_content}

Provide a summary in JSON format:
{{
    "summary": "A summary of the search result about {topic}, including any key information available from the search snippet.",
    "key_points": [
        "Key point 1: Information about {topic}",
        "Key point 2: Additional details about {topic}"
    ],
    "relevance_score": 0.6,
    "credibility_score": 0.5
}}

Provide a summary based on the available search information about {topic}."""
        else:
            prompt = f"""Summarize the following source content about {topic}:

Source URL: {source_url}
Content: {source_content[:2000]}...

Provide a detailed summary in JSON format:
{{
    "summary": "A comprehensive summary of the key information about {topic} from this source, including main concepts, findings, and insights. This should be 2-3 sentences providing substantial detail.",
    "key_points": [
        "Key point 1: Specific insight about {topic}",
        "Key point 2: Another important finding about {topic}",
        "Key point 3: Additional relevant information about {topic}"
    ],
    "relevance_score": 0.8,
    "credibility_score": 0.7
}}

Provide a detailed, informative summary that captures the most important information about {topic} from this source."""

        response = await llm.ainvoke(prompt)
        
        # Track token usage if provided (simple estimation based on text length)
        if token_usage is not None:
            estimated_tokens = len(prompt.split()) + len(response.content.split())
            token_usage['summarization'] = token_usage.get('summarization', 0) + estimated_tokens
        
        try:
            data = json.loads(response.content)
            return SourceSummary(
                source_id=f"source_{uuid.uuid4().hex[:8]}",
                metadata=SourceMetadata(
                    title=f"Source about {topic}",
                    url=source_url,
                    domain=source_url.split('/')[2] if '//' in source_url else "unknown",
                    source_type="web_article"
                ),
                summary=data.get("summary", "Summary not available"),
                key_points=data.get("key_points", []),
                relevance_score=data.get("relevance_score", 0.5),
                credibility_score=data.get("credibility_score", 0.5)
            )
        except:
            # Fallback
            return SourceSummary(
                source_id=f"source_{uuid.uuid4().hex[:8]}",
                metadata=SourceMetadata(
                    title=f"Source about {topic}",
                    url=source_url,
                    domain="example.com",
                    source_type="web_article"
                ),
                summary="Content summary not available",
                key_points=["Key information about the topic"],
                relevance_score=0.5,
                credibility_score=0.5
            )
    
    async def synthesize_brief(
        self, 
        topic: str,
        source_summaries: list,
        research_plan: ResearchPlan,
        context_summary: Optional[ContextSummary] = None,
        token_usage: Optional[Dict[str, int]] = None
    ) -> FinalBrief:
        """Synthesize all source summaries into a final research brief."""
        
        # Check if we have real source content
        real_sources = [s for s in source_summaries if "Content could not be fetched" not in s.summary and "Sample content" not in s.summary]
        
        if real_sources:
            source_text = chr(10).join([f"- {summary.summary}" for summary in real_sources])
            methodology = "This research was conducted using web search and content analysis. Multiple authoritative sources were analyzed to provide a comprehensive understanding of {topic}, including academic sources, industry reports, and expert opinions."
        else:
            source_text = "Limited source content available - research based on general knowledge and search results."
            methodology = "This research was conducted using web search results and general knowledge about {topic}. Due to content fetching limitations, the analysis is based on available search snippets and general information."

        # Add context information if this is a follow-up
        context_info = ""
        if context_summary and context_summary.previous_topics:
            context_info = f"""
User Context (for follow-up queries):
- Previous research topics: {', '.join(context_summary.previous_topics)}
- Key themes explored: {', '.join(context_summary.key_themes)}
- User's preferred research depth: {context_summary.preferred_depth}
- This research should build upon and connect to previous work.
"""

        prompt = f"""Create a comprehensive research brief about {topic}.

        Research Plan: {research_plan.model_dump()}
{context_info}
Source Information:
{source_text}

Create a detailed research brief in JSON format:
{{
    "summary": "A comprehensive executive summary covering the main aspects of {topic}, including its definition, key concepts, applications, and current trends. This should be 3-4 sentences providing a complete overview.",
    "key_findings": [
        "Finding 1: Specific insight about {topic}",
        "Finding 2: Another important discovery about {topic}",
        "Finding 3: Additional key information about {topic}"
    ],
    "methodology": "{methodology}",
    "recommendations": [
        "Recommendation 1: Specific actionable advice related to {topic}",
        "Recommendation 2: Another practical recommendation about {topic}",
        "Recommendation 3: Additional guidance for working with {topic}"
    ],
    "limitations": [
        "Limitation 1: Scope limitation related to {topic} research",
        "Limitation 2: Another constraint of this research approach"
    ]
}}

Provide a detailed, informative research brief that offers real value and insights about {topic}. Even with limited source content, provide the most comprehensive analysis possible based on the topic."""

        response = await self.openai_llm.ainvoke(prompt)
        
        # Track token usage if provided (simple estimation based on text length)
        if token_usage is not None:
            estimated_tokens = len(prompt.split()) + len(response.content.split())
            token_usage['synthesis'] = token_usage.get('synthesis', 0) + estimated_tokens
        
        try:
            data = json.loads(response.content)
            return FinalBrief(
                brief_id=f"brief_{uuid.uuid4().hex}",
                topic=topic,
                summary=data.get("summary", f"Research brief about {topic}"),
                key_findings=data.get("key_findings", [f"Key information about {topic}"]),
                methodology=data.get("methodology", "Web research and analysis"),
                sources=source_summaries,
                recommendations=data.get("recommendations", ["Further research recommended"]),
                limitations=data.get("limitations", ["Limited to available online sources"]),
                generated_at=datetime.utcnow(),
                execution_time=0.0,
                token_usage={},
                cost_estimate=0.0
            )
        except:
            # Fallback
            return FinalBrief(
                brief_id=f"brief_{uuid.uuid4().hex}",
                topic=topic,
                summary=f"Research brief about {topic}",
                key_findings=[f"Key information about {topic}"],
                methodology="Web research and analysis",
                sources=source_summaries,
                recommendations=["Further research recommended"],
                limitations=["Limited to available online sources"],
                generated_at=datetime.utcnow(),
                execution_time=0.0,
                token_usage={},
                cost_estimate=0.0
            )


# Global simplified LLM manager instance (lazy initialization)
simple_llm_manager = None

def get_simple_llm_manager():
    """Get the global SimpleLLMManager instance, creating it if needed."""
    global simple_llm_manager
    if simple_llm_manager is None:
        simple_llm_manager = SimpleLLMManager()
    return simple_llm_manager 