"""Main CLI application for GitDive."""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__

app = typer.Typer(
    name="gitdive",
    help="CLI tool for natural language conversations with git repository history",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"GitDive v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, help="Show version and exit"
    ),
):
    """GitDive: Natural language conversations with git repository history."""
    pass


@app.command()
def index(
    path: Optional[str] = typer.Argument(
        None, help="Path to git repository (defaults to current directory)"
    ),
    incremental: bool = typer.Option(
        False, "--incremental", help="Perform incremental update of existing index"
    ),
):
    """Index git repository history for natural language queries."""
    from .core.indexer import GitIndexer
    
    # Set default path to current directory
    repo_path = Path(path) if path else Path.cwd()
    
    try:
        indexer = GitIndexer(repo_path)
        
        # Validate repository access
        if not indexer.validate_repository():
            console.print("[red]Error:[/red] Invalid or inaccessible git repository")
            raise typer.Exit(1)
        
        console.print(f"[green]Indexing repository:[/green] {repo_path}")
        if incremental:
            console.print(f"[yellow]Note:[/yellow] Incremental updates will be implemented in Phase 2")
        # Start indexing process
        success = indexer.index_repository()
        
        if success:
            console.print("[green]✓[/green] Repository indexed successfully")
        else:
            console.print("[red]✗[/red] Indexing failed")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question about the repository history"),
):
    """Ask questions about the repository history using natural language."""
    console.print("[yellow]Note:[/yellow] Ask command not yet implemented in Phase 1")
    console.print(f"[blue]Question:[/blue] {question}")
    # TODO: Implement in Phase 4


@app.command()
def stats():
    """Show statistics about indexed repositories."""
    console.print("[yellow]Note:[/yellow] Stats command not yet implemented in Phase 1")
    # TODO: Implement in Phase 5


@app.command()
def cleanup():
    """Clean up stored indexes and temporary files."""
    console.print("[yellow]Note:[/yellow] Cleanup command not yet implemented in Phase 1")
    # TODO: Implement in Phase 5


if __name__ == "__main__":
    app() 