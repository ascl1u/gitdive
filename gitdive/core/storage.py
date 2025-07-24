"""Storage management for GitDive using ChromaDB."""

import hashlib
from pathlib import Path
from typing import List, Optional
import sys

import chromadb
from llama_index.core import Document, VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from rich.console import Console
from .constants import (
    EMBEDDING_MODEL_NAME, 
    STORAGE_BASE_DIR, 
    MODELS_SUBDIR, 
    REPOS_SUBDIR, 
    CHROMA_COLLECTION_NAME
)

console = Console(force_terminal=True, file=sys.stdout)


class StorageManager:
    """Handles ChromaDB storage operations."""
    
    def __init__(self):
        # Create cache directory for embedding model to avoid download delays
        cache_dir = Path.home() / STORAGE_BASE_DIR / MODELS_SUBDIR
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.embed_model = HuggingFaceEmbedding(
            model_name=EMBEDDING_MODEL_NAME,
            cache_folder=str(cache_dir)
        )
    
    def get_storage_path(self, repo_path: Path) -> Path:
        """Generate unique storage path for repository."""
        repo_hash = hashlib.sha256(str(repo_path).encode()).hexdigest()
        return Path.home() / STORAGE_BASE_DIR / REPOS_SUBDIR / repo_hash
    
    def setup_storage(self, repo_path: Path) -> Optional[VectorStoreIndex]:
        """Setup ChromaDB storage and return index."""
        storage_path = self.get_storage_path(repo_path)
        
        # Clear existing storage for fresh indexing
        if storage_path.exists():
            import shutil
            console.print(f"[blue]Clearing existing index at {storage_path}[/blue]")
            shutil.rmtree(storage_path)
        
        storage_path.mkdir(parents=True, exist_ok=True)
        
        try:
            chroma_client = chromadb.PersistentClient(path=str(storage_path))
            chroma_collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION_NAME)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            return VectorStoreIndex.from_vector_store(vector_store, embed_model=self.embed_model)
        except chromadb.errors.ChromaError as e:
            console.print(f"[red]ChromaDB Error:[/red] {str(e)}")
            return None
        except PermissionError as e:
            console.print(f"[red]Permission Error:[/red] Cannot write to {storage_path}: {str(e)}")
            return None
        except OSError as e:
            console.print(f"[red]Storage Error:[/red] {str(e)}")
            return None
        except Exception as e:
            console.print(f"[red]Unexpected Error:[/red] {str(e)}")
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
            console.print(f"[red]ChromaDB Error:[/red] {str(e)}")
            return None
        except PermissionError as e:
            console.print(f"[red]Permission Error:[/red] Cannot access {storage_path}: {str(e)}")
            return None
        except OSError as e:
            console.print(f"[red]Storage Error:[/red] {str(e)}")
            return None
        except Exception as e:
            console.print(f"[red]Unexpected Error:[/red] {str(e)}")
            return None
    
    def batch_insert_documents(self, index: VectorStoreIndex, documents: List[Document]) -> int:
        """Insert documents in batch and return count of documents processed."""
        if not documents:
            return 0
        
        try:
            # Insert all documents - trust LlamaIndex internal processing
            for doc in documents:
                index.insert(doc)
            
            return len(documents)
        except Exception as e:
            console.print(f"[red]Error inserting documents:[/red] {str(e)}")
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