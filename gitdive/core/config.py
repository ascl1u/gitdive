"""Configuration management for GitDive."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os

from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from .constants import LLM_CONTEXT_WINDOW, LLM_TOKEN_LIMIT


@dataclass
class LLMConfig:
    """Configuration for LLM integration."""
    model: str = "phi3:3.8b"
    base_url: str = "http://localhost:11434"
    timeout: int = 360
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
class EmbeddingConfig:
    """Configuration for embedding model integration."""
    model: str = "nomic-embed-text:v1.5"
    base_url: str = "http://localhost:11434"
    timeout: int = 360
    
    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Load configuration from environment variables."""
        return cls(
            model=os.getenv("GITDIVE_EMBEDDING_MODEL", cls.model),
            base_url=os.getenv("GITDIVE_EMBEDDING_OLLAMA_URL", os.getenv("GITDIVE_OLLAMA_URL", cls.base_url)),
            timeout=int(os.getenv("GITDIVE_EMBEDDING_TIMEOUT", str(cls.timeout))),
        )


@dataclass 
class GitDiveConfig:
    """Main configuration for GitDive."""
    llm: LLMConfig
    embedding: EmbeddingConfig
    
    @classmethod
    def default(cls) -> "GitDiveConfig":
        """Create default configuration."""
        return cls(
            llm=LLMConfig.from_env(),
            embedding=EmbeddingConfig.from_env()
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

    def create_ollama_embedding(self) -> OllamaEmbedding:
        """Create Ollama embedding with consistent configuration."""
        return OllamaEmbedding(
            model_name=self.embedding.model,
            base_url=self.embedding.base_url,
            request_timeout=self.embedding.timeout,
        )
