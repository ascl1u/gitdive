"""Git diff parser for extracting structural changes."""

import re
from typing import List, Set

from .models import StructuralChanges
from .constants import IGNORE_FILE_PATTERNS
from .logger import Logger


class GitDiffParser:
    """Parses git diffs to extract semantic structural changes."""

    def __init__(self, logger: Logger):
        """Initialize parser with regex patterns for common code structures."""
        self.logger = logger
        # Function patterns for multiple languages
        self.function_patterns = [
            r'^[+-]\s*def\s+(\w+)\s*\(',  # Python
            r'^[+-]\s*function\s+(\w+)\s*\(',  # JavaScript
            r'^[+-]\s*(\w+)\s*\([^)]*\)\s*{',  # C/Java style
            r'^[+-]\s*public\s+\w+\s+(\w+)\s*\(',  # Java methods
            r'^[+-]\s*private\s+\w+\s+(\w+)\s*\(',  # Java private methods
        ]

        # Class patterns for multiple languages
        self.class_patterns = [
            r'^[+-]\s*class\s+(\w+)(?:\s*\([^)]*\))?\s*:',  # Python
            r'^[+-]\s*class\s+(\w+)\s*{',  # C++/Java
            r'^[+-]\s*public\s+class\s+(\w+)',  # Java public class
        ]

        # File pattern for tracking modifications
        self.file_pattern = r'^diff --git a/(.+?) b/(.+?)$'

    def parse_structural_changes(self, diff_content: str) -> StructuralChanges:
        """
        Parse git diff content into semantic structural changes.
        
        Args:
            diff_content: Raw git diff output
            
        Returns:
            StructuralChanges with parsed semantic information
        """
        if not diff_content or not diff_content.strip():
            return self._empty_changes()

        try:
            return self._parse_diff_safely(diff_content)
        except Exception as e:
            self.logger.error(f"Diff parsing failed ({str(e)}), using basic analysis")
            return self._fallback_parse(diff_content)

    def _parse_diff_safely(self, diff_content: str) -> StructuralChanges:
        """Parse diff content with comprehensive structural analysis and file filtering."""
        lines = diff_content.split('\n')

        added_functions: Set[str] = set()
        removed_functions: Set[str] = set()
        modified_functions: Set[str] = set()
        added_classes: Set[str] = set()
        removed_classes: Set[str] = set()
        modified_files: Set[str] = set()
        lines_added = 0
        lines_removed = 0

        current_file = None
        should_include_current_file = False

        for line in lines:
            # Track file changes
            file_match = re.match(self.file_pattern, line)
            if file_match:
                current_file = file_match.group(2)
                should_include_current_file = current_file and self._should_include_file(current_file)
                if should_include_current_file:
                    modified_files.add(current_file)
                continue

            # Only process lines from files we want to include
            if not should_include_current_file:
                continue

            # Count line changes
            if line.startswith('+') and not line.startswith('+++'):
                lines_added += 1
            elif line.startswith('-') and not line.startswith('---'):
                lines_removed += 1

            # Parse structural changes
            self._parse_functions(line, added_functions, removed_functions, modified_functions)
            self._parse_classes(line, added_classes, removed_classes)

        # Log parsing results
        total_items = len(added_functions) + len(removed_functions) + len(added_classes) + len(removed_classes)
        self.logger.debug(f"Parsed structural changes: {total_items} items from {len(modified_files)} files (+{lines_added}/-{lines_removed} lines)")

        return StructuralChanges(
            added_functions=list(added_functions),
            removed_functions=list(removed_functions),
            modified_functions=list(modified_functions),
            added_classes=list(added_classes),
            removed_classes=list(removed_classes),
            modified_files=list(modified_files),
            lines_added=lines_added,
            lines_removed=lines_removed
        )
    
    def _parse_functions(self, line: str, added: Set[str], removed: Set[str], modified: Set[str]):
        """Parse function definitions from diff line."""
        for pattern in self.function_patterns:
            match = re.match(pattern, line)
            if match:
                function_name = match.group(1)
                if line.startswith('+'):
                    added.add(function_name)
                elif line.startswith('-'):
                    removed.add(function_name)
                    # If function appears in both added and removed, it's modified
                    if function_name in added:
                        modified.add(function_name)
                        added.discard(function_name)
                        removed.discard(function_name)
                break
    
    def _parse_classes(self, line: str, added: Set[str], removed: Set[str]):
        """Parse class definitions from diff line."""
        for pattern in self.class_patterns:
            match = re.match(pattern, line)
            if match:
                class_name = match.group(1)
                if line.startswith('+'):
                    added.add(class_name)
                elif line.startswith('-'):
                    removed.add(class_name)
                break
    
    def _should_include_file(self, file_path: str) -> bool:
        """Apply file filtering to determine if a file should be indexed."""
        if not file_path:
            return False
        
        for pattern in IGNORE_FILE_PATTERNS:
            if pattern in file_path:
                return False
        
        return True
    
    def _fallback_parse(self, diff_content: str) -> StructuralChanges:
        """Simple fallback parsing with file filtering for when detailed parsing fails."""
        lines = diff_content.split('\n')

        modified_files = set()
        lines_added = 0
        lines_removed = 0
        current_file = None
        should_include_current_file = False

        for line in lines:
            # Basic file tracking with filtering
            if line.startswith('diff --git'):
                parts = line.split()
                if len(parts) >= 4:
                    file_path = parts[3].replace('b/', '', 1)
                    current_file = file_path
                    should_include_current_file = self._should_include_file(file_path)
                    if should_include_current_file:
                        modified_files.add(file_path)

            # Only count lines from included files
            elif should_include_current_file:
                if line.startswith('+') and not line.startswith('+++'):
                    lines_added += 1
                elif line.startswith('-') and not line.startswith('---'):
                    lines_removed += 1

        self.logger.debug(f"Fallback parsing: {len(modified_files)} files, +{lines_added}/-{lines_removed} lines")

        return StructuralChanges(
            added_functions=[],
            removed_functions=[],
            modified_functions=[],
            added_classes=[],
            removed_classes=[],
            modified_files=list(modified_files),
            lines_added=lines_added,
            lines_removed=lines_removed
        )

    def _empty_changes(self) -> StructuralChanges:
        """Return empty structural changes for null/empty diff content."""
        return StructuralChanges(
            added_functions=[],
            removed_functions=[],
            modified_functions=[],
            added_classes=[],
            removed_classes=[],
            modified_files=[],
            lines_added=0,
            lines_removed=0
        )
