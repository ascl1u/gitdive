"""Progress reporting for GitDive."""

from pathlib import Path
from .logger import Logger


class ProgressReporter:
    """Handles user progress feedback."""

    def __init__(self, logger: Logger):
        """Initialize with a logger instance."""
        self.logger = logger

    def report_start(self, repo_path: Path):
        """Report indexing start."""
        self.logger.info(f"[green]Indexing repository:[/green] {repo_path}")

    def report_commits_found(self, count: int):
        """Report number of commits found."""
        if count == 0:
            self.logger.info("[yellow]Warning:[/yellow] No commits found in repository.")
        else:
            self.logger.info(f"[blue]Found {count} commits with indexable content[/blue]")

    def report_completion(self, count: int, storage_path: Path):
        """Report indexing completion."""
        if count > 0:
            self.logger.info(f"[green]✓[/green] Successfully indexed {count} commits to ChromaDB")
            self.logger.debug(f"Storage location: {storage_path}")
        else:
            self.logger.info("[yellow]Warning:[/yellow] No commits contained indexable content.")
