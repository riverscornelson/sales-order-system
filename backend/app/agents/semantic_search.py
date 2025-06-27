# This file has been refactored for better maintainability
# The monolithic 387-line class has been split into:
# - Strategy pattern for search strategies (search_strategies/)
# - MatchProcessor for match handling
# - Cleaner main agent in semantic_search_refactored.py

# Import the refactored version
from .semantic_search_refactored import SemanticSearchAgent

# For backward compatibility, we re-export the refactored class
__all__ = ['SemanticSearchAgent']