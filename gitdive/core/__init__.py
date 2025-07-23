"""Core functionality for GitDive."""

from .indexer import GitIndexer
from .query import QueryService

# Public API - only expose what CLI needs
__all__ = ["GitIndexer", "QueryService"] 