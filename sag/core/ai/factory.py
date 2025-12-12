"""
LLM client factory

Creates corresponding LLM clients based on configuration, supports scenario-based configuration
"""

import hashlib
import json
from typing import Any, Dict, Optional

from sag.core.ai.base import BaseLLMClient, LLMRetryClient
from sag.core.ai.models import ModelConfig, LLMProvider
from sag.core.ai.llm import OpenAIClient
from sag.core.config import get_settings
from sag.exceptions import ConfigError
from sag.utils import get_logger

logger = get_logger("ai.factory")


def _get_client_fingerprint(config: Dict[str, Any]) -> str:
    """
    Generate client configuration fingerprint (common function)
    
    Only includes core parameters that affect client instance:
    - model: Model name
    - api_key: API key
    - base_url: API address
    
    Other parameters (temperature, dimensions, timeout, etc.) do not affect the client instance itself
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Configuration fingerprint (MD5 hash)
    """
    key_params = {
        'model': config.get('model'),
        'api_key': config.get('api_key'),
        'base_url': config.get('base_url'),
    }
    # Generate configuration hash value
    config_str = json.dumps(key_params, sort_keys=True)
    return hashlib.md5(config_str.encode()).hexdigest()


async def create_llm_client(
    scenario: str = 'general',
    model_config: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> BaseLLMClient | LLMRetryClient:
    """
    Create LLM client (unified entry point, supports scenario-based configuration)

    Configuration priority (from high to low):
    1. model_config explicitly passed
    2. Database scenario configuration (if USE_DB_CONFIG=true)
    3. Environment variable configuration (fallback)

    Args:
        scenario: Scenario identifier, default 'general'
            - 'extract' : Event extraction
            - 'search'  : Search
            - 'chat'    : Chat
            - 'summary' : Summary
            - 'general' : General (default)
        
        model_config: LLM configuration dictionary (optional)
            {
                'model': 'gpt-4',
                'api_key': 'sk-xxx',
                'base_url': 'https://api.302.ai',
                'temperature': 0.3,
                'max_tokens': 8000,
                ...
            }
            - If passed: directly used (highest priority)
            - If not passed: automatically obtained from configuration manager
        
        **kwargs: Scattered parameters (backward compatibility)

    Returns:
        LLM client instance

    Raises:
        ConfigError: Raised when unable to get valid configuration

    Examples:
        # Method 1: Only pass scenario, auto-get config (recommended)
        >>> client = await create_llm_client(scenario='extract')
        
        # Method 2: Explicitly pass configuration
        >>> client = await create_llm_client(
        ...     scenario='extract',
        ...     model_config={'model': 'gpt-4', 'temperature': 0.1}
        ... )
        
        # Method 3: Use default general scenario
        >>> client = await create_llm_client()

    Note:
    - Unified use of OpenAIClient (compatible with OpenAI official + 302.AI proxy)
    - Distinguish different service providers through base_url
    """
    settings = get_settings()

    # ============ Configuration merging (three-layer priority) ============
    
    # Layer 3: Environment variable fallback
    config = {
        'model': settings.llm_model,
        'api_key': settings.llm_api_key,
        'base_url': settings.llm_base_url,
        'temperature': settings.llm_temperature,
        'max_tokens': settings.llm_max_tokens,
        'top_p': settings.llm_top_p,
        'frequency_penalty': settings.llm_frequency_penalty,
        'presence_penalty': settings.llm_presence_penalty,
        'timeout': settings.llm_timeout,
        'max_retries': settings.llm_max_retries,
    }
    
    # Layer 2: Database configuration (specify type='llm')
    if settings.use_db_config:
        db_config = await _load_db_config(type='llm', scenario=scenario)
        if db_config:
            config.update(db_config)
            logger.info(f"📊 Using database LLM config: scenario={scenario}, model={db_config.get('model')}")
        else:
            logger.debug(f"No database LLM config, using environment variables: scenario={scenario}")

    # Layer 1: Explicit configuration (highest priority)
    if model_config:
        config.update(model_config)
        logger.info(f"🎯 Using explicit config: scenario={scenario}")
    
    # Compatible with scattered parameters (backward compatibility)
    if kwargs:
        config.update(kwargs)

    # ============ Validate required parameters ============
    if not config.get('api_key'):
        raise ConfigError(
            f"❌ LLM configuration error: Missing API Key!\n"
            f"Scenario: {scenario}\n"
            f"Please check: database configuration or environment variable LLM_API_KEY"
        )
    
    if not config.get('model'):
        raise ConfigError(f"❌ LLM configuration error: Missing model name! Scenario: {scenario}")

    # ============ Build configuration object ============
    model_config_obj = ModelConfig(
        provider=LLMProvider.OPENAI,  # Unified use of OPENAI (compatible with all proxy services)
        model=config['model'],
        api_key=config['api_key'],
        base_url=config.get('base_url'),
        temperature=config['temperature'],
        max_tokens=config['max_tokens'],
        top_p=config['top_p'],
        frequency_penalty=config['frequency_penalty'],
        presence_penalty=config['presence_penalty'],
        timeout=config['timeout'],
        max_retries=config['max_retries'],
    )

    # ============ Create client (unified use of OpenAIClient) ============
    # OpenAIClient compatible: OpenAI official + 302.AI proxy + other compatible services
    base_client = OpenAIClient(model_config_obj)

    # Wrap retry mechanism
    with_retry = config.get('with_retry', True)
    if with_retry:
        logger.info(
            f"✅ Created LLM client (with retry): scenario={scenario}",
            extra={
                "scenario": scenario,
                "model": config['model'],
                "base_url": config.get('base_url') or 'OpenAI official',
                "max_retries": config['max_retries'],
            },
        )
        return LLMRetryClient(base_client)

    logger.info(
        f"✅ Created LLM client: scenario={scenario}",
        extra={
            "scenario": scenario,
            "model": config['model'],
        },
    )
    return base_client


async def _load_db_config(
    type: str = 'llm',
    scenario: str = 'general'
) -> Optional[Dict[str, Any]]:
    """
    Load model configuration from database (common function)
    
    Degradation strategy (for LLM):
    1. Query dedicated configuration for type + scenario
    2. Degrade to type + 'general'
    3. Return None (use environment variable fallback)
    
    For Embedding/Rerank, etc.:
    - Directly query type + scenario (usually general)
    
    Args:
        type: Model type (llm/embedding/rerank)
        scenario: Usage scenario
        
    Returns:
        Configuration dictionary or None
    """
    try:
        from sqlalchemy import select
        from sag.db import get_session_factory
        from sag.db.models import ModelConfig
        
        async with get_session_factory()() as session:
            # Query configuration for specified type and scenario
            result = await session.execute(
                select(ModelConfig)
                .where(
                    ModelConfig.type == type,
                    ModelConfig.scenario == scenario,
                    ModelConfig.is_active == True
                )
                .order_by(ModelConfig.priority.desc())
                .limit(1)
            )
            config = result.scalar_one_or_none()
            if config:
                logger.debug(f"Found config: type={type}, scenario={scenario}")
                return _db_model_to_dict(config)
            
            # Degradation strategy: only for LLM and non-general scenarios
            if type == 'llm' and scenario != 'general':
                result = await session.execute(
                    select(ModelConfig)
                    .where(
                        ModelConfig.type == 'llm',
                        ModelConfig.scenario == 'general',
                        ModelConfig.is_active == True
                    )
                    .order_by(ModelConfig.priority.desc())
                    .limit(1)
                )
                config = result.scalar_one_or_none()
                if config:
                    logger.debug("Degraded to general LLM config")
                return _db_model_to_dict(config)
        
        return None
        
    except Exception as e:
        # Database query failure does not affect main flow, return None to use environment variable fallback
        logger.warning(f"Database configuration loading failed: {e}")
        return None


def _db_model_to_dict(config) -> Dict[str, Any]:
    """
    Convert database model to dictionary
    
    Args:
        config: ModelConfig model instance
        
    Returns:
        Configuration dictionary
    """
    result = {
        'model': config.model,
        'api_key': config.api_key,
        'base_url': config.base_url,
        'timeout': config.timeout,
        'max_retries': config.max_retries,
    }
    
    # LLM-specific parameters
    if hasattr(config, 'temperature'):
        result['temperature'] = float(config.temperature)
    if hasattr(config, 'max_tokens'):
        result['max_tokens'] = config.max_tokens
    if hasattr(config, 'top_p'):
        result['top_p'] = float(config.top_p)
    if hasattr(config, 'frequency_penalty'):
        result['frequency_penalty'] = float(config.frequency_penalty)
    if hasattr(config, 'presence_penalty'):
        result['presence_penalty'] = float(config.presence_penalty)
    
    # Extended data (e.g., embedding's dimensions)
    if hasattr(config, 'extra_data') and config.extra_data:
        result['extra_data'] = config.extra_data
    
    return result


# ============================================================
# Note:
# - LLM client: Create new instance each time, each module manages itself (extractor, searcher, agent, etc.)
# - Embedding client: Global singleton, automatically replaced when configuration changes
# ============================================================


# ============ Embedding Client Factory ============

async def create_embedding_client(
    scenario: str = 'general',
    embedding_config: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> 'EmbeddingClient':
    """
    Create Embedding client (unified entry point, supports layered configuration)

    Configuration priority (from high to low):
    1. embedding_config explicitly passed
    2. Database configuration (if USE_DB_CONFIG=true, model_type='embedding')
    3. Environment variable configuration (fallback)

    Args:
        scenario: Usage scenario, default 'general' (currently embedding only uses general, can be extended in future)
        embedding_config: Embedding configuration dictionary (optional)
            {
                'model': 'Qwen/Qwen3-Embedding-0.6B',
                'api_key': 'sk-xxx',
                'base_url': 'https://api.302.ai',
                'dimensions': 1536,
                ...
            }
        **kwargs: Scattered parameters (backward compatibility)

    Returns:
        EmbeddingClient instance

    Raises:
        ConfigError: Raised when unable to get valid configuration

    Examples:
        # Method 1: Auto-get config (recommended)
        >>> client = await create_embedding_client()
        
        # Method 2: Explicitly pass configuration
        >>> client = await create_embedding_client(
        ...     embedding_config={'model': 'text-embedding-3-large'}
        ... )
    """
    settings = get_settings()

    # ============ Configuration merging (three-layer priority) ============
    
    # Layer 3: Environment variable fallback
    config = {
        'model': settings.embedding_model_name,
        'api_key': settings.embedding_api_key or settings.llm_api_key,
        'base_url': settings.embedding_base_url or settings.llm_base_url,
        'dimensions': settings.embedding_dimensions,
        'timeout': 60,
        'max_retries': 3,
    }
    
    # Layer 2: Database configuration (specify type='embedding')
    if settings.use_db_config:
        db_config = await _load_db_config(type='embedding', scenario=scenario)
        if db_config:
            # Extract dimensions (may be in extra_data)
            if 'extra_data' in db_config and db_config['extra_data']:
                if 'dimensions' in db_config['extra_data']:
                    db_config['dimensions'] = db_config['extra_data']['dimensions']
            config.update(db_config)
            logger.info(f"📊 Using database Embedding config: model={db_config.get('model')}")
        else:
            logger.debug("No database Embedding config, using environment variables")

    # Layer 1: Explicit configuration (highest priority)
    if embedding_config:
        config.update(embedding_config)
        logger.info("🎯 Using explicit Embedding config")
    
    # Compatible with scattered parameters
    if kwargs:
        config.update(kwargs)

    # ============ Validate required parameters ============
    if not config.get('api_key'):
        raise ConfigError(
            "❌ Embedding configuration error: Missing API Key!\n"
            f"Scenario: {scenario}\n"
            "Please check: database configuration or environment variable EMBEDDING_API_KEY/LLM_API_KEY"
        )
    
    if not config.get('model'):
        raise ConfigError(f"❌ Embedding configuration error: Missing model name! Scenario: {scenario}")

    # ============ Create client ============
    from sag.core.ai.embedding import EmbeddingClient
    
    # ✅ Extract parameters to create client (include api_key, ensure database config takes effect)
    client = EmbeddingClient(
        model=config['model'],
        base_url=config.get('base_url'),
        api_key=config.get('api_key')
    )
    
    # If dimensions parameter exists, need to pass it during generation
    # TODO: Update EmbeddingClient.generate() to support dimensions parameter

    logger.info(
        "✅ Created Embedding client",
        extra={
            "scenario": scenario,
            "model": config['model'],
            "base_url": config.get('base_url') or 'OpenAI official',
            "dimensions": config.get('dimensions') or 'default',
        },
    )
    return client


# Global Embedding client singleton (automatically replaced when configuration changes)
_embedding_client: Optional['EmbeddingClient'] = None
_embedding_config_fingerprint: Optional[str] = None


async def get_embedding_client(scenario: str = 'general') -> 'EmbeddingClient':
    """
    Get Embedding client (singleton, configuration auto-updates)
    
    How it works:
    - Maintains global unique instance
    - Detects configuration changes on each call (based on fingerprint)
    - Automatically replaces with new instance when configuration changes
    - Reuses existing instance when configuration unchanged
    
    Fingerprint parameters: model, api_key, base_url (common three elements)
    
    Args:
        scenario: Usage scenario, default 'general'
    
    Returns:
        EmbeddingClient instance
    """
    global _embedding_client, _embedding_config_fingerprint
    
    # 1. Get complete configuration (merge environment variables, database config, etc.)
    settings = get_settings()
    config = {
        'model': settings.embedding_model_name,
        'api_key': settings.embedding_api_key or settings.llm_api_key,
        'base_url': settings.embedding_base_url or settings.llm_base_url,
        'dimensions': settings.embedding_dimensions,
        'timeout': 60,
        'max_retries': 3,
    }
    
    # 2. Try to load configuration from database
    if settings.use_db_config:
        db_config = await _load_db_config(type='embedding', scenario=scenario)
        if db_config:
            # Extract dimensions (may be in extra_data)
            if 'extra_data' in db_config and db_config['extra_data']:
                if 'dimensions' in db_config['extra_data']:
                    db_config['dimensions'] = db_config['extra_data']['dimensions']
            config.update(db_config)
            logger.debug(f"Using database Embedding config: model={db_config.get('model')}")
    
    # 3. Generate configuration fingerprint (based on key parameters: model, api_key, base_url)
    current_fingerprint = _get_client_fingerprint(config)
    
    # 4. Check if configuration has changed
    if _embedding_client is None or current_fingerprint != _embedding_config_fingerprint:
        # Configuration changed or first creation
        action = 'Updated' if _embedding_client else 'Created'
        
        from sag.core.ai.embedding import EmbeddingClient
        
        _embedding_client = EmbeddingClient(
            model=config['model'],
            base_url=config.get('base_url'),
            api_key=config.get('api_key')
        )
        _embedding_config_fingerprint = current_fingerprint
        
        logger.info(
            f"🔄 {action} Embedding client: model={config['model']}, "
            f"base_url={config.get('base_url') or 'default'}, "
            f"fingerprint={current_fingerprint[:8]}..."
        )
    else:
        logger.debug(f"♻️ Reusing Embedding client (config unchanged): {config['model']}")
    
    return _embedding_client


def reset_embedding_client() -> None:
    """Reset Embedding client singleton"""
    global _embedding_client, _embedding_config_fingerprint
    _embedding_client = None
    _embedding_config_fingerprint = None
    logger.info("Reset Embedding client")
