"""Centralized logger for GitDive."""

import sys
from contextlib import contextmanager
from time import perf_counter

from rich.console import Console

console = Console(force_terminal=True, file=sys.stdout)


class Logger:
    """Handles all logging for the application."""

    def __init__(self, verbose: bool = False):
        """Initialize logger with verbosity level."""
        self.verbose = verbose

    def info(self, message: str):
        """Log informational messages."""
        console.print(message)

    def debug(self, message: str):
        """Log debug messages if verbose is enabled."""
        if self.verbose:
            console.print(f"[dim]{message}[/dim]")

    def error(self, message: str):
        """Log error messages."""
        console.print(f"[red]Error:[/red] {message}")

    @contextmanager
    def timing(self, description: str):
        """
        Context manager for timing blocks of code.

        Args:
            description: Description of the timed block.
        """
        if not self.verbose:
            yield
            return

        start_time = perf_counter()
        self.debug(f"Starting: {description}...")
        yield
        end_time = perf_counter()
        duration = end_time - start_time
        self.debug(f"Finished: {description} in {duration:.2f}s")
