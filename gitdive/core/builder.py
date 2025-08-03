"""Document building for GitDive."""

from typing import List

from llama_index.core import Document

from .models import CommitData, DiffHunk
from .diff_parser import GitDiffParser
from .logger import Logger


class DocumentBuilder:
    """Handles document creation from commit data using semantic content indexing."""

    def __init__(self, logger: Logger):
        """Initialize document builder with diff parser for semantic content extraction."""
        self.diff_parser = GitDiffParser(logger)

    def build_documents(self, commits: List[CommitData]) -> List[Document]:
        """Build LlamaIndex documents from commit data by splitting changes into granular hunks."""
        documents = []
        for commit_data in commits:
            hunks = self.diff_parser.split_diff_into_hunks(commit_data.content)
            for hunk in hunks:
                doc = self._create_document_from_hunk(commit_data, hunk)
                documents.append(doc)

        return documents

    def _create_document_from_hunk(self, commit_data: CommitData, hunk: DiffHunk) -> Document:
        """
        Create a LlamaIndex Document from a single diff hunk, with enriched text for embedding.
        """
        # Create a semantic, human-readable description of the change for embedding
        enriched_text = (
            f"Commit: {commit_data.hash[:8]} - {commit_data.summary}\n"
            f"Author: {commit_data.author}\n"
            f"Date: {commit_data.date}\n"
            f"File: {hunk.file_path}\n"
            f"Change:\n{hunk.content}"
        )

        # The raw hunk content is stored in the metadata for reference
        return Document(
            text=enriched_text,
            metadata={
                "commit_hash": commit_data.hash,
                "commit_short_hash": commit_data.hash[:8],
                "author": commit_data.author,
                "date": commit_data.date,
                "summary": commit_data.summary,
                "file_path": hunk.file_path,
                "raw_hunk": hunk.content,
            },
            # Exclude raw hunk and summary from LLM prompt to save tokens
            excluded_llm_metadata_keys=["raw_hunk", "summary"]
        )
