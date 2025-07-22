"""Document building for GitDive."""

from typing import List

from llama_index.core import Document

from .models import CommitData


class DocumentBuilder:
    """Handles document creation from commit data."""
    
    def build_documents(self, commits: List[CommitData]) -> List[Document]:
        """Build LlamaIndex documents from commit data."""
        documents = []
        
        for commit_data in commits:
            doc = self._create_document(commit_data)
            documents.append(doc)
        
        return documents
    
    def _create_document(self, commit_data: CommitData) -> Document:
        """Create a single document from commit data."""
        # Combine commit message and content for better search
        full_text = f"{commit_data.summary}\n\n{commit_data.content}"
        
        return Document(
            text=full_text,
            metadata={
                "commit_hash": commit_data.hash,
                "author": commit_data.author,
                "date": commit_data.date
            }
        ) 