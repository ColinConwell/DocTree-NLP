"""
Custom exceptions for the Notion NLP library.
"""

class NotionNLPError(Exception):
    """Base exception for Notion NLP library."""
    pass

class AuthenticationError(NotionNLPError):
    """Raised when authentication fails."""
    pass
