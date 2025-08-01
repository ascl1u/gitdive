"""Document building for GitDive."""

from typing import List

from llama_index.core import Document

from .models import CommitData, StructuralChanges
from .diff_parser import GitDiffParser

class DocumentBuilder:
    """Handles document creation from commit data using semantic content indexing."""
    
    def __init__(self, config=None):
        """Initialize document builder with diff parser for semantic content extraction."""
        self.diff_parser = GitDiffParser()
    
    def build_documents(self, commits: List[CommitData]) -> List[Document]:
        """Build LlamaIndex documents from commit data using semantic content."""
        documents = []
        
        for commit_data in commits:
            doc = self._create_document(commit_data)
            documents.append(doc)
        
        return documents
    
    def _create_document(self, commit_data: CommitData) -> Document:
        """Create a document with semantic content extracted from git diff."""
        # Parse raw git diff content into structural changes with integrated file filtering
        changes = self.diff_parser.parse_structural_changes(commit_data.content)
        
        # Create clean, semantic content for better LLM understanding
        content = self._format_semantic_content(commit_data, changes)
        
        return Document(
            text=content,
            metadata={
                "commit_hash": commit_data.hash,
                "commit_short_hash": commit_data.hash[:8],
                "author": commit_data.author,
                "date": commit_data.date,
                "summary": commit_data.summary,
                "added_functions": len(changes.added_functions),
                "removed_functions": len(changes.removed_functions),
                "modified_files": len(changes.modified_files),
                "lines_added": changes.lines_added,
                "lines_removed": changes.lines_removed
            }
        )
    
    def _format_semantic_content(self, commit_data: CommitData, changes: StructuralChanges) -> str:
        """Format structural changes into clean, searchable content."""
        content_parts = [
            f"Commit {commit_data.hash[:8]}: {commit_data.summary}",
            f"Author: {commit_data.author}",
            f"Date: {commit_data.date}",
            ""
        ]
        
        # Add structural changes in a clean, LLM-friendly format
        if changes.added_functions:
            content_parts.append(f"Added Functions: {', '.join(changes.added_functions)}")
        
        if changes.removed_functions:
            content_parts.append(f"Removed Functions: {', '.join(changes.removed_functions)}")
        
        if changes.modified_functions:
            content_parts.append(f"Modified Functions: {', '.join(changes.modified_functions)}")
        
        if changes.added_classes:
            content_parts.append(f"Added Classes: {', '.join(changes.added_classes)}")
        
        if changes.removed_classes:
            content_parts.append(f"Removed Classes: {', '.join(changes.removed_classes)}")
        
        if changes.modified_files:
            content_parts.append(f"Modified Files: {', '.join(changes.modified_files)}")
        
        # Add quantitative summary
        if changes.lines_added or changes.lines_removed:
            content_parts.append(f"Code Changes: +{changes.lines_added} lines, -{changes.lines_removed} lines")
        
        # Add a summary if we have structural changes
        if any([changes.added_functions, changes.removed_functions, changes.added_classes, 
                changes.removed_classes, changes.modified_files]):
            change_summary = self._generate_change_summary(changes)
            content_parts.append(f"Summary: {change_summary}")
        
        return "\n".join(content_parts)
    
    def _generate_change_summary(self, changes: StructuralChanges) -> str:
        """Generate a brief summary of the structural changes."""
        summary_parts = []
        
        total_functions = len(changes.added_functions) + len(changes.removed_functions) + len(changes.modified_functions)
        total_classes = len(changes.added_classes) + len(changes.removed_classes)
        
        if total_functions > 0:
            summary_parts.append(f"{total_functions} function changes")
        
        if total_classes > 0:
            summary_parts.append(f"{total_classes} class changes")
        
        if changes.modified_files:
            summary_parts.append(f"{len(changes.modified_files)} files modified")
        
        if not summary_parts:
            summary_parts.append("code modifications")
        
        return ", ".join(summary_parts)
