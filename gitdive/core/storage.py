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

console = Console(force_terminal=True, file=sys.stdout)


class StorageManager:
    """Handles ChromaDB storage operations."""
    
    def __init__(self):
        # Create cache directory for embedding model to avoid download delays
        cache_dir = Path.home() / ".gitdive" / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-en-v1.5",
            cache_folder=str(cache_dir)
        )
    
    def get_storage_path(self, repo_path: Path) -> Path:
        """Generate unique storage path for repository."""
        repo_hash = hashlib.sha256(str(repo_path).encode()).hexdigest()
        return Path.home() / ".gitdive" / "repos" / repo_hash
    
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
            chroma_collection = chroma_client.get_or_create_collection("commits")
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
            chroma_collection = chroma_client.get_collection("commits")
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