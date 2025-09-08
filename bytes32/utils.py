import os
import sys
import time
from functools import lru_cache
from httpx import ReadError, RemoteProtocolError
from requests.exceptions import ChunkedEncodingError

import openai

# from openai import OpenAI


import tiktoken

from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from bytes32.trapi import get_llm_client


# client = openai.AzureOpenAI() if openai.api_type == "azure" else openai.OpenAI()
# client = OpenAI(api_key="x", base_url="https://api.deepseek.com")
# client = OpenAI(api_key="x")
# Removed global client initialization - now created per request with model parameter


if sys.version_info >= (3, 12):
    from itertools import batched
else:
    def batched(iterable, n: int):
        """ Yield batches of n elements. """
        batch = []
        for item in iterable:
            batch.append(item)
            if len(batch) == n:
                yield batch
                batch = []

        if batch:
            yield batch


# Cache LLM client per model to avoid recreating it on every call
@lru_cache(maxsize=None)
def _get_cached_client(model: str):
    return get_llm_client(model)


@lru_cache()
def get_tokenizer(model):
    # return tiktoken.encoding_for_model(model)
    """
        获取模型对应的 tokenizer。
        对于不被 tiktoken 支持的模型（如 deepseek-chat），手动指定编码器。
        """
    # 手动支持的模型（DeepSeek 全系列）
    custom_tokenizer_models = {
        "deepseek-chat": "cl100k_base",
        "deepseek-reasoner": "cl100k_base",
    }

    if model in custom_tokenizer_models:
        return tiktoken.get_encoding(custom_tokenizer_models[model])

    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        print(f"[Tokenizer Warning] Unknown model '{model}', falling back to cl100k_base")
        return tiktoken.get_encoding("cl100k_base")

def count_tokens(text, model=None):
    """ Get the number of tokens for a string, measured using tiktoken. """

    model = model or "gpt-4"

    if isinstance(model, str):
        tokenizer = get_tokenizer(model)
    else:
        # Assume model is a namedtuple (model_name, tokenizer)
        tokenizer = model.tokenizer

    return len(tokenizer.encode(text))


@retry(
    reraise=True,
    stop=stop_after_attempt(1000),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=(
        retry_if_exception_type(openai.APIError)
        | retry_if_exception_type(openai.APIConnectionError)
        | retry_if_exception_type(openai.RateLimitError)
    ),
)
def call_gpt(model, stream=False, **kwargs):
    kwargs["temperature"] = 0.0
    kwargs["top_p"] = 1
    kwargs["frequency_penalty"] = 0.0
    kwargs["presence_penalty"] = 0.0
    kwargs["timeout"] = 4*10*60  # 40 minutes
    kwargs["model"] = model
    kwargs["stream"] = stream

    # Get cached client for the specific model
    client, deployment_name = _get_cached_client(model)
    kwargs["model"] = deployment_name
    if "gpt-5" in deployment_name:
        # 'max_tokens' is not supported with gpt-5. Use 'max_completion_tokens' instead.
        kwargs["max_completion_tokens"] = kwargs.pop("max_tokens", None)

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as e:
        print(e)
        raise e

    return response


@retry(
    reraise=True,
    stop=stop_after_attempt(1000),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=(
        retry_if_exception_type(openai.Timeout)
    ),
)
def llm_gpt(prompt, model="gpt-3.5-turbo", n=1, **kwargs):
    response = call_gpt(model=model, messages=[{"role": "user", "content": prompt}], n=n, **kwargs)

    if n == 1:
        choice = response.choices[0]
        output = choice.message.content.strip()
    else:
        output = []
        for choice in response.choices:
            output.append(choice.message.content.strip())

    return output


def stream_llm_gpt(prompt, model="gpt-3.5-turbo", role="user", **kwargs):
    messages = [{"role": role, "content": prompt}]

    response = ""
    while True:
        try:

            stream = call_gpt(stream=True, model=model, messages=messages, **kwargs)
            pbar = tqdm(stream, unit="token", total=kwargs.get("max_tokens", 8*1024), leave=False)
            for chunk in pbar:
                time.sleep(0.01)  # Should help with Errno 104: Connection reset by peer https://stackoverflow.com/questions/383738/104-connection-reset-by-peer-socket-error-or-when-does-closing-a-socket-resu
                chunk_content = chunk.choices[0].delta.content
                # if isinstance(chunk, tuple):
                #     chunk = chunk[1]  # 可能是 (i, chunk) 的结构
                # chunk_content = chunk.choices[0].delta.get("content", "")

                if chunk_content:
                    response += chunk_content
                    pbar.set_postfix_str(f"...{response[-70:]!r}")

                    nb_tokens = count_tokens(chunk_content)
                    pbar.update(nb_tokens)
            else:
                pbar.close()
                break

        except (openai.APITimeoutError, openai.APIError, ChunkedEncodingError, ReadError, RemoteProtocolError) as e:
            if isinstance(e, openai.APIError):
                print("*****", e.type)
                if "An error occurred during streaming" not in e.message:
                    raise e

            # Append the response we received so far to messages.
            if len(messages) == 1:
                messages.append({"role": "assistant", "content": response})

            messages[-1] = {"role": "assistant", "content": response}
            print(e)

    return response


def stream_llm_gpt0(messages, model="gpt-3.5-turbo", **kwargs):
    response_text = ""
    try:
        stream = call_gpt(stream=True, model=model, messages=messages, **kwargs)
        for chunk in stream:
            if hasattr(chunk, "choices"):
                chunk_content = chunk.choices[0].delta.content
                if chunk_content:
                    response_text += chunk_content
    except Exception as e:
        print(f"[Stream Error] {e}")
        raise e
    return response_text


def load_program(filename):
    with open(filename, 'r') as f:
        program = f.read()

    return program


def extract_python_code(raw_response):
    # Postprocess response, keep only the code chunks between "```" and "```"
    # Iterate over all code chunks and return the biggest.
    code = ""
    code_chunks = raw_response.split("```")
    for i in range(1, len(code_chunks), 2):
        code_chunk = code_chunks[i]
        if code_chunk.startswith("python\n"):
            code_chunk = code_chunk[7:]

        if len(code_chunk) > len(code):
            code = code_chunk

    return code


def get_empty_metrics():
    return {
        "validity": {
            "TextGame": False,
            "runnable": False,
            "winnable": False,
            "getTaskDescription": False,
            "generatePossibleActions": False,
            "step": False, # has the member function step
            "calculateScore": False,
            "num_valid_actions": 0,
            "error_msg": '',
        },
        "compliance": {
            "fold": "",
            "experiment": "",
            "passed": False,
            "response_msg": ''
        },
        "winnability": {
            "gpt_done": False,
            "gpt_bug": False,
            "num_actions": 0,
            "score": 0,
            "game_won": False,
            "done": False,
            "step": 0,
            "max_steps": 0,
            "history": [],
            "transcript": "",
            "init_prompt": "",
        },
        "alignment": {
            "score": 0,
            "error_msg": "",
            "evaluations": [],
        },
    }
