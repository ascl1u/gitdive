"""Progress reporting for GitDive."""

from pathlib import Path
import sys

from rich.console import Console

console = Console(force_terminal=True, file=sys.stdout)


class ProgressReporter:
    """Handles user progress feedback."""
    
    def __init__(self):
        self.dots_printed = 0
    
    def report_start(self, repo_path: Path):
        """Report indexing start."""
        console.print(f"[green]Indexing repository:[/green] {repo_path}")
    
    def report_commits_found(self, count: int):
        """Report number of commits found."""
        if count == 0:
            console.print("[yellow]Warning:[/yellow] No commits found in repository.")
        else:
            console.print(f"[blue]Found {count} commits with indexable content[/blue]")
            console.print("Processing commits ", end="")
            console.file.flush()  # Force immediate output
            self.dots_printed = 0
    
    def report_commit_progress(self):
        """Show a single dot for commit progress."""
        console.print(".", end="")
        console.file.flush()  # Force immediate output
        self.dots_printed += 1
        
        # Add line break every 50 dots for readability
        if self.dots_printed % 50 == 0:
            console.print()
    
    def report_processing_commit(self, commit_hash: str, summary: str, position: int):
        """Report individual commit processing (for first few)."""
        if position <= 5:
            console.print(f"[dim]Processed commit: {commit_hash[:8]} - {summary}[/dim]")
    
    def report_completion(self, count: int, storage_path: Path):
        """Report indexing completion."""
        # Add final line break if we printed dots
        if self.dots_printed > 0:
            console.print()  # New line after dots
        
        if count > 0:
            console.print(f"[green]✓[/green] Successfully indexed {count} commits to ChromaDB")
            console.print(f"[dim]Storage location: {storage_path}[/dim]")
        else:
            console.print("[yellow]Warning:[/yellow] No commits contained indexable content.") 