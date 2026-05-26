import logging
import os
import time
from typing import List, Optional

import requests
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

logger = logging.getLogger(__name__)


# =========================
# OLLAMA CONNECTOR
# =========================

class OllamaChatCompletion(ChatCompletionClientBase):
    """
    Lightweight Ollama connector for Semantic Kernel (production-safe version)
    """

    service_id: str = "ollama_chat"
    model_id: str = "gemma3:1b"
    base_url: str = "http://localhost:11434"

    @property
    def ai_model_id(self) -> str:
        return self.model_id

    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: PromptExecutionSettings,
        **kwargs
    ) -> List[ChatMessageContent]:

        messages = []
        for msg in chat_history.messages:
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            content = getattr(msg, "content", str(msg))

            if role in ["system", "user", "assistant"]:
                messages.append({"role": role, "content": content})

        payload = {
            "model": self.model_id,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": getattr(settings, "temperature", 0.7),
                "num_predict": getattr(settings, "max_tokens", 512),
            },
        }

        url = f"{self.base_url.rstrip('/')}/api/chat"

        max_retries = 3
        timeout = 120

        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, timeout=timeout)

                if response.status_code == 404:
                    raise Exception(f"Model not found: {self.model_id}")

                if response.status_code >= 400:
                    raise Exception(f"Ollama error: {response.text}")

                data = response.json()
                content = data.get("message", {}).get("content", "")

                return [ChatMessageContent(role=AuthorRole.ASSISTANT, content=content)]

            except requests.exceptions.ReadTimeout:
                logger.warning(f"Ollama timeout attempt {attempt + 1}")
                time.sleep(2 ** attempt)

            except requests.exceptions.ConnectionError:
                raise Exception("Cannot connect to Ollama. Run: `ollama serve`")

            except Exception as e:
                logger.exception(f"Ollama error: {e}")
                raise

        return [
            ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content="Sorry, the AI model is not responding right now."
            )
        ]

    async def get_streaming_chat_message_contents(
        self, chat_history: ChatHistory, settings: PromptExecutionSettings, **kwargs
    ):
        messages = await self.get_chat_message_contents(chat_history, settings, **kwargs)
        for msg in messages:
            yield [msg]


# =========================
# KERNEL FACTORY
# =========================

def create_kernel_ollama(
    model: Optional[str] = None,
    base_url: Optional[str] = None
) -> Kernel:

    model = model or os.getenv("OLLAMA_MODEL", "gemma3:1b")
    base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    kernel = Kernel()

    ollama_service = OllamaChatCompletion(
        model_id=model,
        base_url=base_url
    )

    kernel.add_service(ollama_service)

    logger.info(f"Ollama Kernel initialized: {model} @ {base_url}")

    return kernel


# =========================
# HUGGING FACE INFERENCE (router API)
# =========================

class HuggingFaceChatCompletion(ChatCompletionClientBase):
    """
    Hugging Face Inference Providers — OpenAI-compatible chat API.
    https://router.huggingface.co/v1/chat/completions
    """

    service_id: str = "huggingface_chat"
    model_id: str = "Qwen/Qwen2.5-7B-Instruct"
    api_key: str = ""
    base_url: str = "https://router.huggingface.co/v1"

    @property
    def ai_model_id(self) -> str:
        return self.model_id

    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: PromptExecutionSettings,
        **kwargs
    ) -> List[ChatMessageContent]:

        if not self.api_key:
            return [
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    content="Hugging Face API key is not configured. Set HF_API_TOKEN in .env",
                )
            ]

        messages = []
        for msg in chat_history.messages:
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            content = getattr(msg, "content", str(msg))
            if role in ("system", "user", "assistant"):
                messages.append({"role": role, "content": content})

        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": int(getattr(settings, "max_tokens", 512) or 512),
            "temperature": float(getattr(settings, "temperature", 0.7) or 0.7),
            "stream": False,
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)

            if response.status_code == 401:
                raise Exception("Invalid Hugging Face API token. Check HF_API_TOKEN in .env")

            if response.status_code == 503:
                data = response.json() if response.text else {}
                err = data.get("error", response.text)
                return [
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        content=f"The model is loading on Hugging Face. Please try again in a moment. ({err})",
                    )
                ]

            if response.status_code >= 400:
                raise Exception(f"Hugging Face API error ({response.status_code}): {response.text}")

            data = response.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            if not content:
                content = "Sorry, I did not receive a valid response from the model."

            return [ChatMessageContent(role=AuthorRole.ASSISTANT, content=content)]

        except requests.exceptions.ConnectionError:
            raise Exception("Cannot reach Hugging Face API. Check your internet connection.")

        except Exception as e:
            logger.exception("Hugging Face chat error: %s", e)
            return [
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    content=f"Sorry, the AI model returned an error: {e}",
                )
            ]

    async def get_streaming_chat_message_contents(
        self, chat_history: ChatHistory, settings: PromptExecutionSettings, **kwargs
    ):
        messages = await self.get_chat_message_contents(chat_history, settings, **kwargs)
        for msg in messages:
            yield [msg]


def create_kernel_huggingface(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Kernel:
    try:
        from django.conf import settings as django_settings

        model = model or getattr(django_settings, "HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        api_key = api_key or getattr(django_settings, "HF_API_KEY", "")
        base_url = base_url or getattr(django_settings, "HF_BASE_URL", "https://router.huggingface.co/v1")
    except Exception:
        model = model or os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        api_key = api_key or os.getenv("HF_API_TOKEN", "") or os.getenv("HF_API_KEY", "")
        base_url = base_url or os.getenv("HF_BASE_URL", "https://router.huggingface.co/v1")

    kernel = Kernel()
    hf_service = HuggingFaceChatCompletion(
        model_id=model,
        api_key=api_key,
        base_url=base_url,
    )
    kernel.add_service(hf_service)
    logger.info("Hugging Face Kernel initialized: %s", model)
    return kernel


def create_kernel(
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Kernel:
    """
    Create Semantic Kernel with the configured LLM provider.
    Set LLM_PROVIDER=huggingface|ollama in .env
    """
    try:
        from django.conf import settings as django_settings

        provider = (provider or getattr(django_settings, "LLM_PROVIDER", "ollama")).lower()
    except Exception:
        provider = (provider or os.getenv("LLM_PROVIDER", "ollama")).lower()

    if provider in ("huggingface", "hf"):
        return create_kernel_huggingface(model=model)

    return create_kernel_ollama(model=model)
