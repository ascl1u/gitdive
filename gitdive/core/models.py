"""Data models for GitDive."""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class CommitData:
    """Immutable data container for commit information."""
    hash: str
    summary: str
    author: str
    date: str
    content: str


@dataclass(frozen=True)
class StructuralChanges:
    """Immutable data container for semantic git diff changes."""
    added_functions: List[str]
    removed_functions: List[str]
    modified_functions: List[str]
    added_classes: List[str]
    removed_classes: List[str]
    modified_files: List[str]
    lines_added: int
    lines_removed: int 