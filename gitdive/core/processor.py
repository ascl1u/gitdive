"""Git commit processing for GitDive."""

from typing import List

from .git_cli import GitCommand
from .models import CommitData
from .constants import COMMIT_HASH_DISPLAY_LENGTH
from .logger import Logger


class CommitProcessor:
    """Handles git commit data extraction using git CLI."""

    def __init__(self, git_cmd: GitCommand, logger: Logger):
        """Initialize with GitCommand instance and logger."""
        self.git_cmd = git_cmd
        self.logger = logger

    def extract_commits(self) -> List[CommitData]:
        """Extract all commits with their content."""
        commits_data = []

        try:
            # Get all commits metadata in one efficient call
            commits_info = self.git_cmd.get_commits()

            for commit_info in commits_info:
                commit_hash = commit_info['hash']

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
            self.logger.error(f"Error extracting commits: {str(e)}")
            return []

    def _extract_commit_content(self, commit_hash: str) -> str:
        """Extract content from a single commit using git CLI."""
        try:
            if self.git_cmd.is_initial_commit(commit_hash):
                return self._extract_initial_commit_content(commit_hash)
            else:
                return self._extract_regular_commit_content(commit_hash)
        except Exception as e:
            self.logger.error(f"Error processing commit {commit_hash[:COMMIT_HASH_DISPLAY_LENGTH]}: {str(e)}")
            return ""
    
    def _extract_initial_commit_content(self, commit_hash: str) -> str:
        """Extract content from initial commit by getting all file contents."""
        files_changed = self.git_cmd.get_commit_files(commit_hash)
        added_lines = []
        
        for file_path in files_changed:
            # File filtering will be handled by GitDiffParser during semantic parsing
            file_content = self.git_cmd.get_file_content_at_commit(commit_hash, file_path)
            if file_content:
                file_lines = file_content.split('\n')
                added_lines.extend(file_lines)
        
        return '\n'.join(added_lines)
    
    def _extract_regular_commit_content(self, commit_hash: str) -> str:
        """Extract raw diff content from regular commit for semantic parsing."""
        diff_content = self.git_cmd.get_commit_diff(commit_hash)
        
        if not diff_content:
            return ""
        
        # Return raw diff content with headers intact for proper semantic parsing
        # File filtering and content extraction will be handled by GitDiffParser
        return diff_content
