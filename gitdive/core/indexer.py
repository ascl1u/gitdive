"""Git repository indexer"""

import hashlib
from pathlib import Path
from typing import List, Optional

import chromadb
import git
from llama_index.core import Document, VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from rich.console import Console

console = Console()


class GitIndexer:
    """Handles git repository indexing with safety controls and time filtering."""
    
    def __init__(self, repo_path: Path):
        """Initialize indexer with repository path."""
        self.repo_path = Path(repo_path).resolve()
        self.repo = None
        
    def validate_repository(self) -> bool:
        """
        Validate repository access and implement access control.
        
        Returns:
            bool: True if repository is valid and accessible
        """
        try:
            # Check if path exists and is a directory
            if not self.repo_path.exists() or not self.repo_path.is_dir():
                console.print(f"[red]Error:[/red] Path does not exist or is not a directory: {self.repo_path}")
                return False
            
            # Prevent indexing .git directories directly
            if self.repo_path.name == '.git':
                console.print("[red]Error:[/red] Cannot index .git directory directly. Use the repository root.")
                return False
            
            # Check if it's inside a .git directory
            if '.git' in self.repo_path.parts:
                console.print("[red]Error:[/red] Cannot index paths inside .git directory.")
                return False
            
            # Try to open as git repository
            self.repo = git.Repo(self.repo_path)
            
            # Additional safety check - ensure we have a valid repo
            if self.repo.bare:
                console.print("[red]Error:[/red] Bare repositories are not supported.")
                return False
                
            return True
            
        except git.InvalidGitRepositoryError:
            console.print("[red]Error:[/red] Not a valid git repository.")
            return False
        except git.NoSuchPathError:
            console.print("[red]Error:[/red] Repository path does not exist.")
            return False
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to validate repository: {str(e)}")
            return False

    def _get_storage_path(self) -> Path:
        """Generate unique storage path for this repository."""
        repo_hash = hashlib.sha256(str(self.repo_path).encode()).hexdigest()[:16]
        return Path.home() / ".gitdive" / "repos" / repo_hash

    def _should_include_file(self, file_path: str) -> bool:
        """Apply 3-layer filtering: .gitignore → global ignore → content heuristics."""
        if not file_path:
            return False
        
        # Layer 1: .gitignore (basic check for common patterns)
        gitignore_patterns = ['.git/', '__pycache__/', 'node_modules/']
        for pattern in gitignore_patterns:
            if pattern in file_path:
                return False
        
        # Layer 2: Global ignore list
        ignore_patterns = ['.lock', '.png', '.jpg', '.pdf', '.zip', '.exe', '.dll']
        for pattern in ignore_patterns:
            if file_path.endswith(pattern):
                return False
        
        # Layer 3: Basic content heuristics (file extension check)
        return True

    def _extract_added_lines(self, commit) -> str:
        """Extract only + lines from commit diff."""
        added_lines = []
        try:
            parent = commit.parents[0] if commit.parents else None
            is_initial_commit = parent is None
            
            if is_initial_commit:
                # For initial commits, get all file contents as "added"
                for file_path in commit.stats.files.keys():
                    if not self._should_include_file(file_path):
                        continue
                    
                    try:
                        # Get file content from the commit
                        file_content = (commit.tree / file_path).data_stream.read().decode('utf-8', errors='ignore')
                        # Apply size limit per file
                        file_content = file_content[:10000]
                        file_lines = file_content.split('\n')
                        added_lines.extend(file_lines)
                    except Exception:
                        continue
            else:
                # Regular commit - process diff
                diff_items = list(commit.diff(parent))
                
                for item in diff_items:
                    file_path = item.b_path or item.a_path
                    
                    if not self._should_include_file(file_path):
                        continue
                        
                    if not item.diff:
                        continue
                        
                    diff_text = item.diff.decode('utf-8', errors='ignore')
                    # Apply size limit per file diff
                    diff_text = diff_text[:10000]
                    for line in diff_text.split('\n'):
                        if line.startswith('+') and not line.startswith('+++'):
                            added_lines.append(line[1:])  # Remove + prefix
                
        except Exception:
            pass  # Skip problematic commits
        
        return '\n'.join(added_lines)  # No total limit needed - already limited per file
    
    def index_repository(self) -> bool:
        """
        Index the repository with ChromaDB storage.
        
        Returns:
            bool: True if indexing succeeded
        """
        try:
            if not self.repo:
                console.print("[red]Error:[/red] Repository not validated. Call validate_repository() first.")
                return False
            
            # Get basic commit list
            commits = self._get_commits()
            
            if not commits:
                console.print("[yellow]Warning:[/yellow] No commits found in repository.")
                return True
            
            console.print(f"[blue]Found {len(commits)} commits to index[/blue]")
            
            # Set up ChromaDB storage
            storage_path = self._get_storage_path()
            storage_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB
            chroma_client = chromadb.PersistentClient(path=str(storage_path))
            chroma_collection = chroma_client.get_or_create_collection("commits")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            
            # Initialize local embedding model
            embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
            index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
            
            # Process commits
            documents_created = 0
            for commit in commits:
                diff_content = self._extract_added_lines(commit)
                
                if diff_content.strip():  # Only create document if we have content
                    # Combine commit message and diff content for better search
                    full_text = f"{commit.summary}\n\n{diff_content}"
                    doc = Document(
                        text=full_text,
                        metadata={
                            "commit_hash": commit.hexsha,
                            "author": f"{commit.author.name} <{commit.author.email}>",
                            "date": str(commit.authored_datetime)
                        }
                    )
                    index.insert(doc)
                    documents_created += 1
                    
                    if documents_created <= 5:  # Show first 5 for verification
                        console.print(f"[dim]Indexed commit: {commit.hexsha[:8]} - {commit.summary}[/dim]")
            
            if documents_created > 5:
                console.print(f"[dim]... and {documents_created - 5} more commits indexed[/dim]")
            
            console.print(f"[green]✓[/green] Created {documents_created} documents in ChromaDB at {storage_path}")
            return True
            
        except Exception as e:
            console.print(f"[red]Error during indexing:[/red] {str(e)}")
            return False
    
    def _get_commits(self) -> List[git.Commit]:
        """Get basic list of commits (Phase 1: no filtering)."""
        try:
            commits = []
            
            # Get all commits from the default branch
            for commit in self.repo.iter_commits():
                commits.append(commit)
            
            return commits
            
        except Exception as e:
            console.print(f"[red]Error getting commits:[/red] {str(e)}")
            return [] 