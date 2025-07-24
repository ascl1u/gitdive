"""Constants for GitDive application."""

# File processing limits
FILE_SIZE_LIMIT = 10000

# LLM configuration constants  
LLM_CONTEXT_WINDOW = 2048
LLM_TOKEN_LIMIT = 256

# Content processing constants
COMMIT_HASH_DISPLAY_LENGTH = 8
TIMING_LOG_PREVIEW_LENGTH = 100
LLM_PROCESSING_CONTENT_LENGTH = 200
FALLBACK_SUMMARY_LENGTH = 500
PROGRESS_DOTS_PER_LINE = 50

# Storage configuration
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
STORAGE_BASE_DIR = ".gitdive"
MODELS_SUBDIR = "models"
REPOS_SUBDIR = "repos"
CHROMA_COLLECTION_NAME = "commits"
DEFAULT_SIMILARITY_TOP_K = 1

# File filtering
IGNORE_FILE_PATTERNS = [
    '.git/', '__pycache__/', 'node_modules/', 
    '.lock', '.png', '.jpg', '.pdf', '.zip', '.exe', '.dll'
]

# Git processing
GIT_LOG_FORMAT = '%H\x1F%s\x1F%an\x1F%ae\x1F%ai'
GIT_FIELD_COUNT = 5 