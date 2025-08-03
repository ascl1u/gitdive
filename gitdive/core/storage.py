"""Storage management for GitDive using ChromaDB."""

import hashlib
from pathlib import Path
from typing import List, Optional
import shutil

import chromadb
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from .config import GitDiveConfig
from .constants import (
    STORAGE_BASE_DIR,
    REPOS_SUBDIR,
    CHROMA_COLLECTION_NAME
)
from .logger import Logger


class StorageManager:
    """Handles ChromaDB storage operations."""

    def __init__(self, config: GitDiveConfig, embed_model: OllamaEmbedding, logger: Logger):
        """Initialize storage manager."""
        self.config = config
        self.embed_model = embed_model
        self.logger = logger

    def get_storage_path(self, repo_path: Path) -> Path:
        """Generate unique storage path for repository."""
        repo_hash = hashlib.sha256(str(repo_path).encode()).hexdigest()
        return Path.home() / STORAGE_BASE_DIR / REPOS_SUBDIR / repo_hash

    def setup_storage(self, repo_path: Path) -> Optional[VectorStoreIndex]:
        """Setup ChromaDB storage and return index."""
        storage_path = self.get_storage_path(repo_path)

        # Clear existing storage for fresh indexing
        if storage_path.exists():
            self.logger.info(f"[blue]Clearing existing index at {storage_path}[/blue]")
            shutil.rmtree(storage_path)

        storage_path.mkdir(parents=True, exist_ok=True)

        try:
            chroma_client = chromadb.PersistentClient(path=str(storage_path))
            chroma_collection = chroma_client.get_or_create_collection(
                CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            return VectorStoreIndex.from_documents(
                [], storage_context=storage_context, embed_model=self.embed_model
            )
        except chromadb.errors.ChromaError as e:
            self.logger.error(f"ChromaDB Error: {str(e)}")
            return None
        except PermissionError as e:
            self.logger.error(f"Permission Error: Cannot write to {storage_path}: {str(e)}")
            return None
        except OSError as e:
            self.logger.error(f"Storage Error: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected Error: {str(e)}")
            return None

    def load_existing_index(self, repo_path: Path) -> Optional[VectorStoreIndex]:
        """Load existing index for querying."""
        storage_path = self.get_storage_path(repo_path)
        if not storage_path.exists():
            return None

        try:
            chroma_client = chromadb.PersistentClient(path=str(storage_path))
            chroma_collection = chroma_client.get_collection(CHROMA_COLLECTION_NAME)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            return VectorStoreIndex.from_vector_store(vector_store, embed_model=self.embed_model)
        except chromadb.errors.ChromaError as e:
            self.logger.error(f"ChromaDB Error: {str(e)}")
            return None
        except PermissionError as e:
            self.logger.error(f"Permission Error: Cannot access {storage_path}: {str(e)}")
            return None
        except OSError as e:
            self.logger.error(f"Storage Error: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected Error: {str(e)}")
            return None

    def batch_insert_documents(self, index: VectorStoreIndex, documents: List[Document]) -> int:
        """Insert documents in batch and return count of documents processed."""
        if not documents:
            return 0

        try:
            index.insert_nodes(documents)
            return len(documents)
        except Exception as e:
            self.logger.error(f"Error inserting documents: {str(e)}")
            return 0
    
    def cleanup_repository_index(self, repo_path: Path) -> tuple[bool, str, Optional[Path]]:
        """
        Clean up the index for a specific repository.
        
        Args:
            repo_path: Path to the git repository
            
        Returns:
            Tuple of (success, message, cleaned_path)
        """
        storage_path = self.get_storage_path(repo_path)
        
        # Check if index exists
        if not storage_path.exists():
            return True, "No index found for this repository", None
        
        try:
            import shutil
            shutil.rmtree(storage_path)
            return True, f"Successfully cleaned up index", storage_path
        except PermissionError as e:
            return False, f"Permission denied: Cannot delete {storage_path}", None
        except OSError as e:
            return False, f"Failed to delete index: {str(e)}", None
        except Exception as e:
            return False, f"Unexpected error during cleanup: {str(e)}", None
