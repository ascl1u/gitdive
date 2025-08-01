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

    def __init__(
        self,
        repo_path: Path,
        config: GitDiveConfig,
        storage_manager: StorageManager,
    ):
        """Initialize query service with repository path and configuration."""
        self.repo_path = Path(repo_path).resolve()
        self.config = config
        self.storage_manager = storage_manager
        self.embed_model = self.storage_manager.embed_model
    
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
            timer.start_step("Query execution")
            
            timer.log_prompt_info("User question", question, len(question))
            
            # Retrieve context from vector store
            timer.log_llamaindex_operation("Retrieving context from vector store")
            retriever = query_engine.retriever
            nodes = retriever.retrieve(question)
            
            if nodes:
                timer.log_processing_stats("Retrieved context", len(nodes), sum(len(n.get_content()) for n in nodes))
                for i, node in enumerate(nodes):
                    timer.log_timing(f"  - Node {i+1}: score={node.score:.2f}, len={len(node.get_content())}")
            else:
                timer.log_timing("No context retrieved from vector store")

            timer.log_timing("Starting RAG query via LlamaIndex")
            timer.log_llamaindex_operation("Executing query engine with streaming enabled")
            
            # Use query engine with optimized RAG pipeline
            response = query_engine.query(question)
            
            timer.log_llamaindex_operation("LLM response received")
            
            # Diagnostic: Log response for analysis
            response_str = str(response)
            timer.log_timing(f"Response length: {len(response_str)} chars")
            response_preview = response_str[:200] + "..." if len(response_str) > 200 else response_str
            timer.log_timing(f"Response preview: '{response_preview}'")
            
            timer.end_step("Query execution")
            
            # Display response with enhanced analysis for semantic content
            timer.start_step("Response processing")
            if response and str(response).strip():
                response_text = str(response)
                
                # Enhanced analysis for semantic content verification
                timer.log_timing(f"Final response analysis:")
                timer.log_timing(f"  - Response quality: {'Good' if len(response_text) > 100 else 'Brief'}")
                
                # Check if response references multiple sources (commits/documents)
                commit_refs = response_text.count('commit') + response_text.count('hash')
                timer.log_timing(f"  - Commit references found: {commit_refs}")
                
                # Display the actual response
                console.print(response_text)
                
                # Summary of query execution results
                timer.log_timing(f"Query execution summary:")
                timer.log_timing(f"  - Response: {len(response_text)} chars")
                timer.log_timing(f"  - Multi-doc evidence: {commit_refs} commit references")
                
            else:
                console.print("[yellow]Note:[/yellow] No relevant commits found for your question.")
                timer.log_timing("Empty or null response received")
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
        """Create query engine with Ollama LLM configuration and multi-document support."""
        try:
            # Initialize Ollama LLM with consistent configuration
            llm = self.config.create_ollama_llm()
            
            # Create query engine optimized for multi-document processing
            query_engine = index.as_query_engine(
                llm=llm,
                embed_model=self.embed_model,
                system_prompt=ASK_SYSTEM_PROMPT,
                similarity_top_k=DEFAULT_SIMILARITY_TOP_K,
                response_mode="compact",  # Combines multiple documents intelligently
                streaming=True,  # Re-enabled for performance
                verbose=False  # Reduce noise in output
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
