"""Timing utility for debugging GitDive pipeline performance."""

import time
import logging
from typing import Dict, Optional
from rich.console import Console

console = Console(force_terminal=True)


class PipelineTimer:
    """Simple timing utility for measuring pipeline performance."""
    
    def __init__(self, verbose: bool = False):
        """Initialize timer with verbose flag."""
        self.verbose = verbose
        self.start_times: Dict[str, float] = {}
        self.total_start_time: Optional[float] = None
        
        # Enable LlamaIndex debug logging when verbose
        if self.verbose:
            self._enable_llamaindex_logging()
    
    def start_pipeline(self):
        """Start timing the entire pipeline."""
        if self.verbose:
            self.total_start_time = time.time()
            console.print("[dim][TIMING] Pipeline started[/dim]")
    
    def start_step(self, step_name: str):
        """Start timing a specific step."""
        if self.verbose:
            self.start_times[step_name] = time.time()
            console.print(f"[dim][TIMING] {step_name} - starting...[/dim]")
    
    def end_step(self, step_name: str):
        """End timing a specific step and log duration."""
        if self.verbose and step_name in self.start_times:
            duration = time.time() - self.start_times[step_name]
            console.print(f"[dim][TIMING] {step_name} - completed in {duration:.2f}s[/dim]")
            del self.start_times[step_name]
    
    def log_timing(self, message: str):
        """Log a timing message."""
        if self.verbose:
            console.print(f"[dim][TIMING] {message}[/dim]")
    
    def end_pipeline(self):
        """End timing the entire pipeline."""
        if self.verbose and self.total_start_time:
            total_duration = time.time() - self.total_start_time
            console.print(f"[dim][TIMING] Total pipeline completed in {total_duration:.2f}s[/dim]")
    
    def log_llamaindex_operation(self, operation: str, details: str = ""):
        """Log LlamaIndex operation details."""
        if self.verbose:
            console.print(f"[dim][LLAMAINDEX] {operation}{' - ' + details if details else ''}[/dim]")
    
    def log_http_metadata(self, method: str, url: str, payload_size: int, response_time: float):
        """Log HTTP request metadata without full content."""
        if self.verbose:
            console.print(f"[dim][HTTP] {method} {url} - {payload_size} bytes - {response_time:.2f}s[/dim]")
    
    def log_prompt_info(self, prompt_type: str, content_preview: str, total_length: int):
        """Log key sections of prompts without full content."""
        if self.verbose:
            preview = content_preview[:100] + "..." if len(content_preview) > 100 else content_preview
            console.print(f"[dim][PROMPT] {prompt_type} ({total_length} chars): '{preview}'[/dim]")
    
    def log_processing_stats(self, operation: str, count: int, total_size: int = 0):
        """Log processing statistics."""
        if self.verbose:
            size_info = f", {total_size} total chars" if total_size > 0 else ""
            console.print(f"[dim][TIMING] {operation} - processed {count} items{size_info}[/dim]")
    
    def _enable_llamaindex_logging(self):
        """Enable LlamaIndex debug logging for verbose mode."""
        # Set LlamaIndex loggers to INFO level to capture key operations
        logging.getLogger("llama_index.llms").setLevel(logging.INFO)
        logging.getLogger("llama_index.query_engine").setLevel(logging.INFO) 