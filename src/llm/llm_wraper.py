import logging
import os
from typing import Optional, TypeVar, Union

import openai
import tiktoken
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PydanticModelType = TypeVar("PydanticModelType ", bound=BaseModel)

DISPLAY_TOKENS = True

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in a text string for a given model.

    Args:
        text: The text to count tokens for
        model: The model to use for token counting

    Returns:
        Number of tokens

    Raises:
        ValueError: If the model is not supported
    """
    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except KeyError as e:
        raise ValueError(f"Unsupported model for token counting: {model}") from e


def generate_chat_response(
    base_prompt: str,
    task_prompt: str,
    model: str,
    temperature: float = 0.7,
    structured_output: Optional[PydanticModelType] = None,
    max_tokens: Optional[int] = None,
    display_tokens: bool = DISPLAY_TOKENS,
) -> Union[str, PydanticModelType]:
    """
    Generate a chat completion using OpenAI's API.

    Args:
        base_prompt: The system prompt to guide the model's behavior
        task_prompt: The user's input prompt
        model: The model to use for completion
        temperature: Controls randomness (0.0 to 1.0)
        structured_output: Optional Pydantic model for structured output
        display_tokens: Whether to display token counts

    Returns:
        Either a string response or a parsed Pydantic model instance

    Raises:
        ValueError: If parameters are invalid
        openai.OpenAIError: If there's an API error
    """
    # Parameter validation
    if not 0 <= temperature <= 1:
        raise ValueError("Temperature must be between 0 and 1")
    if not base_prompt or not task_prompt:
        raise ValueError("Prompts cannot be empty")
    if not model:
        raise ValueError("Model name cannot be empty")

    # Common message structure
    messages = [
        {"role": "system", "content": base_prompt},
        {"role": "user", "content": task_prompt},
    ]

    try:

        if structured_output:
            completion = client.beta.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=structured_output,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            result = completion.choices[0].message.parsed
        else:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            result = completion.choices[0].message.content

        if display_tokens:
            input_tokens = count_tokens(base_prompt) + count_tokens(task_prompt)
            logger.info(f"{input_tokens} tokens as input for model {model}")
            output_tokens = count_tokens(str(result))
            logger.info(f"{output_tokens} tokens as output for model {model}")

        return result

    except openai.OpenAIError as e:
        raise openai.OpenAIError(f"OpenAI API error: {str(e)}") from e
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}") from e
