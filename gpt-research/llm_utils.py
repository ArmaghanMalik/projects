from __future__ import annotations

import json
import time

import openai
from langchain.adapters import openai as lc_openai
from colorama import Fore, Style
from openai.error import APIError, RateLimitError

from agent.prompts import auto_agent_instructions
from config import Config

CFG = Config()

OPENAI_API_KEY = ''
openai.api_key = OPENAI_API_KEY

from typing import Optional
import logging

def create_chat_completion(
    messages: list,  # type: ignore
    model: Optional[str] = None,
    temperature: float = CFG.temperature,
    max_tokens: Optional[int] = None
) -> str:
    """Create a chat completion using the OpenAI API
    Args:
        messages (list[dict[str, str]]): The messages to send to the chat completion
        model (str, optional): The model to use. Defaults to None.
        temperature (float, optional): The temperature to use. Defaults to 0.9.
        max_tokens (int, optional): The max tokens to use. Defaults to None.
    Returns:
        str: The response from the chat completion
    """

    # validate input
    if model is None:
        raise ValueError("Model cannot be None")
    if max_tokens is not None and max_tokens > 8001:
        raise ValueError(f"Max tokens cannot be more than 8001, but got {max_tokens}")

    # create response
    for attempt in range(10):  # maximum of 10 attempts
        response = send_chat_completion_request(
            messages, model, temperature, max_tokens
        )
        return response

    logging.error("Failed to get response from OpenAI API")
    raise RuntimeError("Failed to get response from OpenAI API")


def send_chat_completion_request(
    messages, model, temperature, max_tokens
):
    result = lc_openai.ChatCompletion.create(
        openai_api_key=OPENAI_API_KEY,
        model=model, # Change model here to use different models
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        provider="ChatOpenAI", # Change provider here to use a different API
    )
    return result["choices"][0]["message"]["content"]


def choose_agent(task: str) -> str:
    """Determines what agent should be used
    Args:
        task (str): The research question the user asked
    Returns:
        agent - The agent that will be used
        agent_role_prompt (str): The prompt for the agent
    """
    try:
        response = create_chat_completion(
            model=CFG.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{auto_agent_instructions()}"},
                {"role": "user", "content": f"task: {task}"}],
            temperature=0,
        )

        return json.loads(response)
    except Exception as e:
        print(f"{Fore.RED}Error in choose_agent: {e}{Style.RESET_ALL}")
        return {"agent": "Default Agent",
                "agent_role_prompt": "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."}


