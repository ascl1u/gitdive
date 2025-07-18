"""Git repository indexer"""

from pathlib import Path

import git
from rich.console import Console

console = Console()


class GitIndexer:
    """Handles git repository indexing with safety controls and time filtering."""
    
    def __init__(self, repo_path: Path):
        """Initialize indexer with repository path."""
        self.repo_path = Path(repo_path).resolve()
        self.repo = None
        
    def validate_repository(self) -> bool:
        """
        Validate repository access and implement access control.
        
        Returns:
            bool: True if repository is valid and accessible
        """
        try:
            # Check if path exists and is a directory
            if not self.repo_path.exists() or not self.repo_path.is_dir():
                console.print(f"[red]Error:[/red] Path does not exist or is not a directory: {self.repo_path}")
                return False
            
            # Prevent indexing .git directories directly
            if self.repo_path.name == '.git':
                console.print("[red]Error:[/red] Cannot index .git directory directly. Use the repository root.")
                return False
            
            # Check if it's inside a .git directory
            if '.git' in self.repo_path.parts:
                console.print("[red]Error:[/red] Cannot index paths inside .git directory.")
                return False
            
            # Try to open as git repository
            self.repo = git.Repo(self.repo_path)
            
            # Additional safety check - ensure we have a valid repo
            if self.repo.bare:
                console.print("[red]Error:[/red] Bare repositories are not supported.")
                return False
                
            return True
            
        except git.InvalidGitRepositoryError:
            console.print("[red]Error:[/red] Not a valid git repository.")
            return False
        except git.NoSuchPathError:
            console.print("[red]Error:[/red] Repository path does not exist.")
            return False
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to validate repository: {str(e)}")
            return False
    
# TODO: Time-based filtering will be implemented in Phase 2
    
    def index_repository(self) -> bool:
        """
        Index the repository (Phase 1: basic structure only).
        
        Returns:
            bool: True if indexing succeeded
        """
        try:
            if not self.repo:
                console.print("[red]Error:[/red] Repository not validated. Call validate_repository() first.")
                return False
            
            # Get basic commit list (no filtering in Phase 1)
            commits = self._get_commits()
            
            if not commits:
                console.print("[yellow]Warning:[/yellow] No commits found in repository.")
                return True
            
            console.print(f"[blue]Found {len(commits)} commits to index[/blue]")
            
            # TODO: Phase 2 - Implement actual indexing logic
            # For now, just simulate the process
            for i, commit in enumerate(commits[:5], 1):  # Show first 5 commits only
                console.print(f"[dim]Processing commit {i}: {commit.hexsha[:8]} - {commit.summary}[/dim]")
                # In Phase 2, this will extract diffs and create documents
            
            if len(commits) > 5:
                console.print(f"[dim]... and {len(commits) - 5} more commits[/dim]")
            
            console.print("[green]✓[/green] Repository validation and basic indexing structure completed")
            return True
            
        except Exception as e:
            console.print(f"[red]Error during indexing:[/red] {str(e)}")
            return False
    
    def _get_commits(self) -> list:
        """Get basic list of commits (Phase 1: no filtering)."""
        try:
            commits = []
            
            # Get all commits from the default branch
            for commit in self.repo.iter_commits():
                commits.append(commit)
            
            return commits
            
        except Exception as e:
            console.print(f"[red]Error getting commits:[/red] {str(e)}")
            return [] 