"""Git repository indexer orchestrator."""

from pathlib import Path
from typing import Optional
import sys

from llama_index.core import VectorStoreIndex
from rich.console import Console

from .builder import DocumentBuilder
from .git_cli import GitCommand
from .processor import CommitProcessor
from .reporter import ProgressReporter
from .storage import StorageManager
from .timing import PipelineTimer

console = Console(force_terminal=True, file=sys.stdout)


class GitIndexer:
    """Orchestrates git repository indexing using component-based architecture."""
    
    def __init__(self, repo_path: Path):
        """Initialize indexer with repository path and components."""
        self.repo_path = Path(repo_path).resolve()
        
        # Initialize git command utility
        self.git_cmd = GitCommand(self.repo_path)
        
        # Initialize components
        self.storage_manager = StorageManager()
        self.commit_processor = CommitProcessor(self.git_cmd)
        self.document_builder = DocumentBuilder()
        self.progress_reporter = ProgressReporter()
        
        # Connect progress callback
        self.commit_processor.set_progress_callback(self.progress_reporter.report_commit_progress)
        
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
            
            # Validate repository using git CLI
            if not self.git_cmd.validate_repository():
                console.print("[red]Error:[/red] Not a valid git repository.")
                return False
                
            return True
            
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to validate repository: {str(e)}")
            return False

    def load_index(self) -> Optional[VectorStoreIndex]:
        """Load existing index for querying."""
        return self.storage_manager.load_existing_index(self.repo_path)
    

    def index_repository(self, verbose: bool = False) -> bool:
        """
        Index the repository using component-based architecture.
        
        Args:
            verbose: Enable detailed timing information
            
        Returns:
            bool: True if indexing succeeded
        """
        timer = PipelineTimer(verbose)
        
        try:
            timer.start_pipeline()
            
            # Report start
            self.progress_reporter.report_start(self.repo_path)
            
            # Setup storage
            timer.start_step("Vector store setup")
            index = self.storage_manager.setup_storage(self.repo_path)
            if not index:
                console.print("[red]Error:[/red] Failed to setup vector store")
                return False
            timer.end_step("Vector store setup")
            
            # Extract commits (batch processing using git CLI)
            timer.start_step("Git commit extraction")
            commits = self.commit_processor.extract_commits()
            timer.end_step("Git commit extraction")
            
            # Report commits found
            self.progress_reporter.report_commits_found(len(commits))
            timer.log_processing_stats("Commit extraction", len(commits))
            
            if not commits:
                console.print("[blue]No commits found with indexable content[/blue]")
                timer.end_pipeline()
                return True  # Success - nothing to index
            
            # Build documents
            timer.start_step("Document building")
            documents = self.document_builder.build_documents(commits)
            total_content_size = sum(len(doc.text) for doc in documents)
            timer.end_step("Document building")
            timer.log_processing_stats("Document building", len(documents), total_content_size)
            
            # Insert documents in batch
            timer.start_step("Embedding generation and storage")
            documents_created = self.storage_manager.batch_insert_documents(index, documents)
            timer.end_step("Embedding generation and storage")
            timer.log_processing_stats("Document storage", documents_created)
            
            # Report completion
            storage_path = self.storage_manager.get_storage_path(self.repo_path)
            self.progress_reporter.report_completion(documents_created, storage_path)
            
            timer.end_pipeline()
            # Success if we processed everything without errors
            return True
            
        except Exception as e:
            timer.log_timing(f"Indexing failed with error: {str(e)}")
            console.print(f"[red]Error during indexing:[/red] {str(e)}")
            return False 