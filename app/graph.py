"""
LangGraph workflow for research brief generation.
"""

import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.schemas import GraphState, ContextSummary, ResearchPlan, SourceSummary, FinalBrief
from app.llm_simple import get_simple_llm_manager
from app.tools import research_search_tool
from app.database import db_manager


class ResearchBriefGraph:
    """LangGraph workflow for research brief generation."""
    
    def __init__(self):
        self.graph = self._build_graph()
        # Disable checkpointing to avoid serialization issues
        # self.checkpointer = MemorySaver()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create the graph
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("context_summarization", self._context_summarization_node)
        workflow.add_node("planning", self._planning_node)
        workflow.add_node("search", self._search_node)
        workflow.add_node("content_fetching", self._content_fetching_node)
        workflow.add_node("per_source_summarization", self._per_source_summarization_node)
        workflow.add_node("synthesis", self._synthesis_node)
        workflow.add_node("post_processing", self._post_processing_node)
        
        # Define the workflow
        workflow.set_entry_point("context_summarization")
        
        # Add edges with conditional logic
        workflow.add_edge("context_summarization", "planning")
        workflow.add_edge("planning", "search")
        workflow.add_edge("search", "content_fetching")
        workflow.add_edge("content_fetching", "per_source_summarization")
        workflow.add_edge("per_source_summarization", "synthesis")
        workflow.add_edge("synthesis", "post_processing")
        workflow.add_edge("post_processing", END)
        
        return workflow
    
    async def _context_summarization_node(self, state: GraphState) -> GraphState:
        """Node for summarizing user context and previous interactions."""
        state.current_step = "context_summarization"
        
        try:
            if state.follow_up:
                # Get user's previous briefs
                previous_briefs = db_manager.get_user_briefs(state.user_id, limit=5)
                
                # Generate context summary
                context_summary = await get_simple_llm_manager().summarize_context(
                    user_id=state.user_id,
                    previous_briefs=previous_briefs,
                    current_topic=state.topic,
                    token_usage=state.token_usage
                )
                
                state.context_summary = context_summary
            else:
                # For new queries, create minimal context
                state.context_summary = ContextSummary(
                    user_id=state.user_id,
                    previous_topics=[],
                    key_themes=[],
                    preferred_depth=state.depth,
                    last_interaction=None,
                    context_relevance_score=0.0
                )
            
            return state
        
        except Exception as e:
            state.errors.append(f"Context summarization error: {str(e)}")
            return state
    
    async def _planning_node(self, state: GraphState) -> GraphState:
        """Node for creating research plan."""
        state.current_step = "planning"
        
        try:
            # Generate research plan
            research_plan = await get_simple_llm_manager().generate_research_plan(
                topic=state.topic,
                depth=state.depth,
                context_summary=state.context_summary,
                token_usage=state.token_usage
            )
            
            state.research_plan = research_plan
            return state
        
        except Exception as e:
            state.errors.append(f"Planning error: {str(e)}")
            # Create a fallback research plan instead of failing completely
            from app.schemas import ResearchStep
            state.research_plan = ResearchPlan(
                topic=state.topic,
                depth=state.depth,
                steps=[
                    ResearchStep(
                        step_id=1,
                        title=f"Research {state.topic} basics",
                        description=f"Find basic information about {state.topic}",
                        priority=5,
                        estimated_time=30,
                        keywords=[state.topic, "basics", "introduction"]
                    )
                ],
                total_estimated_time=30,
                focus_areas=[state.topic, "fundamentals"]
            )
            return state
    
    async def _search_node(self, state: GraphState) -> GraphState:
        """Node for performing web searches."""
        state.current_step = "search"
        
        try:
            # Perform research search
            search_results = await research_search_tool._arun(
                topic=state.topic,
                depth=state.depth
            )
            
            state.search_results = search_results
            return state
        
        except Exception as e:
            state.errors.append(f"Search error: {str(e)}")
            return state
    
    async def _content_fetching_node(self, state: GraphState) -> GraphState:
        """Node for fetching content from search results."""
        state.current_step = "content_fetching"
        
        # Content is already fetched in the search step
        # This node can be used for additional content processing if needed
        return state
    
    async def _per_source_summarization_node(self, state: GraphState) -> GraphState:
        """Node for summarizing individual sources."""
        state.current_step = "per_source_summarization"
        
        try:
            source_summaries = []
            
            for i, result in enumerate(state.search_results):
                content_data = result.get("content", {})
                search_result = result["search_result"]
                
                # Skip if we don't have basic search result data
                if not search_result:
                    continue
                
                # Create source metadata
                from app.schemas import SourceMetadata
                metadata = SourceMetadata(
                    title=search_result.get("title", "Search Result"),
                    url=search_result.get("url", ""),
                    domain=search_result.get("domain", ""),
                    publication_date=None,  # Would need additional parsing
                    author=None,  # Would need additional parsing
                    source_type="web_article"
                )
                
                # Generate source summary
                # Use content if available, otherwise use search snippet
                if content_data.get("success", False) and content_data.get("content"):
                    source_content = content_data.get("content", "")
                else:
                    # Use search snippet when content fetching failed
                    source_content = search_result.get("snippet", "")
                
                try:
                    source_summary = await get_simple_llm_manager().summarize_source(
                        source_content=source_content,
                        source_url=search_result.get("url", ""),
                        topic=state.topic,
                        token_usage=state.token_usage
                    )
                    
                    # Update metadata
                    source_summary.metadata = metadata
                    source_summary.source_id = f"source_{i}_{uuid.uuid4().hex[:8]}"
                    
                    source_summaries.append(source_summary)
                except Exception as e:
                    # Create a fallback source summary if LLM fails
                    from app.schemas import SourceSummary
                    fallback_summary = SourceSummary(
                        source_id=f"source_{i}_{uuid.uuid4().hex[:8]}",
                        metadata=metadata,
                        summary=f"Information about {state.topic} from {search_result.get('title', 'this source')}",
                        key_points=[f"Key information about {state.topic}"],
                        relevance_score=0.6,
                        credibility_score=0.5
                    )
                    source_summaries.append(fallback_summary)
            
            state.source_summaries = source_summaries
            return state
        
        except Exception as e:
            state.errors.append(f"Source summarization error: {str(e)}")
            return state
    
    async def _synthesis_node(self, state: GraphState) -> GraphState:
        """Node for synthesizing all information into final brief."""
        state.current_step = "synthesis"
        
        try:
            # Check if research plan exists, if not create a simple one
            if not state.research_plan:
                from app.schemas import ResearchStep
                state.research_plan = ResearchPlan(
                    topic=state.topic,
                    depth=state.depth,
                    steps=[
                        ResearchStep(
                            step_id=1,
                            title=f"Research {state.topic} basics",
                            description=f"Find basic information about {state.topic}",
                            priority=5,
                            estimated_time=30,
                            keywords=[state.topic, "basics", "introduction"]
                        )
                    ],
                    total_estimated_time=30,
                    focus_areas=[state.topic, "fundamentals"]
                )
            
            # Generate final brief
            final_brief = await get_simple_llm_manager().synthesize_brief(
                topic=state.topic,
                source_summaries=state.source_summaries,
                research_plan=state.research_plan,
                context_summary=state.context_summary,
                token_usage=state.token_usage
            )
            
            # Add metadata
            final_brief.brief_id = f"brief_{uuid.uuid4().hex}"
            final_brief.generated_at = datetime.utcnow()
            
            # Calculate execution time
            if state.start_time:
                final_brief.execution_time = time.time() - state.start_time.timestamp()
            else:
                final_brief.execution_time = 0.0
            
            # Estimate cost (simplified)
            total_tokens = sum(state.token_usage.values()) if state.token_usage else 0
            final_brief.token_usage = state.token_usage
            final_brief.cost_estimate = total_tokens * 0.00003  # Rough estimate
            
            state.final_brief = final_brief
            return state
        
        except Exception as e:
            state.errors.append(f"Synthesis error: {str(e)}")
            return state
    
    async def _post_processing_node(self, state: GraphState) -> GraphState:
        """Node for post-processing and saving results."""
        state.current_step = "post_processing"
        
        try:
            if state.final_brief:
                # Save brief to database
                print(f"DEBUG: Saving brief {state.final_brief.brief_id} for user {state.user_id}")
                db_manager.save_brief(state.final_brief, state.user_id)
                print(f"DEBUG: Brief saved successfully")
                
                # Update user context
                print(f"DEBUG: Updating user context for {state.user_id}")
                db_manager.update_user_context(
                    user_id=state.user_id,
                    topic=state.topic,
                    depth=state.depth
                )
                print(f"DEBUG: User context updated successfully")
            else:
                print(f"DEBUG: No final_brief to save")
            
            return state
        
        except Exception as e:
            print(f"DEBUG: Post-processing error: {str(e)}")
            state.errors.append(f"Post-processing error: {str(e)}")
            return state
    
    async def run(self, topic: str, depth: int, user_id: str, follow_up: bool = False) -> FinalBrief:
        """Run the research brief generation workflow."""
        
        # Initialize state
        initial_state = GraphState(
            topic=topic,
            depth=depth,
            user_id=user_id,
            follow_up=follow_up,
            start_time=datetime.utcnow()
        )
        
        # Run the workflow
        config = {"configurable": {"thread_id": f"thread_{user_id}_{uuid.uuid4().hex[:8]}"}}
        
        try:
            final_state = await self.app.ainvoke(initial_state, config)
            
            # Handle both dict and GraphState return types
            if isinstance(final_state, dict):
                # Convert dict to GraphState if needed
                if 'final_brief' in final_state and final_state['final_brief']:
                    return final_state['final_brief']
                elif 'errors' in final_state and final_state['errors']:
                    error_msg = "; ".join(final_state['errors'])
                    raise Exception(f"Workflow errors: {error_msg}")
                else:
                    raise Exception("Failed to generate brief - no final_brief in state")
            else:
                # Handle GraphState object
                if final_state.errors:
                    error_msg = "; ".join(final_state.errors)
                    raise Exception(f"Workflow errors: {error_msg}")
                
                if final_state.final_brief:
                    return final_state.final_brief
                else:
                    raise Exception("Failed to generate brief - no final_brief in state")
        
        except Exception as e:
            raise Exception(f"Workflow execution failed: {str(e)}")


# Global graph instance
research_graph = ResearchBriefGraph() 