"""SAG - Data Flow Intelligent Engine

AI-driven data processing and aggregation search engine
"""

__version__ = "0.1.0"
__author__ = "Zleap Team"
__email__ = "contact@zleap.ai"

from sag.engine import (
    SAGEngine,
    DocumentLoadConfig,
    ExtractBaseConfig,
    LoadBaseConfig,
    ModelConfig,
    LogLevel,
    OutputConfig,
    OutputMode,
    SearchBaseConfig,
    ConversationLoadConfig,
    StageResult,
    TaskConfig,
    TaskLog,
    TaskResult,
    TaskStage,
    TaskStatus,
)
from sag.exceptions import SAGError, LLMError, StorageError, ValidationError

__all__ = [
    # Version
    "__version__",
    # Engine
    "SAGEngine",
    "TaskConfig",
    "TaskResult",
    "TaskLog",
    "TaskStatus",
    "TaskStage",
    "StageResult",
    # Configs
    "ModelConfig",
    "LoadBaseConfig",
    "DocumentLoadConfig",
    "ConversationLoadConfig",
    "ExtractBaseConfig",
    "SearchBaseConfig",
    "OutputConfig",
    "OutputMode",
    "LogLevel",
    # Exceptions
    "SAGError",
    "LLMError",
    "StorageError",
    "ValidationError",
]
