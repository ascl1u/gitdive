"""Git repository indexer orchestrator."""

from pathlib import Path
from typing import Optional

from llama_index.core import VectorStoreIndex

from .builder import DocumentBuilder
from .processor import CommitProcessor
from .reporter import ProgressReporter
from .storage import StorageManager
from .timing import PipelineTimer
from .logger import Logger


class GitIndexer:
    """Orchestrates git repository indexing using component-based architecture."""

    def __init__(
        self,
        repo_path: Path,
        storage_manager: StorageManager,
        commit_processor: CommitProcessor,
        document_builder: DocumentBuilder,
        logger: Logger,
    ):
        """Initialize indexer with repository path and components."""
        self.repo_path = Path(repo_path).resolve()
        self.storage_manager = storage_manager
        self.commit_processor = commit_processor
        self.document_builder = document_builder
        self.logger = logger
        self.progress_reporter = ProgressReporter(logger)
        self.git_cmd = self.commit_processor.git_cmd
        self.commit_processor.git_cmd.logger = logger

    def validate_repository(self) -> bool:
        """
        Validate repository access and implement access control.
        
        Returns:
            bool: True if repository is valid and accessible
        """
        try:
            # Check if path exists and is a directory
            if not self.repo_path.exists() or not self.repo_path.is_dir():
                self.logger.error(f"Path does not exist or is not a directory: {self.repo_path}")
                return False

            # Prevent indexing .git directories directly
            if self.repo_path.name == '.git':
                self.logger.error("Cannot index .git directory directly. Use the repository root.")
                return False

            # Check if it's inside a .git directory
            if '.git' in self.repo_path.parts:
                self.logger.error("Cannot index paths inside .git directory.")
                return False

            # Validate repository using git CLI
            if not self.git_cmd.validate_repository():
                self.logger.error("Not a valid git repository.")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to validate repository: {str(e)}")
            return False

    def load_index(self) -> Optional[VectorStoreIndex]:
        """Load existing index for querying."""
        return self.storage_manager.load_existing_index(self.repo_path)

    def index_repository(self) -> bool:
        """
        Index the repository using component-based architecture.
        
        Returns:
            bool: True if indexing succeeded
        """
        timer = PipelineTimer(self.logger)

        try:
            with timer.pipeline("Total indexing pipeline"):
                self.progress_reporter.report_start(self.repo_path)

                with self.logger.timing("Vector store setup"):
                    index = self.storage_manager.setup_storage(self.repo_path)
                    if not index:
                        self.logger.error("Failed to setup vector store")
                        return False

                with self.logger.timing("Git commit extraction"):
                    commits = self.commit_processor.extract_commits()

                self.progress_reporter.report_commits_found(len(commits))
                timer.log_processing_stats("Commit extraction", len(commits))

                if not commits:
                    self.logger.info("No commits found with indexable content")
                    return True  # Success - nothing to index

                with self.logger.timing("Document building"):
                    documents = self.document_builder.build_documents(commits)
                    total_content_size = sum(len(doc.text) for doc in documents)
                    timer.log_processing_stats("Document building", len(documents), total_content_size)

                with self.logger.timing("Embedding generation and storage"):
                    documents_created = self.storage_manager.batch_insert_documents(index, documents)
                    timer.log_processing_stats("Document storage", documents_created)

                storage_path = self.storage_manager.get_storage_path(self.repo_path)
                self.progress_reporter.report_completion(documents_created, storage_path)

            return True

        except Exception as e:
            self.logger.error(f"Error during indexing: {str(e)}")
            return False
