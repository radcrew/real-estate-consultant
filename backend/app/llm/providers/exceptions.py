"""HTTP errors for LLM providers."""

from __future__ import annotations

from typing import NoReturn

from anthropic import AnthropicError
from anthropic import APITimeoutError as AnthropicAPITimeoutError
from botocore.exceptions import BotoCoreError, ClientError
from openai import APITimeoutError, OpenAIError
from pydantic import ValidationError

from app.utils.exceptions import (
    raise_bad_gateway,
    raise_gateway_timeout,
    raise_service_unavailable,
    raise_unprocessable_entity,
)

# Bedrock is reached through two SDKs: the Anthropic SDK for chat (Messages API) and
# boto3/botocore for embeddings (bedrock-runtime InvokeModel). Both funnel into the same
# raisers, so the failure a caller sees never depends on which client produced it.
BedrockTimeout = AnthropicAPITimeoutError | BotoCoreError
BedrockCallFailure = AnthropicError | BotoCoreError | ClientError

# The self-hosted Qwen model is reached over lambda:Invoke, so only botocore raises here.
QwenCallFailure = BotoCoreError | ClientError


def raise_ai_unavailable() -> NoReturn:
    raise_service_unavailable("AI unavailable")


def raise_embeddings_unavailable() -> NoReturn:
    raise_service_unavailable("Embeddings unavailable")


def raise_hf_api_key_not_configured() -> NoReturn:
    raise_service_unavailable("Hugging Face API key is not configured.")


def raise_openrouter_api_key_not_configured() -> NoReturn:
    raise_service_unavailable("OpenRouter API key is not configured.")


def raise_hf_completion_parse_failed(*, cause: ValidationError) -> NoReturn:
    raise_bad_gateway(
        "We couldn't process the assistant's reply. Please try again in a moment.",
        cause=cause,
    )


def raise_openrouter_completion_parse_failed(*, cause: ValidationError) -> NoReturn:
    raise_bad_gateway(
        "We couldn't process the assistant's reply. Please try again in a moment.",
        cause=cause,
    )


def raise_hf_request_timeout(*, cause: APITimeoutError) -> NoReturn:
    raise_gateway_timeout("Timed out while calling Hugging Face API.", cause=cause)


def raise_openrouter_request_timeout(*, cause: APITimeoutError) -> NoReturn:
    raise_gateway_timeout("Timed out while calling OpenRouter API.", cause=cause)


def raise_hf_openai_error(*, cause: OpenAIError) -> NoReturn:
    raise_bad_gateway(
        "The AI service is temporarily unavailable. Please try again later.",
        cause=cause,
    )


def raise_openrouter_openai_error(*, cause: OpenAIError) -> NoReturn:
    raise_bad_gateway(
        "The AI service is temporarily unavailable. Please try again later.",
        cause=cause,
    )


def raise_hf_structured_refusal(*, refusal: str) -> NoReturn:
    raise_bad_gateway(
        "The AI service was unable to process this request. Please try again later.",
    )


def raise_openrouter_structured_refusal(*, refusal: str) -> NoReturn:
    raise_bad_gateway(
        "The AI service was unable to process this request. Please try again later.",
    )


def raise_hf_structured_reply_incomplete() -> NoReturn:
    raise_bad_gateway(
        "The assistant's reply didn't come through completely. "
        "Please try again in a moment.",
    )


def raise_openrouter_structured_reply_incomplete() -> NoReturn:
    raise_bad_gateway(
        "The assistant's reply didn't come through completely. "
        "Please try again in a moment.",
    )


def raise_bedrock_not_configured() -> NoReturn:
    raise_service_unavailable("AWS region is not configured.")


def raise_bedrock_access_denied(*, cause: BedrockCallFailure) -> NoReturn:
    """Model access is not enabled for this account/region in the Bedrock console."""
    raise_service_unavailable(
        "The AI service is not configured for this account.",
        cause=cause,
    )


def raise_bedrock_rate_limited(*, cause: BedrockCallFailure) -> NoReturn:
    raise_service_unavailable(
        "The AI service is busy right now. Please try again in a moment.",
        cause=cause,
    )


def raise_bedrock_request_timeout(*, cause: BedrockTimeout) -> NoReturn:
    raise_gateway_timeout("Timed out while calling AWS Bedrock.", cause=cause)


def raise_bedrock_api_error(*, cause: BedrockCallFailure) -> NoReturn:
    raise_bad_gateway(
        "The AI service is temporarily unavailable. Please try again later.",
        cause=cause,
    )


def raise_bedrock_completion_parse_failed(*, cause: ValidationError) -> NoReturn:
    raise_bad_gateway(
        "We couldn't process the assistant's reply. Please try again in a moment.",
        cause=cause,
    )


def raise_bedrock_structured_refusal(*, refusal: str) -> NoReturn:
    raise_bad_gateway(
        "The AI service was unable to process this request. Please try again later.",
    )


def raise_bedrock_structured_reply_incomplete() -> NoReturn:
    raise_bad_gateway(
        "The assistant's reply didn't come through completely. "
        "Please try again in a moment.",
    )


def raise_guardrail_blocked() -> NoReturn:
    """Policy refused the text. Deliberately vague about which rule fired.

    Naming the rule tells someone probing the filter exactly what to rephrase, and the
    honest guidance for a legitimate user is the same either way.
    """
    raise_unprocessable_entity(
        "That message can't be processed. Please rephrase it without sensitive personal "
        "details.",
    )


def raise_guardrail_unavailable(*, cause: BedrockCallFailure) -> NoReturn:
    """Screening could not run, and the configuration says not to proceed unscreened."""
    raise_service_unavailable(
        "We couldn't check that message right now. Please try again in a moment.",
        cause=cause,
    )


def raise_qwen_not_configured() -> NoReturn:
    """No region, no function name, or no function by that name to invoke."""
    raise_service_unavailable("The Qwen inference function is not configured.")


def raise_qwen_access_denied(*, cause: QwenCallFailure) -> NoReturn:
    """The caller's IAM policy does not allow invoking the function."""
    raise_service_unavailable(
        "The AI service is not configured for this account.",
        cause=cause,
    )


def raise_qwen_rate_limited(*, cause: QwenCallFailure) -> NoReturn:
    """Lambda concurrency limit reached — transient, and worth one retry."""
    raise_service_unavailable(
        "The AI service is busy right now. Please try again in a moment.",
        cause=cause,
    )


def raise_qwen_circuit_open() -> NoReturn:
    """Recent invocations kept failing, so this one is refused without being attempted.

    Deliberately indistinguishable from being throttled: to the caller both mean "not
    now, try again", and a 503 is what the queued path (§14.1) classifies as retryable.
    """
    raise_service_unavailable("The AI service is busy right now. Please try again in a moment.")


def raise_qwen_request_timeout(*, cause: QwenCallFailure) -> NoReturn:
    raise_gateway_timeout("Timed out while calling the Qwen inference function.", cause=cause)


def raise_qwen_invoke_failed(*, cause: QwenCallFailure) -> NoReturn:
    raise_bad_gateway(
        "The AI service is temporarily unavailable. Please try again later.",
        cause=cause,
    )


def raise_qwen_function_error() -> NoReturn:
    """The function ran and raised.

    Lambda reports this as a 200 with ``FunctionError`` set, so it is a failure only if
    you look — hence a raiser of its own, rather than falling through to the parse path
    holding a stack trace where the completion should be.
    """
    raise_bad_gateway(
        "The AI service is temporarily unavailable. Please try again later.",
    )


def raise_qwen_completion_parse_failed(*, cause: ValidationError) -> NoReturn:
    raise_bad_gateway(
        "We couldn't process the assistant's reply. Please try again in a moment.",
        cause=cause,
    )


def raise_qwen_structured_reply_incomplete() -> NoReturn:
    raise_bad_gateway(
        "The assistant's reply didn't come through completely. "
        "Please try again in a moment.",
    )
