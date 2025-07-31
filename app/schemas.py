"""
Pydantic schemas for structured outputs and validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator, computed_field


class ResearchStep(BaseModel):
    """Individual research planning step."""
    step_id: int = Field(..., description="Unique identifier for the step")
    title: str = Field(..., description="Title of the research step")
    description: str = Field(..., description="Detailed description of what this step involves")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1-5, 5 being highest)")
    estimated_time: int = Field(..., ge=1, description="Estimated time in minutes")
    keywords: List[str] = Field(default_factory=list, description="Keywords for this research step")


class ResearchPlan(BaseModel):
    """Structured research planning steps."""
    topic: str = Field(..., description="The research topic")
    depth: int = Field(..., ge=1, le=5, description="Research depth level (1-5)")
    steps: List[ResearchStep] = Field(..., description="Ordered list of research steps")
    focus_areas: List[str] = Field(..., description="Key focus areas for the research")
    
    @computed_field
    @property
    def total_estimated_time(self) -> int:
        """Compute total estimated time from steps."""
        return sum(step.estimated_time for step in self.steps)


class SourceMetadata(BaseModel):
    """Metadata for a research source."""
    title: str = Field(..., description="Title of the source")
    url: HttpUrl = Field(..., description="URL of the source")
    domain: str = Field(..., description="Domain of the source")
    publication_date: Optional[datetime] = Field(None, description="Publication date if available")
    author: Optional[str] = Field(None, description="Author if available")
    source_type: str = Field(..., description="Type of source (article, paper, report, etc.)")


class SourceSummary(BaseModel):
    """Individual source summary with metadata."""
    source_id: str = Field(..., description="Unique identifier for the source")
    metadata: SourceMetadata = Field(..., description="Source metadata")
    summary: str = Field(..., description="Summarized content from the source")
    key_points: List[str] = Field(..., description="Key points extracted from the source")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")
    credibility_score: float = Field(..., ge=0.0, le=1.0, description="Credibility score (0-1)")
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)


class ContextSummary(BaseModel):
    """Summary of previous user interactions and briefs."""
    user_id: str = Field(..., description="User identifier")
    previous_topics: List[str] = Field(..., description="List of previous research topics")
    key_themes: List[str] = Field(..., description="Recurring themes from previous briefs")
    preferred_depth: int = Field(..., ge=1, le=5, description="User's preferred research depth")
    last_interaction: Optional[datetime] = Field(None, description="Last interaction timestamp")
    context_relevance_score: float = Field(..., ge=0.0, le=1.0, description="How relevant previous context is")


class FinalBrief(BaseModel):
    """Complete research brief with references."""
    brief_id: str = Field(..., description="Unique identifier for the brief")
    topic: str = Field(..., description="The research topic")
    summary: str = Field(..., description="Executive summary of the research")
    key_findings: List[str] = Field(..., description="Key findings from the research")
    methodology: str = Field(..., description="Research methodology used")
    sources: List[SourceSummary] = Field(..., description="All sources used in the research")
    recommendations: List[str] = Field(..., description="Recommendations based on findings")
    limitations: List[str] = Field(..., description="Limitations of the research")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    execution_time: float = Field(..., description="Total execution time in seconds")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Token usage by model")
    cost_estimate: float = Field(..., description="Estimated cost in USD")


class BriefRequest(BaseModel):
    """Request model for generating a research brief."""
    topic: str = Field(..., min_length=1, max_length=500, description="Research topic")
    depth: int = Field(..., ge=1, le=5, description="Research depth (1-5)")
    follow_up: bool = Field(False, description="Whether this is a follow-up query")
    user_id: str = Field(..., description="User identifier")


class BriefResponse(BaseModel):
    """Response model for research brief generation."""
    brief: FinalBrief = Field(..., description="Generated research brief")
    status: str = Field("success", description="Response status")
    message: str = Field("Research brief generated successfully", description="Response message")


class ErrorResponse(BaseModel):
    """Error response model."""
    status: str = Field("error", description="Response status")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code if applicable")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class GraphState(BaseModel):
    """State model for LangGraph execution."""
    topic: str = Field(..., description="Research topic")
    depth: int = Field(..., description="Research depth")
    user_id: str = Field(..., description="User identifier")
    follow_up: bool = Field(False, description="Whether this is a follow-up query")
    
    # Intermediate results
    context_summary: Optional[ContextSummary] = Field(None, description="Context summary")
    research_plan: Optional[ResearchPlan] = Field(None, description="Research plan")
    search_results: List[Dict[str, Any]] = Field(default_factory=list, description="Search results")
    source_summaries: List[SourceSummary] = Field(default_factory=list, description="Source summaries")
    final_brief: Optional[FinalBrief] = Field(None, description="Final brief")
    
    # Execution metadata
    start_time: Optional[datetime] = Field(None, description="Execution start time")
    current_step: str = Field("", description="Current execution step")
    errors: List[str] = Field(default_factory=list, description="Execution errors")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Token usage tracking") 