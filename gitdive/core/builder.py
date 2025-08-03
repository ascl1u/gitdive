"""Document building for GitDive."""

from typing import List

from llama_index.core import Document

from .models import CommitData
from .diff_parser import GitDiffParser
from .logger import Logger

class DocumentBuilder:
    """Handles document creation from commit data using semantic content indexing."""

    def __init__(self, logger: Logger):
        """Initialize document builder with diff parser for semantic content extraction."""
        self.diff_parser = GitDiffParser(logger)
    
    def build_documents(self, commits: List[CommitData]) -> List[Document]:
        """Build LlamaIndex documents from commit data using semantic content."""
        documents = []
        
        for commit_data in commits:
            doc = self._create_document(commit_data)
            documents.append(doc)
        
        return documents
    
    def _create_document(self, commit_data: CommitData) -> Document:
        """
        Create a LlamaIndex Document from commit data.
        The document's text is the raw diff, and the metadata contains
        the semantic summary.
        """
        # The raw diff content is the primary text for indexing
        content = commit_data.content
        
        # The semantic summary is stored in the metadata
        changes = self.diff_parser.parse_structural_changes(content)
        
        return Document(
            text=content,
            metadata={
                "commit_hash": commit_data.hash,
                "commit_short_hash": commit_data.hash[:8],
                "author": commit_data.author,
                "date": commit_data.date,
                "summary": commit_data.summary,
                "added_functions": ", ".join(changes.added_functions),
                "removed_functions": ", ".join(changes.removed_functions),
                "modified_files": ", ".join(changes.modified_files),
                "lines_added": changes.lines_added,
                "lines_removed": changes.lines_removed,
            },
            # The summary provides a quick human-readable overview
            # but is not the primary content for the LLM
            excluded_llm_metadata_keys=["summary"]
        )
