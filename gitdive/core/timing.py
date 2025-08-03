"""Timing utility for debugging GitDive pipeline performance."""

from contextlib import contextmanager
import logging
from .logger import Logger


class PipelineTimer:
    """Simple timing utility for measuring pipeline performance."""

    def __init__(self, logger: Logger):
        """Initialize timer with a logger instance."""
        self.logger = logger

        # Enable LlamaIndex debug logging when verbose
        if self.logger.verbose:
            self._enable_llamaindex_logging()

    @contextmanager
    def pipeline(self, description: str):
        """Context manager for timing an entire pipeline."""
        with self.logger.timing(description):
            yield

    def log_processing_stats(self, operation: str, count: int, total_size: int = 0):
        """Log processing statistics."""
        size_info = f", {total_size} total chars" if total_size > 0 else ""
        self.logger.debug(f"{operation} - processed {count} items{size_info}")

    def _enable_llamaindex_logging(self):
        """Enable LlamaIndex debug logging for verbose mode."""
        # Set LlamaIndex loggers to INFO level to capture key operations
        logging.getLogger("llama_index.llms").setLevel(logging.INFO)
        logging.getLogger("llama_index.query_engine").setLevel(logging.INFO)
