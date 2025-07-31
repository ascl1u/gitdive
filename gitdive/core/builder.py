"""Document building for GitDive."""

from typing import List

from llama_index.core import Document

from .models import CommitData

class DocumentBuilder:
    """Handles document creation from commit data using raw content indexing."""
    
    def __init__(self, config=None):
        """Initialize document builder. Config no longer needed for raw indexing."""
        pass
    
    def build_documents(self, commits: List[CommitData]) -> List[Document]:
        """Build LlamaIndex documents from commit data using raw content."""
        documents = []
        
        for commit_data in commits:
            doc = self._create_document(commit_data)
            documents.append(doc)
        
        return documents
    
    def _create_document(self, commit_data: CommitData) -> Document:
        """Create a document with raw git diff content and rich metadata."""
        # Create structured content preserving git semantics
        content = f"""Commit: {commit_data.hash[:8]}
Author: {commit_data.author}
Date: {commit_data.date}
Message: {commit_data.summary}

Changes:
{commit_data.content}"""
        
        return Document(
            text=content,
            metadata={
                "commit_hash": commit_data.hash,
                "commit_short_hash": commit_data.hash[:8],
                "author": commit_data.author,
                "date": commit_data.date,
                "summary": commit_data.summary,
                "content_length": len(commit_data.content)
            }
        ) 