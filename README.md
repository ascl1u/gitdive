# GitDive

CLI tool for natural language conversations with git repository history.

## Installation

```bash
pip install -e .
```

## Usage

### Index a repository
```bash
# Index current repository
gitdive index

# Index specific repository
gitdive index /path/to/repo

### Ask questions
```bash
gitdive ask "What changes were made to the authentication system?"
```

### Other commands
```bash
gitdive stats    # Show indexing statistics
gitdive cleanup  # Clean up stored indexes
```

## Requirements

- Python 3.13+
- Git repository 

## License

Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
