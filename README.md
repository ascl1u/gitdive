# GitDive

CLI tool for natural language conversations with git repository history. Index commits and ask questions about your project's evolution using a local llm.

## Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai) with a compatible model:
  ```bash
  ollama pull phi3:3.8b  # Recommended
  ```

## Installation

```bash
pip install gitdive
```

## Usage

**Index a repository:**
```bash
gitdive index                    # Current directory
gitdive index /path/to/repo      # Specific repository
gitdive index --verbose          # Show timing details
```

**Ask questions:**
```bash
gitdive ask "What changed in the authentication system?"
gitdive ask "Who worked on the API endpoints?"
gitdive ask "When was the database schema last modified?"
```

**Cleanup:**
```bash
gitdive cleanup  # Remove stored index
```

## Configuration

Configure via environment variables:

```bash
export GITDIVE_LLM_MODEL="llama3.1:8b"        # Default: phi3:3.8b
export GITDIVE_OLLAMA_URL="http://localhost:11434"  # Default
export GITDIVE_LLM_TIMEOUT="300"              # Default: 180
```

Indexes are stored in `~/.gitdive/repos/`

## Requirements

- Python 3.9+
- Git repository
- Ollama with compatible model

## License

Apache License 2.0
