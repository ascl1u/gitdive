"""Query service for natural language repository questions."""

from pathlib import Path
from typing import Optional
import sys

from llama_index.core import VectorStoreIndex
from llama_index.llms.ollama import Ollama
from rich.console import Console

from .config import GitDiveConfig
from .storage import StorageManager
from .timing import PipelineTimer
from .prompts import ASK_SYSTEM_PROMPT
from .constants import DEFAULT_SIMILARITY_TOP_K, TIMING_LOG_PREVIEW_LENGTH

console = Console(force_terminal=True, file=sys.stdout)


class QueryService:
    """Handles natural language queries against indexed repository data."""
    
    def __init__(self, repo_path: Path, config: GitDiveConfig):
        """Initialize query service with repository path and configuration."""
        self.repo_path = Path(repo_path).resolve()
        self.config = config
        self.storage_manager = StorageManager()
    
    def ask(self, question: str, verbose: bool = False) -> bool:
        """
        Ask a question about the repository and print the response.
        
        Args:
            question: Natural language question about repository history
            verbose: Enable detailed timing information
            
        Returns:
            bool: True if query succeeded, False if error occurred
        """
        timer = PipelineTimer(verbose)
        
        try:
            timer.start_pipeline()
            
            # Load existing index
            console.print("[dim]Loading repository index...[/dim]")
            timer.start_step("Index loading")
            index = self._load_index()
            if not index:
                console.print("[red]Error:[/red] No index found. Run 'gitdive index' first.")
                return False
            timer.end_step("Index loading")
            
            console.print("[dim]Index loaded successfully[/dim]")
            
            # Create query engine with Ollama LLM
            console.print(f"[dim]Connecting to {self.config.llm.model} at {self.config.llm.base_url}...[/dim]")
            timer.start_step("Query engine creation")
            query_engine = self._create_query_engine(index)
            if not query_engine:
                return False
            timer.end_step("Query engine creation")
            
            console.print("[dim]LLM connected, processing query...[/dim]")
            
            # Execute query with detailed timing
            console.print(f"[dim]Repository analysis (timeout: {self.config.llm.timeout}s):[/dim]")
            timer.start_step("Vector similarity search")
            
            # The query() call includes both vector search and LLM processing
            # We'll time the entire operation here
            timer.log_timing("Starting vector similarity search and LLM processing")
            timer.start_step("Vector retrieval from ChromaDB")
            
            # First, manually retrieve similar documents to see what's being sent
            retriever = index.as_retriever(similarity_top_k=DEFAULT_SIMILARITY_TOP_K)
            retrieved_nodes = retriever.retrieve(question)
            timer.end_step("Vector retrieval from ChromaDB")
            
            timer.log_timing(f"Retrieved {len(retrieved_nodes)} documents from vector store")
            for i, node in enumerate(retrieved_nodes):
                content_preview = node.text[:TIMING_LOG_PREVIEW_LENGTH] + "..." if len(node.text) > TIMING_LOG_PREVIEW_LENGTH else node.text
                timer.log_timing(f"Document {i+1}: {len(node.text)} chars - '{content_preview}'")
            
            timer.start_step("LLM query execution")
            timer.log_llamaindex_operation("Initializing query engine for LLM processing")
            
            # Log the system prompt being used
            timer.log_prompt_info("System prompt", ASK_SYSTEM_PROMPT, len(ASK_SYSTEM_PROMPT))
            
            # Log the question and context being sent
            context_text = retrieved_nodes[0].text if retrieved_nodes else "No context"
            timer.log_prompt_info("Context", context_text, len(context_text))
            timer.log_prompt_info("Question", question, len(question))
            
            timer.log_llamaindex_operation("Sending query to LLM via LlamaIndex")
            response = query_engine.query(question)
            timer.log_llamaindex_operation("LLM response received")
            timer.end_step("LLM query execution")
            timer.end_step("Vector similarity search")
            
            # Display response
            timer.start_step("Response processing")
            if response and str(response).strip():
                console.print(str(response))
            else:
                console.print("[yellow]Note:[/yellow] No relevant commits found for your question.")
            timer.end_step("Response processing")
            
            timer.end_pipeline()
            return True
            
        except Exception as e:
            timer.log_timing(f"Pipeline failed with error: {str(e)}")
            self._handle_query_error(e)
            return False
    
    def _load_index(self) -> Optional[VectorStoreIndex]:
        """Load existing index using StorageManager."""
        return self.storage_manager.load_existing_index(self.repo_path)
    
    def _create_query_engine(self, index: VectorStoreIndex):
        """Create query engine with Ollama LLM configuration."""
        try:
            # Initialize Ollama LLM with consistent configuration
            llm = self.config.create_ollama_llm()
            
            # Create query engine with minimal context for maximum speed
            query_engine = index.as_query_engine(
                llm=llm,
                system_prompt=ASK_SYSTEM_PROMPT,
                similarity_top_k=DEFAULT_SIMILARITY_TOP_K
            )
            
            return query_engine
            
        except Exception as e:
            if "Connection" in str(e) or "timeout" in str(e).lower():
                console.print(f"[red]Error:[/red] Cannot connect to Ollama at {self.config.llm.base_url}")
            else:
                console.print(f"[red]Error:[/red] Failed to initialize LLM: {str(e)}")
            return None
    
    def _handle_query_error(self, error: Exception):
        """Handle query errors with consistent theming."""
        error_msg = str(error)
        
        if "Connection" in error_msg or "timeout" in error_msg.lower():
            console.print(f"[red]Error:[/red] Cannot connect to Ollama at {self.config.llm.base_url}")
        elif "index" in error_msg.lower():
            console.print("[red]Error:[/red] Index loading failed. Try re-running 'gitdive index'.")
        else:
            console.print(f"[red]Error:[/red] Query processing failed: {error_msg}") 