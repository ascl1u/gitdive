"""Data models for GitDive."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CommitData:
    """Immutable data container for commit information."""
    hash: str
    summary: str
    author: str
    date: str
    content: str 