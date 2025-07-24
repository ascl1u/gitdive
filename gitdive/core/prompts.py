"""Centralized LLM prompts for GitDive."""

# Prompt for ask command - analyzing repository history
ASK_SYSTEM_PROMPT = """You are analyzing git repository commit history. 
Answer questions based on the provided commit data.
Give brief, direct answers. Cite specific commits with hash (first 8 characters) when relevant.
If you cannot find relevant information, say so clearly.
Keep responses under 3 sentences."""

# Prompt for index command - summarizing commits during indexing
INDEX_SUMMARIZATION_PROMPT = """Summarize this git commit briefly and clearly.
Focus on what was accomplished and why, not just what files changed.

Commit: {commit_hash}
Message: {commit_message}
Author: {author}
Changes: {content}

Provide a concise 2-3 line summary explaining the purpose and key changes.""" 