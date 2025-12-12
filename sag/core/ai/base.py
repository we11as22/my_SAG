"""
LLM client base class

Defines the unified interface for LLM clients
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from sag.core.ai.models import ModelConfig, LLMMessage, LLMResponse, LLMRole
from sag.exceptions import LLMError, LLMTimeoutError
from sag.utils import get_logger

logger = get_logger("ai.llm")


class BaseLLMClient(ABC):
    """LLM client base class"""

    def __init__(self, config: ModelConfig) -> None:
        """
        Initialize LLM client

        Args:
            config: LLM configuration
        """
        self.config = config
        logger.info(
            "Initializing %s client",
            config.provider.value,
            extra={"model": config.model},
        )

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Chat completion

        Args:
            messages: Message list
            temperature: Temperature parameter
            max_tokens: Maximum output tokens
            **kwargs: Other parameters

        Returns:
            LLM response

        Raises:
            LLMError: LLM call failed
            LLMTimeoutError: Call timeout
        """
        ...

    @abstractmethod
    def chat_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        include_reasoning: bool = False,
        **kwargs: Any,
    ) -> AsyncIterator[tuple[str, Optional[str]]]:
        """
        Streaming chat completion

        Args:
            messages: Message list
            temperature: Temperature parameter
            max_tokens: Maximum output tokens
            include_reasoning: Whether to return reasoning content (reasoning_content)
            **kwargs: Other parameters

        Yields:
            Tuple (content, reasoning) - content is content fragment, reasoning is reasoning fragment (if any)

        Raises:
            LLMError: LLM call failed
            LLMTimeoutError: Call timeout
        """
        ...

    async def chat_with_schema(
        self,
        messages: List[LLMMessage],
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Structured output (JSON Schema)

        Args:
            messages: Message list
            response_schema: JSON Schema definition (optional, if not provided only validates JSON format)
            temperature: Temperature parameter
            max_tokens: Maximum output tokens
            **kwargs: Other parameters

        Returns:
            Parsed JSON object

        Raises:
            LLMError: LLM call failed or invalid JSON format
            ValidationError: Response does not match Schema (only when schema is provided)
        """
        import json

        # Build prompt
        if response_schema:
            # Has schema: add detailed schema requirements
            schema_prompt = f"""Please return data according to the following JSON Schema:

                {json.dumps(response_schema, ensure_ascii=False, indent=2)}

**Output Format**:
                ```json
                {{
  "your": "data"
                }}
                ```

**Important**: Your output will be parsed by Python's json.loads(), please ensure:
1. In JSON strings, backslashes \\ must be written as \\\\ (double backslash)
2. For example: LaTeX formula \\( A^* \\) in JSON should be written as "\\\\( A^* \\\\)"
3. Complete example: {{"content": "Prove \\\\( A^* \\\\) algorithm is more efficient"}}

Return only JSON, no other explanations.
            """
        else:
            # No schema: only require JSON format
            schema_prompt = """Please return JSON format data, wrapped in ```json code block.

**Important**: Backslashes \\ in JSON strings must be written as \\\\ (double backslash)
For example: {{"text": "\\\\( formula \\\\)"}}
"""

        # Add schema prompt to message list
        enhanced_messages = [
            LLMMessage(role=LLMRole.SYSTEM, content=schema_prompt),
            *messages,
        ]

        # Call LLM (parameters read from config, not hardcoded)
        response = await self.chat(
            enhanced_messages,
            temperature=temperature,  # Not hardcoded, use passed value or config default
            max_tokens=max_tokens,    # Not hardcoded, use passed value or config default
            **kwargs,
        )

        # Parse JSON response
        try:
            import re
            
            # Extract JSON content (may be wrapped in markdown code block)
            content = response.content.strip()
            
            # Use regex to extract ```json or ``` code block
            json_block_match = re.search(
                r'```(?:json)?\s*\n(.*?)\n```', 
                content, 
                re.DOTALL | re.IGNORECASE
            )
            
            if json_block_match:
                content = json_block_match.group(1).strip()
                logger.debug("Extracted JSON from markdown code block")
            else:
                logger.debug("Directly parsing JSON (no code block)")

            # Parse JSON
            result = json.loads(content)

            # If schema is provided, validate
            if response_schema:
                # Try strict validation with jsonschema
                try:
                    import jsonschema

                    jsonschema.validate(instance=result, schema=response_schema)
                    logger.debug("JSON schema validation passed")
                except ImportError:
                    # jsonschema not installed, use simple validation
                    if "properties" in response_schema:
                        required = response_schema.get("required", [])
                        for field in required:
                            if field not in result:
                                raise ValueError(f"Missing required field: {field}")
                    logger.debug("JSON simple validation passed")
                except Exception as e:
                    # jsonschema validation failed
                    if type(e).__name__ == "ValidationError":
                        logger.error("JSON schema validation failed: %s", e)
                        raise LLMError(f"Response does not match Schema: {e}") from e
                    raise
            else:
                # No schema, only validate JSON format (already passed json.loads)
                logger.debug("JSON format validation passed (no schema provided)")

            return result

        except json.JSONDecodeError as e:
            logger.error("JSON parsing failed: %s\nContent: %s", e, response.content)
            raise LLMError(f"LLM returned invalid JSON: {e}") from e
        except ValueError as e:
            logger.error("Schema validation failed: %s", e)
            raise LLMError(f"Response does not match Schema: {e}") from e

    def _prepare_messages(
        self,
        messages: List[LLMMessage],
    ) -> List[Dict[str, str]]:
        """
        Prepare message list (convert to API format)

        Args:
            messages: Message list

        Returns:
            Message list in API format
        """
        return [msg.to_dict() for msg in messages]


class LLMRetryClient:
    """LLM client wrapper with retry mechanism"""

    def __init__(
        self,
        client: BaseLLMClient,
        max_retries: Optional[int] = None,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ) -> None:
        """
        Initialize retry client

        Args:
            client: Base LLM client
            max_retries: Maximum retry count (None uses client config)
            retry_delay: Initial retry delay (seconds)
            backoff_factor: Backoff factor
        """
        self.client = client
        self.max_retries = max_retries or client.config.max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor

    def _should_retry(self, error: Exception) -> bool:
        """
        Determine if error should be retried

        Args:
            error: Exception object

        Returns:
            True means should retry, False means should not retry
        """
        # Timeout errors don't retry (network issues, retry may continue to timeout)
        if isinstance(error, LLMTimeoutError):
            return False

        # Rate limit errors should retry
        from sag.exceptions import LLMRateLimitError

        if isinstance(error, LLMRateLimitError):
            return True

        # Other LLM errors can retry
        if isinstance(error, LLMError):
            return True

        # Unknown errors default to no retry
        return False

    async def chat(
        self,
        messages: List[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Chat completion with retry

        Implements exponential backoff retry strategy:
        - 1st failure: wait 1 second
        - 2nd failure: wait 2 seconds
        - 3rd failure: wait 4 seconds

        Intelligently decides whether to retry based on error type:
        - Timeout errors: don't retry
        - Rate limit: retry
        - Other LLM errors: retry
        """
        last_error: Optional[Exception] = None
        delay = self.retry_delay

        for attempt in range(self.max_retries + 1):
            try:
                return await self.client.chat(messages, **kwargs)
            except Exception as e:
                last_error = e

                # Determine if should retry
                if not self._should_retry(e):
                    logger.error("Encountered non-retryable error: %s", e)
                    raise

                if attempt < self.max_retries:
                    logger.warning(
                        "LLM call failed, retrying in %s seconds (attempt %d/%d)",
                        delay,
                        attempt + 1,
                        self.max_retries,
                        extra={"error": str(e), "error_type": type(e).__name__},
                    )
                    await asyncio.sleep(delay)
                    delay *= self.backoff_factor
                else:
                    logger.error(
                        "LLM call failed, retried %d times",
                        self.max_retries,
                        exc_info=True,
                    )

        raise LLMError(f"LLM call failed, retried {self.max_retries} times") from last_error

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        **kwargs: Any,
    ) -> AsyncIterator[tuple[str, Optional[str]]]:
        """
        Streaming call (no retry)

        Streaming calls cannot be retried on failure, directly raise exception

        Yields:
            Tuple (content, reasoning) - content is content fragment, reasoning is reasoning fragment (if any)
        """
        async for chunk in self.client.chat_stream(messages, **kwargs):
            yield chunk

    async def chat_with_schema(
        self,
        messages: List[LLMMessage],
        response_schema: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Structured output with retry

        Intelligently decides whether to retry based on error type
        """
        last_error: Optional[Exception] = None
        delay = self.retry_delay

        for attempt in range(self.max_retries + 1):
            try:
                return await self.client.chat_with_schema(
                    messages,
                    response_schema,
                    **kwargs,
                )
            except Exception as e:
                last_error = e

                # Determine if should retry
                if not self._should_retry(e):
                    logger.error("Encountered non-retryable error: %s", e)
                    raise

                if attempt < self.max_retries:
                    logger.warning(
                        "Structured output failed, retrying in %s seconds (attempt %d/%d)",
                        delay,
                        attempt + 1,
                        self.max_retries,
                        extra={"error": str(e), "error_type": type(e).__name__},
                    )
                    await asyncio.sleep(delay)
                    delay *= self.backoff_factor

        raise LLMError(f"Structured output failed, retried {self.max_retries} times") from last_error
