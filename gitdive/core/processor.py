"""Git commit processing for GitDive."""

from typing import List
import sys

from rich.console import Console

from .git_cli import GitCommand
from .models import CommitData
from .constants import FILE_SIZE_LIMIT, COMMIT_HASH_DISPLAY_LENGTH, IGNORE_FILE_PATTERNS

console = Console(force_terminal=True, file=sys.stdout)


class CommitProcessor:
    """Handles git commit data extraction using git CLI."""
    
    def __init__(self, git_cmd: GitCommand):
        """Initialize with GitCommand instance."""
        self.git_cmd = git_cmd
        self.progress_callback = None
    
    def set_progress_callback(self, callback):
        """Set callback for progress updates."""
        self.progress_callback = callback
    
    def extract_commits(self) -> List[CommitData]:
        """Extract all commits with their content."""
        commits_data = []
        
        try:
            # Get all commits metadata in one efficient call
            commits_info = self.git_cmd.get_commits()
            total_commits_processed = len(commits_info)
            
            for i, commit_info in enumerate(commits_info, 1):
                commit_hash = commit_info['hash']
                
                # Show progress dot
                if self.progress_callback:
                    self.progress_callback()
                
                # Extract content using git CLI
                content = self._extract_commit_content(commit_hash)
                
                if content.strip():  # Only include commits with actual content
                    commit_data = CommitData(
                        hash=commit_hash,
                        summary=commit_info['summary'],
                        author=commit_info['author'],
                        date=commit_info['date'],
                        content=content
                    )
                    commits_data.append(commit_data)
            
            return commits_data
        except Exception as e:
            console.print(f"[red]Error extracting commits:[/red] {str(e)}")
            return []
    
    def _extract_commit_content(self, commit_hash: str) -> str:
        """Extract content from a single commit using git CLI."""
        try:
            if self.git_cmd.is_initial_commit(commit_hash):
                return self._extract_initial_commit_content(commit_hash)
            else:
                return self._extract_regular_commit_content(commit_hash)
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Error processing commit {commit_hash[:COMMIT_HASH_DISPLAY_LENGTH]}: {str(e)}")
            return ""
    
    def _extract_initial_commit_content(self, commit_hash: str) -> str:
        """Extract content from initial commit by getting all file contents."""
        files_changed = self.git_cmd.get_commit_files(commit_hash)
        added_lines = []
        
        for file_path in files_changed:
            if not self._should_include_file(file_path):
                continue
            
            file_content = self.git_cmd.get_file_content_at_commit(commit_hash, file_path)
            if file_content:
                file_content = file_content[:FILE_SIZE_LIMIT]  # Size limit per file
                file_lines = file_content.split('\n')
                added_lines.extend(file_lines)
        
        return '\n'.join(added_lines)
    
    def _extract_regular_commit_content(self, commit_hash: str) -> str:
        """Extract content from regular commit by processing diff."""
        diff_content = self.git_cmd.get_commit_diff(commit_hash)
        
        if not diff_content:
            return ""
        
        # Apply file filtering to the diff content
        filtered_lines = []
        current_file = None
        
        for line in diff_content.split('\n'):
            # Track which file we're in based on diff headers
            if line.startswith('diff --git'):
                # Extract file path from diff header
                # Format: diff --git a/path/file.py b/path/file.py
                parts = line.split(' ')
                if len(parts) >= 4:
                    # Use the 'b/' version (after changes) and remove prefix
                    file_with_prefix = parts[3]  # b/path/file.py
                    if file_with_prefix.startswith('b/'):
                        current_file = file_with_prefix[2:]  # Remove 'b/' prefix
                    elif file_with_prefix.startswith('a/'):
                        current_file = file_with_prefix[2:]  # Remove 'a/' prefix  
                    else:
                        current_file = file_with_prefix  # No prefix
            elif current_file and self._should_include_file(current_file):
                # Only extract added lines (+ lines) from the diff
                if line.startswith('+') and not line.startswith('+++'):
                    filtered_lines.append(line[1:])  # Remove + prefix
        
        return '\n'.join(filtered_lines)
    
    def _should_include_file(self, file_path: str) -> bool:
        """Simple file filtering for indexing."""
        if not file_path:
            return False
        
        for pattern in IGNORE_FILE_PATTERNS:
            if pattern in file_path:
                return False
        
        return True 