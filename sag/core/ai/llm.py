"""
OpenAI LLM client implementation

Note:
- Supports standard OpenAI models (sophnet/Qwen3-30B-A3B-Thinking-2507, gpt-3.5-turbo, etc.)
- Supports thinking models (Thinking Models): Some models (like Qwen3-30B-A3B-Thinking) place
  the reasoning process in the reasoning_content field instead of the content field. This implementation
  automatically detects and handles this situation.
"""

from typing import Any, AsyncIterator, Iterable, List, Optional, cast

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)
from openai.types.chat import ChatCompletionMessageParam

from sag.core.ai.base import BaseLLMClient
from sag.core.ai.models import ModelConfig, LLMMessage, LLMProvider, LLMResponse, LLMUsage
from sag.exceptions import LLMError, LLMRateLimitError, LLMTimeoutError
from sag.utils import get_logger

logger = get_logger("ai.openai")


class OpenAIClient(BaseLLMClient):
    """OpenAI client implementation"""

    def __init__(self, config: ModelConfig) -> None:
        """
        Initialize OpenAI client

        Args:
            config: LLM configuration
        """
        super().__init__(config)

        # Create AsyncOpenAI client
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )

    async def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        OpenAI chat completion

        Args:
            messages: Message list
            temperature: Temperature parameter
            max_tokens: Maximum output tokens
            **kwargs: Other parameters

        Returns:
            LLM response

        Raises:
            LLMError: Call failed
            LLMTimeoutError: Call timeout
            LLMRateLimitError: Rate limit
        """
        try:
            # Prepare messages
            api_messages = self._prepare_messages(messages)

            # Log model information used
            logger.info(
                "🤖 Calling LLM - Model: %s, base_url: %s, temperature: %.2f, max_tokens: %s, timeout: %s",
                self.config.model,
                self.config.base_url,
                temperature or self.config.temperature,
                max_tokens or self.config.max_tokens or "Not set",
                self.config.timeout,
            )

            # Call API (use cast for explicit type conversion)
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=cast(Iterable[ChatCompletionMessageParam], api_messages),
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,  # Read from config, not hardcoded
                **kwargs,
            )

            # Parse response
            choice = response.choices[0]
            usage = response.usage

            # Process response content
            content = choice.message.content
            reasoning = getattr(choice.message, "reasoning_content", None)

            logger.debug(
                "OpenAI response: content=%s, reasoning_content=%s, finish_reason=%s",
                choice.message.content,
                reasoning,
                choice.finish_reason,
            )

            return LLMResponse(
                content=content or "",
                model=response.model,
                usage=LLMUsage(
                    prompt_tokens=usage.prompt_tokens if usage else 0,
                    completion_tokens=usage.completion_tokens if usage else 0,
                    total_tokens=usage.total_tokens if usage else 0,
                ),
                finish_reason=choice.finish_reason or "stop",
            )

        except APITimeoutError as e:
            logger.error(
                "❌ OpenAI call timeout - Model: %s, base_url: %s, timeout: %s, error: %s",
                self.config.model,
                self.config.base_url,
                self.config.timeout,
                e,
            )
            raise LLMTimeoutError(f"OpenAI call timeout: {e}") from e
        except RateLimitError as e:
            logger.error(
                "❌ OpenAI rate limit - Model: %s, error: %s",
                self.config.model,
                e,
            )
            raise LLMRateLimitError(f"OpenAI rate limit: {e}") from e
        except (APIError, APIConnectionError) as e:
            logger.error(
                "❌ OpenAI call failed - Model: %s, base_url: %s, error: %s",
                self.config.model,
                self.config.base_url,
                e,
                exc_info=True,
            )
            raise LLMError(f"OpenAI call failed: {e}") from e
        except Exception as e:
            logger.error("Unknown error: %s", e, exc_info=True)
            raise LLMError(f"OpenAI call failed: {e}") from e

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        include_reasoning: bool = False,
        **kwargs: Any,
    ) -> AsyncIterator[tuple[str, Optional[str]]]:
        """
        OpenAI streaming chat completion

        Args:
            messages: Message list
            temperature: Temperature parameter
            max_tokens: Maximum output tokens
            include_reasoning: Whether to return reasoning content (reasoning_content)
            **kwargs: Other parameters

        Yields:
            Tuple (content, reasoning) - content is content fragment, reasoning is reasoning fragment (if any)

        Raises:
            LLMError: Call failed
        """
        try:
            # Log model information used (add max_tokens)
            logger.info(
                "🤖 Calling streaming LLM - Model: %s, base_url: %s, temperature: %.2f, max_tokens: %s, timeout: %s",
                self.config.model,
                self.config.base_url,
                temperature or self.config.temperature,
                max_tokens or self.config.max_tokens or "Not set",
                self.config.timeout,
            )

            # Prepare messages
            api_messages = self._prepare_messages(messages)

            # Call streaming API (use cast for explicit type conversion)
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                messages=cast(Iterable[ChatCompletionMessageParam], api_messages),
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stream=True,
                **kwargs,
            )

            # Generate content fragments one by one
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    content = delta.content if delta.content else None
                    reasoning = None

                    # If reasoning content is needed, try to get reasoning_content
                    if include_reasoning:
                        reasoning = getattr(delta, "reasoning_content", None)

                    # Only yield if there is content or reasoning
                    if content or reasoning:
                        yield (content or "", reasoning)

        except APITimeoutError as e:
            logger.error("OpenAI streaming call timeout: %s", e)
            raise LLMTimeoutError(f"OpenAI streaming call timeout: {e}") from e
        except (APIError, APIConnectionError) as e:
            logger.error("OpenAI streaming call failed: %s", e, exc_info=True)
            raise LLMError(f"OpenAI streaming call failed: {e}") from e
        except Exception as e:
            logger.error("Unknown error: %s", e, exc_info=True)
            raise LLMError(f"OpenAI streaming call failed: {e}") from e


async def create_openai_client(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    api_key: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
) -> OpenAIClient:
    """
    Create OpenAI client (read default values from environment variables)

    Args:
        api_key: API key
        model: Model name (optional, default read from environment variables)
        base_url: Base URL (optional, default read from environment variables)
        temperature: Temperature parameter (optional, default read from environment variables)
        max_tokens: Maximum output tokens (optional, default read from environment variables)
        timeout: Timeout (seconds) (optional, default read from environment variables)
        max_retries: Maximum retry count (optional, default read from environment variables)

    Returns:
        OpenAI client instance
    """
    from sag.core.config.settings import get_settings
    settings = get_settings()
    
    config = ModelConfig(
        provider=LLMProvider.OPENAI,
        model=model or settings.llm_model,
        api_key=api_key,
        base_url=base_url or settings.llm_base_url,
        temperature=temperature or settings.llm_temperature,
        max_tokens=max_tokens or settings.llm_max_tokens,
        top_p=settings.llm_top_p,
        frequency_penalty=settings.llm_frequency_penalty,
        presence_penalty=settings.llm_presence_penalty,
        timeout=timeout or settings.llm_timeout,
        max_retries=max_retries or settings.llm_max_retries,
    )

    return OpenAIClient(config)
