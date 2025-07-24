"""Configuration management for GitDive."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os

from llama_index.llms.ollama import Ollama
from .constants import LLM_CONTEXT_WINDOW, LLM_TOKEN_LIMIT


@dataclass
class LLMConfig:
    """Configuration for LLM integration."""
    model: str = "phi3:3.8b"
    base_url: str = "http://localhost:11434"
    timeout: int = 180
    stream: bool = True
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load configuration from environment variables."""
        return cls(
            model=os.getenv("GITDIVE_LLM_MODEL", cls.model),
            base_url=os.getenv("GITDIVE_OLLAMA_URL", cls.base_url),
            timeout=int(os.getenv("GITDIVE_LLM_TIMEOUT", str(cls.timeout))),
            stream=os.getenv("GITDIVE_LLM_STREAM", "true").lower() == "true",
        )


@dataclass 
class GitDiveConfig:
    """Main configuration for GitDive."""
    llm: LLMConfig
    
    @classmethod
    def default(cls) -> "GitDiveConfig":
        """Create default configuration."""
        return cls(
            llm=LLMConfig.from_env()
        )
    
    def create_ollama_llm(self) -> Ollama:
        """Create Ollama LLM with consistent configuration."""
        return Ollama(
            model=self.llm.model,
            base_url=self.llm.base_url,
            request_timeout=self.llm.timeout,
            context_window=LLM_CONTEXT_WINDOW,
            num_predict=LLM_TOKEN_LIMIT
        ) 