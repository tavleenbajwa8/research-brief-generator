"""
LLM configurations and LangChain integrations.
"""

import os
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.schemas import ResearchPlan, SourceSummary, ContextSummary, FinalBrief


class LLMManager:
    """Manager for different LLM configurations and interactions."""
    
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
        if task_type == "summarization" and self.gemini_llm:
            return self.gemini_llm
        return self.openai_llm
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_research_plan(
        self, 
        topic: str, 
        depth: int, 
        context_summary: Optional[ContextSummary] = None,
        token_usage: Optional[Dict[str, int]] = None
    ) -> ResearchPlan:
        """Generate a structured research plan."""
        
        parser = PydanticOutputParser(pydantic_object=ResearchPlan)
        
        context_prompt = ""
        if context_summary:
            context_prompt = f"""
            Previous research context:
            - Previous topics: {', '.join(context_summary.previous_topics)}
            - Key themes: {', '.join(context_summary.key_themes)}
            - Preferred depth: {context_summary.preferred_depth}
            """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert research planner. Create a detailed, structured research plan for the given topic.

The plan should include:
1. Clear research steps with priorities
2. Estimated time for each step
3. Focus areas to explore
4. Keywords for each step

{format_instructions}"""),
            ("human", f"""Topic: {topic}
Depth Level: {depth} (1=basic overview, 5=comprehensive analysis)
{context_prompt}

Generate a research plan that will guide the research process effectively.""")
        ])
        
        # Use the older, more compatible LangChain syntax
        formatted_prompt = prompt.format_messages(
            format_instructions=parser.get_format_instructions()
        )
        
        response = await self.openai_llm.ainvoke(formatted_prompt)
        result = parser.parse(response.content)
        
        # Track token usage if provided
        if token_usage is not None and hasattr(response, 'usage_metadata') and response.usage_metadata:
            total_tokens = response.usage_metadata.get('total_tokens', 0)
            token_usage['planning'] = token_usage.get('planning', 0) + total_tokens
        
        return result
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def summarize_context(
        self, 
        user_id: str, 
        previous_briefs: list,
        current_topic: str,
        token_usage: Optional[Dict[str, int]] = None
    ) -> ContextSummary:
        """Summarize user context from previous interactions."""
        
        parser = PydanticOutputParser(pydantic_object=ContextSummary)
        
        brief_summaries = []
        for brief in previous_briefs[:5]:  # Last 5 briefs
            brief_summaries.append(f"- {brief.topic}: {brief.summary[:200]}...")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing user research patterns and preferences. 
Summarize the user's research history and preferences into a structured context.

{format_instructions}"""),
            ("human", f"""User ID: {user_id}
Current Topic: {current_topic}

Previous Research Briefs:
{chr(10).join(brief_summaries) if brief_summaries else "No previous briefs found."}

Analyze the user's research patterns and create a context summary that will help personalize future research briefs.""")
        ])
        
        # Use the older, more compatible LangChain syntax
        formatted_prompt = prompt.format_messages(
            format_instructions=parser.get_format_instructions()
        )
        
        response = await self.openai_llm.ainvoke(formatted_prompt)
        result = parser.parse(response.content)
        
        # Track token usage if provided
        if token_usage is not None and hasattr(response, 'usage_metadata') and response.usage_metadata:
            total_tokens = response.usage_metadata.get('total_tokens', 0)
            token_usage['context'] = token_usage.get('context', 0) + total_tokens
        
        return result
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def summarize_source(
        self, 
        source_content: str, 
        source_url: str,
        topic: str,
        token_usage: Optional[Dict[str, int]] = None
    ) -> SourceSummary:
        """Summarize a single source with structured output."""
        
        parser = PydanticOutputParser(pydantic_object=SourceSummary)
        
        llm = self.get_llm_for_task("summarization")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert research analyst. Summarize the given source content 
and extract key information in a structured format.

{format_instructions}"""),
            ("human", f"""Topic: {topic}
Source URL: {source_url}

Source Content:
{source_content[:4000]}...

Please provide a comprehensive summary with:
1. Key points extracted
2. Relevance score (0-1) based on topic alignment
3. Credibility score (0-1) based on source quality
4. Structured metadata""")
        ])
        
        # Use the older, more compatible LangChain syntax
        formatted_prompt = prompt.format_messages(
            format_instructions=parser.get_format_instructions()
        )
        
        response = await llm.ainvoke(formatted_prompt)
        result = parser.parse(response.content)
        
        # Track token usage if provided
        if token_usage is not None and hasattr(response, 'usage_metadata') and response.usage_metadata:
            total_tokens = response.usage_metadata.get('total_tokens', 0)
            token_usage['summarization'] = token_usage.get('summarization', 0) + total_tokens
        
        return result
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def synthesize_brief(
        self, 
        topic: str,
        source_summaries: list,
        research_plan: ResearchPlan,
        context_summary: Optional[ContextSummary] = None,
        token_usage: Optional[Dict[str, int]] = None
    ) -> FinalBrief:
        """Synthesize all source summaries into a final research brief."""
        
        parser = PydanticOutputParser(pydantic_object=FinalBrief)
        
        context_prompt = ""
        if context_summary and context_summary.previous_topics:
            context_prompt = f"""
            User Context (for follow-up queries):
            - Previous research topics: {', '.join(context_summary.previous_topics)}
            - Key themes explored: {', '.join(context_summary.key_themes)}
            - User's preferred research depth: {context_summary.preferred_depth}
            - This research should build upon and connect to previous work.
            """
        
        source_summaries_text = ""
        for i, summary in enumerate(source_summaries, 1):
            source_summaries_text += f"""
            Source {i}:
            - Title: {summary.metadata.title}
            - URL: {summary.metadata.url}
            - Summary: {summary.summary}
            - Key Points: {', '.join(summary.key_points)}
            - Relevance: {summary.relevance_score}
            """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert research analyst. Create a comprehensive research brief
that synthesizes information from multiple sources into a coherent, well-structured document.

{format_instructions}"""),
            ("human", f"""Topic: {topic}
Research Plan: {research_plan.dict()}
{context_prompt}

Source Summaries:
{source_summaries_text}

Create a comprehensive research brief that:
1. Provides an executive summary
2. Identifies key findings
3. Describes the methodology used
4. Includes recommendations
5. Acknowledges limitations
6. Properly references all sources""")
        ])
        
        # Use the older, more compatible LangChain syntax
        formatted_prompt = prompt.format_messages(
            format_instructions=parser.get_format_instructions()
        )
        
        response = await self.openai_llm.ainvoke(formatted_prompt)
        result = parser.parse(response.content)
        
        # Track token usage if provided
        if token_usage is not None and hasattr(response, 'usage_metadata') and response.usage_metadata:
            total_tokens = response.usage_metadata.get('total_tokens', 0)
            token_usage['synthesis'] = token_usage.get('synthesis', 0) + total_tokens
        
        return result


# Global LLM manager instance
llm_manager = LLMManager() 