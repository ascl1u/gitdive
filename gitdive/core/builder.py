"""Document building for GitDive."""

from typing import List
import sys

from llama_index.core import Document
from llama_index.llms.ollama import Ollama
from rich.console import Console

from .models import CommitData
from .config import GitDiveConfig
from .prompts import INDEX_SUMMARIZATION_PROMPT

console = Console(force_terminal=True, file=sys.stdout)


class DocumentBuilder:
    """Handles document creation from commit data."""
    
    def __init__(self, config: GitDiveConfig):
        """Initialize with configuration for LLM summarization."""
        self.config = config
    
    def build_documents(self, commits: List[CommitData]) -> List[Document]:
        """Build LlamaIndex documents from commit data."""
        documents = []
        
        for commit_data in commits:
            doc = self._create_document(commit_data)
            documents.append(doc)
        
        return documents
    
    def _create_document(self, commit_data: CommitData) -> Document:
        """Create a single document from commit data using LLM summarization."""
        # Use LLM to create semantic summary instead of raw content
        summary = self._summarize_commit(commit_data)
        
        return Document(
            text=summary,
            metadata={
                "commit_hash": commit_data.hash,
                "author": commit_data.author,
                "date": commit_data.date
            }
        )
    
    def _summarize_commit(self, commit_data: CommitData) -> str:
        """Summarize commit using LLM for better context during ask queries."""
        try:
            # Log which model is being used for sanity check
            console.print(f"[dim]Summarizing commit {commit_data.hash[:8]} using model: {self.config.llm.model}[/dim]")
            
            # Initialize Ollama LLM with same configuration as ask command
            llm = Ollama(
                model=self.config.llm.model,
                base_url=self.config.llm.base_url,
                request_timeout=self.config.llm.timeout,
                context_window=2048,  # Limit context to prevent memory issues
                num_predict=256       # Limit response length
            )
            
            # Create prompt for commit summarization with minimal content for debugging
            prompt = INDEX_SUMMARIZATION_PROMPT.format(
                commit_hash=commit_data.hash[:8],
                commit_message=commit_data.summary,
                author=commit_data.author,
                content=commit_data.content[:200]  # Very small content for debugging
            )
            
            console.print(f"[dim]Prompt length: {len(prompt)} chars[/dim]")
            
            # Generate semantic summary
            response = llm.complete(prompt)
            return str(response)
            
        except Exception as e:
            # Fallback to truncated raw content if LLM fails
            console.print(f"[yellow]Warning:[/yellow] LLM summarization failed for commit {commit_data.hash[:8]}: {str(e)}")
            fallback = f"{commit_data.summary}\n\n{commit_data.content[:500]}"
            if len(commit_data.content) > 500:
                fallback += "..."
            return fallback 