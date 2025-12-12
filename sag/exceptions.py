"""
SAG exception definitions

All custom exceptions inherit from SAGError base class
"""


class SAGError(Exception):
    """SAG base exception class"""

    def __init__(self, message: str, *args: object) -> None:
        self.message = message
        super().__init__(message, *args)


class ConfigError(SAGError):
    """Configuration error exception"""

    pass


class StorageError(SAGError):
    """Storage layer exception"""

    pass


class DatabaseError(StorageError):
    """Database exception"""

    pass


class CacheError(StorageError):
    """Cache exception"""

    pass


class LLMError(SAGError):
    """LLM call exception"""

    pass


class LLMTimeoutError(LLMError):
    """LLM call timeout exception"""

    pass


class LLMRateLimitError(LLMError):
    """LLM rate limit exception"""

    pass


class AIError(SAGError):
    """AI-related exception (including LLM and Embedding)"""

    pass


class ValidationError(SAGError):
    """Data validation exception"""

    pass


class LoadError(SAGError):
    """Document loading exception"""

    pass


class EntityError(SAGError):
    """Entity processing exception"""

    pass


class ExtractError(SAGError):
    """Event extraction exception"""

    pass


class SearchError(SAGError):
    """Search exception"""

    pass


class PromptError(SAGError):
    """Prompt exception"""

    pass
