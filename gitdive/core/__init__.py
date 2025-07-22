"""Core functionality for GitDive."""

from .indexer import GitIndexer

# Public API - only expose what CLI needs
__all__ = ["GitIndexer"] 