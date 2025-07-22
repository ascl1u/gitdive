"""Git CLI wrapper for reliable git operations."""

import subprocess
from pathlib import Path
from typing import List, Optional

from rich.console import Console

console = Console()


class GitCommand:
    """Reliable git CLI wrapper with error handling."""
    
    def __init__(self, repo_path: Path):
        """Initialize with repository path."""
        self.repo_path = Path(repo_path).resolve()
    
    def run(self, args: List[str], suppress_errors: bool = False) -> str:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            if not suppress_errors:
                console.print(f"[yellow]Git command failed:[/yellow] git {' '.join(args)}")
                console.print(f"[yellow]Error:[/yellow] {e.stderr}")
            raise
        except FileNotFoundError:
            console.print("[red]Error:[/red] Git not found in PATH")
            raise
    
    def validate_repository(self) -> bool:
        """Validate that path is a valid git repository."""
        try:
            # Check if it's a git repository
            self.run(['rev-parse', '--git-dir'])
            
            # Check if it's bare (we don't support bare repos)
            result = self.run(['rev-parse', '--is-bare-repository'])
            if result.strip() == 'true':
                return False
                
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_commits(self) -> List[dict]:
        """Get all commits with metadata."""
        try:
            # Format: hash|subject|author_name|author_email|date
            format_str = '%H\x1F%s\x1F%an\x1F%ae\x1F%ai'
            output = self.run(['log', f'--format={format_str}'])
            
            commits = []
            for line in output.strip().split('\n'):
                if not line:
                    continue
                    
                parts = line.split('\x1F', 4)
                if len(parts) == 5:
                    hash_val, summary, author_name, author_email, date = parts
                    commits.append({
                        'hash': hash_val,
                        'summary': summary,
                        'author': f"{author_name} <{author_email}>",
                        'date': date
                    })
            
            return commits
        except subprocess.CalledProcessError:
            return []
    
    def get_commit_diff(self, commit_hash: str) -> str:
        """Get raw diff for a specific commit with headers for file tracking."""
        try:
            # Get raw diff with headers for file tracking
            output = self.run([
                'show', 
                '--format=',  # No commit message
                '--unified=0',  # No context lines
                commit_hash
            ])
            
            return output
        except subprocess.CalledProcessError:
            return ""
    
    def get_commit_files(self, commit_hash: str) -> List[str]:
        """Get list of files changed in a commit."""
        try:
            output = self.run(['show', '--name-only', '--format=', commit_hash])
            return [f.strip() for f in output.split('\n') if f.strip()]
        except subprocess.CalledProcessError:
            return []
    
    def is_initial_commit(self, commit_hash: str) -> bool:
        """Check if commit is the initial commit (has no parents)."""
        try:
            # Ensure we're using the full hash, trimmed of whitespace
            full_hash = commit_hash.strip()
            # Try to get parent - if it fails, it's initial commit
            # Suppress error logging since we expect this to fail for initial commits
            self.run(['rev-parse', f'{full_hash}^'], suppress_errors=True)
            return False
        except subprocess.CalledProcessError:
            return True
    
    def get_file_content_at_commit(self, commit_hash: str, file_path: str) -> str:
        """Get file content at specific commit."""
        try:
            output = self.run(['show', f'{commit_hash}:{file_path}'])
            return output
        except subprocess.CalledProcessError:
            return "" 