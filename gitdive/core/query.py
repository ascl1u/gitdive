"""Query service for natural language repository questions."""

from pathlib import Path
from typing import Optional

from llama_index.core import VectorStoreIndex

from .config import GitDiveConfig
from .storage import StorageManager
from .timing import PipelineTimer
from .prompts import ASK_SYSTEM_PROMPT
from .constants import DEFAULT_SIMILARITY_TOP_K
from .logger import Logger


class QueryService:
    """Handles natural language queries against indexed repository data."""

    def __init__(
        self,
        repo_path: Path,
        config: GitDiveConfig,
        storage_manager: StorageManager,
        logger: Logger,
    ):
        """Initialize query service with repository path and configuration."""
        self.repo_path = Path(repo_path).resolve()
        self.config = config
        self.storage_manager = storage_manager
        self.logger = logger
        self.embed_model = self.storage_manager.embed_model
        self.storage_manager.logger = logger

    def ask(self, question: str) -> bool:
        """
        Ask a question about the repository and print the response.
        
        Args:
            question: Natural language question about repository history
            
        Returns:
            bool: True if query succeeded, False if error occurred
        """
        timer = PipelineTimer(self.logger)

        try:
            with timer.pipeline("Total query pipeline"):
                self.logger.debug("Loading repository index...")
                with self.logger.timing("Index loading"):
                    index = self._load_index()
                    if not index:
                        self.logger.error("No index found. Run 'gitdive index' first.")
                        return False
                self.logger.debug("Index loaded successfully")

                self.logger.debug(f"Connecting to {self.config.llm.model} at {self.config.llm.base_url}...")
                with self.logger.timing("Query engine creation"):
                    query_engine = self._create_query_engine(index)
                    if not query_engine:
                        return False
                self.logger.debug("LLM connected, processing query...")

                with self.logger.timing("Query execution"):
                    response = query_engine.query(question)

                with self.logger.timing("Response processing"):
                    if response and str(response).strip():
                        self.logger.info(str(response))
                    else:
                        self.logger.info("[yellow]Note:[/yellow] No relevant commits found for your question.")

            return True

        except Exception as e:
            self._handle_query_error(e)
            return False

    def _load_index(self) -> Optional[VectorStoreIndex]:
        """Load existing index using StorageManager."""
        return self.storage_manager.load_existing_index(self.repo_path)

    def _create_query_engine(self, index: VectorStoreIndex):
        """Create query engine with Ollama LLM configuration and multi-document support."""
        try:
            llm = self.config.create_ollama_llm()
            return index.as_query_engine(
                llm=llm,
                embed_model=self.embed_model,
                system_prompt=ASK_SYSTEM_PROMPT,
                similarity_top_k=DEFAULT_SIMILARITY_TOP_K,
                response_mode="compact",
                streaming=True,
                verbose=False,
            )
        except Exception as e:
            if "Connection" in str(e) or "timeout" in str(e).lower():
                self.logger.error(f"Cannot connect to Ollama at {self.config.llm.base_url}")
            else:
                self.logger.error(f"Failed to initialize LLM: {str(e)}")
            return None

    def _handle_query_error(self, error: Exception):
        """Handle query errors with consistent theming."""
        error_msg = str(error)
        if "Connection" in error_msg or "timeout" in error_msg.lower():
            self.logger.error(f"Cannot connect to Ollama at {self.config.llm.base_url}")
        elif "index" in error_msg.lower():
            self.logger.error("Index loading failed. Try re-running 'gitdive index'.")
        else:
            self.logger.error(f"Query processing failed: {error_msg}")
