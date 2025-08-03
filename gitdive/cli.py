"""Main CLI application for GitDive."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed timing information"),
):
    """Index git repository history for natural language queries."""
    from .core.indexer import GitIndexer
    from .core.config import GitDiveConfig
    from .core.storage import StorageManager
    from .core.git_cli import GitCommand
    from .core.processor import CommitProcessor
    from .core.builder import DocumentBuilder
    from .core.logger import Logger

    # Set default path to current directory
    repo_path = Path(path) if path else Path.cwd()

    # Centralized dependency creation
    logger = Logger(verbose)
    config = GitDiveConfig.default()
    embed_model = config.create_ollama_embedding()
    storage_manager = StorageManager(config, embed_model, logger)
    git_cmd = GitCommand(repo_path, logger)
    commit_processor = CommitProcessor(git_cmd, logger)
    document_builder = DocumentBuilder(logger)

    indexer = GitIndexer(
        repo_path,
        storage_manager,
        commit_processor,
        document_builder,
        logger,
    )

    # Validate repository access
    if not indexer.validate_repository():
        raise typer.Exit(1)

    # Start indexing process
    success = indexer.index_repository()

    if success:
        logger.info("[green]✓[/green] Repository indexed successfully")
    else:
        logger.error("Indexing failed")
        raise typer.Exit(1)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question about the repository history"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed timing information"),
):
    """Ask questions about the repository history using natural language."""
    from .core.query import QueryService
    from .core.config import GitDiveConfig
    from .core.storage import StorageManager
    from .core.logger import Logger

    # Centralized dependency creation
    logger = Logger(verbose)
    config = GitDiveConfig.default()
    embed_model = config.create_ollama_embedding()
    storage_manager = StorageManager(config, embed_model, logger)

    # Echo question with consistent theming
    logger.info(f"[blue]Question:[/blue] {question}")

    # Process query
    query_service = QueryService(Path.cwd(), config, storage_manager, logger)
    success = query_service.ask(question)

    if not success:
        raise typer.Exit(1)


@app.command()
def cleanup():
    """Clean up stored indexes and temporary files."""
    from .core.git_cli import GitCommand
    from .core.storage import StorageManager
    from .core.config import GitDiveConfig
    from .core.logger import Logger

    # Use current directory as repository path
    repo_path = Path.cwd()
    logger = Logger()

    # Validate repository access
    git_cmd = GitCommand(repo_path, logger)
    if not git_cmd.validate_repository():
        logger.error("Invalid or inaccessible git repository")
        raise typer.Exit(1)

    # Ask for user confirmation
    if not typer.confirm(f"Delete index for repository: {repo_path}?"):
        logger.info("[blue]Cleanup cancelled[/blue]")
        raise typer.Exit(0)

    # Perform cleanup
    config = GitDiveConfig.default()
    embed_model = config.create_ollama_embedding()
    storage_manager = StorageManager(config, embed_model, logger)
    success, message, cleaned_path = storage_manager.cleanup_repository_index(repo_path)

    if success:
        if cleaned_path:
            logger.info(f"[green]✓[/green] {message}")
            logger.info(f"[dim]Removed: {cleaned_path}[/dim]")
        else:
            logger.info(f"[blue]{message}[/blue]")
    else:
        logger.error(message)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
