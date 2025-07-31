"""
Command Line Interface for Research Brief Generator

Provides CLI access to the research brief generation functionality.
"""

import asyncio
import json
import sys
import warnings
import os
from typing import Optional
import click

# Suppress Windows asyncio cleanup warnings globally
if sys.platform == "win32":
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    # Also suppress stderr output for these specific messages
    import contextlib
    import io
    
    # Monkey patch to suppress ProactorBasePipeTransport cleanup warnings
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        original_del = _ProactorBasePipeTransport.__del__
        
        def silent_del(self):
            try:
                original_del(self)
            except Exception:
                pass  # Silently ignore cleanup exceptions
        
        _ProactorBasePipeTransport.__del__ = silent_del
    except ImportError:
        pass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax

from app.config import settings
from app.schemas import BriefRequest, FinalBrief
from app.graph import research_graph
from app.database import db_manager

console = Console()

def display_brief(brief: FinalBrief) -> None:
    """Display a research brief in a formatted way."""
    console.print(f"\n[bold blue]Research Brief: {brief.brief_id}[/bold blue]")
    console.print(f"[dim]Generated at: {brief.generated_at}[/dim]\n")
    
    # Summary
    console.print(Panel(brief.summary, title="[bold]Summary[/bold]", border_style="blue"))
    
    # Key Findings
    console.print("\n[bold green]Key Findings:[/bold green]")
    for i, finding in enumerate(brief.key_findings, 1):
        console.print(f"  {i}. {finding}")
    
    # Methodology
    console.print(f"\n[bold yellow]Methodology:[/bold yellow]\n{brief.methodology}")
    
    # Sources
    console.print("\n[bold magenta]Sources:[/bold magenta]")
    if brief.sources:
        for source in brief.sources:
            console.print(f"  • {source.metadata.title if source.metadata else 'Unknown'}")
            console.print(f"    URL: {source.metadata.url if source.metadata else 'N/A'}")
            console.print(f"    Relevance: {source.relevance_score:.2f}/1.0")
            console.print(f"    Summary: {source.summary[:100]}...")
            console.print()
    else:
        console.print("  No sources available")
    
    # Recommendations
    console.print("[bold cyan]Recommendations:[/bold cyan]")
    for i, rec in enumerate(brief.recommendations, 1):
        console.print(f"  {i}. {rec}")
    
    # Limitations
    console.print(f"\n[bold red]Limitations:[/bold red]\n{brief.limitations}")
    
    # Metadata
    console.print(f"\n[dim]Execution Time: {brief.execution_time:.2f}s[/dim]")
    console.print(f"[dim]Cost Estimate: ${brief.cost_estimate:.4f}[/dim]")
    console.print(f"[dim]Token Usage: {sum(brief.token_usage.values())} tokens[/dim]")

def display_user_briefs(briefs: list) -> None:
    """Display a list of user briefs in a table format."""
    if not briefs:
        console.print("[yellow]No previous briefs found for this user.[/yellow]")
        return
    
    table = Table(title=f"Previous Briefs for User")
    table.add_column("Brief ID", style="cyan")
    table.add_column("Topic", style="green")
    table.add_column("Generated", style="blue")
    table.add_column("Execution Time", style="yellow")
    table.add_column("Cost", style="red")
    
    for brief in briefs:
        table.add_row(
            brief.brief_id[:8] + "...",
            brief.summary[:50] + "..." if len(brief.summary) > 50 else brief.summary,
            brief.generated_at.strftime("%Y-%m-%d %H:%M"),
            f"{brief.execution_time:.2f}s",
            f"${brief.cost_estimate:.4f}"
        )
    
    console.print(table)

@click.group()
@click.version_option(version=settings.app_version, prog_name=settings.app_name)
def cli():
    """Research Brief Generator CLI
    
    A context-aware research assistant system using LangGraph and LangChain.
    """
    # Suppress Windows asyncio cleanup warnings
    if sys.platform == "win32":
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        warnings.filterwarnings("ignore", message=".*Exception ignored.*")
        warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
    pass

@cli.command()
@click.option('--topic', '-t', required=True, help='Research topic')
@click.option('--depth', '-d', default=3, type=click.IntRange(1, 5), help='Research depth (1-5)')
@click.option('--user-id', '-u', required=True, help='User identifier')
@click.option('--follow-up', '-f', is_flag=True, help='Mark as follow-up query')
@click.option('--output', '-o', help='Output file for JSON response')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def generate(topic: str, depth: int, user_id: str, follow_up: bool, output: Optional[str], verbose: bool):
    """Generate a research brief for a given topic."""
    if verbose:
        console.print(f"[bold]Generating research brief...[/bold]")
        console.print(f"Topic: {topic}")
        console.print(f"Depth: {depth}")
        console.print(f"User ID: {user_id}")
        console.print(f"Follow-up: {follow_up}")
        console.print()
    
    async def run_generation():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Generating research brief...", total=None)
                
                brief = await research_graph.run(
                    topic=topic,
                    depth=depth,
                    user_id=user_id,
                    follow_up=follow_up
                )
                
                progress.update(task, description="Research brief generated successfully!")
            
            # Display the brief
            display_brief(brief)
            
            # Save to file if requested
            if output:
                with open(output, 'w') as f:
                    json.dump(brief.dict(), f, indent=2, default=str)
                console.print(f"\n[green]Brief saved to {output}[/green]")
            
            return brief
            
        except Exception as e:
            console.print(f"\nError generating brief: {str(e)}")
            if verbose:
                console.print_exception()
            return
    
    try:
        # Use asyncio.run with proper cleanup to avoid Runtime errors
        if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Run with proper cleanup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_generation())
            return result
        finally:
            # Properly close the loop and cleanup
            try:
                # Cancel all pending tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                # Wait for tasks to complete with stderr suppression
                if pending:
                    with contextlib.redirect_stderr(io.StringIO()):
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            finally:
                with contextlib.redirect_stderr(io.StringIO()):
                    loop.close()
    except Exception as e:
        console.print(f"\nError: {str(e)}")
        return

@cli.command()
@click.option('--user-id', '-u', required=True, help='User identifier')
@click.option('--limit', '-l', default=10, help='Maximum number of briefs to show')
def history(user_id: str, limit: int):
    """Show research brief history for a user."""
    try:
        briefs = db_manager.get_user_briefs(user_id, limit)
        display_user_briefs(briefs)
    except Exception as e:
        console.print(f"Error retrieving history: {str(e)}")
        sys.exit(1)

@cli.command()
@click.option('--user-id', '-u', required=True, help='User identifier')
def context(user_id: str):
    """Show user context information."""
    try:
        context = db_manager.get_user_context(user_id)
        if context:
            console.print(f"\n[bold blue]User Context for {user_id}[/bold blue]")
            console.print(f"Previous Topics: {', '.join(context.previous_topics)}")
            console.print(f"Key Themes: {', '.join(context.key_themes)}")
            console.print(f"Preferred Depth: {context.preferred_depth}")
            console.print(f"Last Interaction: {context.last_interaction}")
            console.print(f"Context Relevance Score: {context.context_relevance_score:.2f}")
        else:
            console.print(f"[yellow]No context found for user {user_id}[/yellow]")
    except Exception as e:
        console.print(f"Error retrieving context: {str(e)}")
        sys.exit(1)

@cli.command()
def interactive():
    """Start an interactive session for generating research briefs."""
    console.print(Panel.fit(
        "[bold blue]Research Brief Generator - Interactive Mode[/bold blue]\n"
        "Generate research briefs interactively. Press Ctrl+C to exit.",
        border_style="blue"
    ))
    
    while True:
        try:
            console.print("\n" + "="*50)
            
            # Get topic
            topic = Prompt.ask("[bold green]Enter research topic[/bold green]")
            if not topic.strip():
                continue
            
            # Get depth
            depth = Prompt.ask(
                "[bold yellow]Research depth (1-5)[/bold yellow]",
                default="3",
                choices=["1", "2", "3", "4", "5"]
            )
            
            # Get user ID
            user_id = Prompt.ask("[bold cyan]User ID[/bold cyan]")
            if not user_id.strip():
                continue
            
            # Check if follow-up
            follow_up = Confirm.ask("[bold magenta]Is this a follow-up query?[/bold magenta]", default=False)
            
            # Show user context if available
            try:
                context = db_manager.get_user_context(user_id)
                if context and context.previous_topics:
                    console.print(f"\n[dim]Previous topics: {', '.join(context.previous_topics)}[/dim]")
            except Exception:
                pass
            
            # Confirm generation
            if Confirm.ask(f"\n[bold]Generate brief for '{topic}' with depth {depth}?[/bold]", default=True):
                async def run_interactive():
                    try:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            console=console
                        ) as progress:
                            task = progress.add_task("Generating research brief...", total=None)
                            
                            brief = await research_graph.run(
                                topic=topic,
                                depth=int(depth),
                                user_id=user_id,
                                follow_up=follow_up
                            )
                            
                            progress.update(task, description="Research brief generated successfully!")
                        
                        display_brief(brief)
                        
                        # Ask if user wants to save
                        if Confirm.ask("\n[bold]Save brief to file?[/bold]", default=False):
                            filename = Prompt.ask("Filename", default=f"brief_{brief.brief_id[:8]}.json")
                            with open(filename, 'w') as f:
                                json.dump(brief.dict(), f, indent=2, default=str)
                            console.print(f"[green]Brief saved to {filename}[/green]")
                        
                    except Exception as e:
                        console.print(f"\nError generating brief: {str(e)}")
                
                # Run with proper cleanup
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(run_interactive())
                finally:
                    # Properly close the loop and cleanup
                    try:
                        # Cancel all pending tasks
                        pending = asyncio.all_tasks(loop)
                        for task in pending:
                            task.cancel()
                        
                        # Wait for tasks to complete with stderr suppression
                        if pending:
                            with contextlib.redirect_stderr(io.StringIO()):
                                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception:
                        pass
                    finally:
                        with contextlib.redirect_stderr(io.StringIO()):
                            loop.close()
            
            # Ask if user wants to continue
            if not Confirm.ask("\n[bold]Generate another brief?[/bold]", default=True):
                break
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting interactive mode...[/yellow]")
            break
        except Exception as e:
            console.print(f"\nError: {str(e)}")

@cli.command()
def config():
    """Show current configuration."""
    console.print(Panel.fit(
        f"[bold]Configuration[/bold]\n\n"
        f"App Name: {settings.app_name}\n"
        f"Version: {settings.app_version}\n"
        f"Debug: {settings.debug}\n"
        f"Log Level: {settings.log_level}\n"
        f"Database URL: {settings.database_url}\n"
        f"Default Model: {settings.default_model}\n"
        f"Summarization Model: {settings.summarization_model}\n"
        f"Max Search Results: {settings.max_search_results}\n"
        f"Search Timeout: {settings.search_timeout}s\n"
        f"Rate Limit (per minute): {settings.rate_limit_per_minute}\n"
        f"Rate Limit (per hour): {settings.rate_limit_per_hour}",
        title="[bold blue]Current Settings[/bold blue]",
        border_style="blue"
    ))

@cli.command()
def health():
    """Check system health."""
    console.print("[bold]Checking system health...[/bold]")
    
    # Check database connection
    try:
        from sqlalchemy import text
        session = db_manager.get_session()
        session.execute(text("SELECT 1"))
        session.close()
        console.print("[green]✓ Database connection: OK[/green]")
    except Exception as e:
        console.print(f"[red]✗ Database connection: FAILED - {str(e)}[/red]")
    
    # Check API keys
    if settings.openai_api_key:
        console.print("[green]✓ OpenAI API key: Configured[/green]")
    else:
        console.print("[red]✗ OpenAI API key: Not configured[/red]")
    
    if settings.google_api_key:
        console.print("[green]✓ Google API key: Configured[/green]")
    else:
        console.print("[yellow]⚠ Google API key: Not configured (summarization will use OpenAI)[/yellow]")
    
    if settings.langsmith_api_key:
        console.print("[green]✓ LangSmith API key: Configured[/green]")
    else:
        console.print("[yellow]⚠ LangSmith API key: Not configured (tracing disabled)[/yellow]")

if __name__ == '__main__':
    cli() 