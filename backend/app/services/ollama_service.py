"""Ollama client service managing native tool-calling and model communication."""

import json
import time
from typing import Any, Dict, List, Optional, Union

import ollama

from backend.app.core.config import OLLAMA_HOST, OLLAMA_MODEL
from backend.app.core.constants import EVALUATION_TEMPERATURE
from backend.app.core.exceptions import (
    OllamaAPIError,
    OllamaConnectionError,
    OllamaModelNotFoundError,
)
from backend.app.core.logging import logger
from backend.app.models.tool_models import (
    OllamaHealthResponse,
    OllamaModelResponse,
    ToolDefinition,
    ToolSelectionResult,
)
from backend.app.services.tool_service import load_canonical_tools, tools_to_ollama_format

class OllamaService:
    """Provides high-level, native tool-calling interactions with local Ollama."""

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[ollama.Client] = None,
    ):
        self.host = host or OLLAMA_HOST
        # Model is fixed to configured value; arbitrary runtime overrides are restricted
        self.model = model or OLLAMA_MODEL
        self._client = client

    @property
    def client(self) -> ollama.Client:
        """Lazy-initializes the Ollama client instance."""
        if self._client is None:
            self._client = ollama.Client(host=self.host)
        return self._client

    @client.setter
    def client(self, value: ollama.Client) -> None:
        self._client = value

    def health_check(self) -> OllamaHealthResponse:
        """Checks whether the local Ollama instance is reachable."""
        try:
            self.client.list()
            return OllamaHealthResponse(
                reachable=True,
                host=self.host,
                message="Ollama daemon is reachable.",
            )
        except Exception as exc:
            logger.warning("Ollama health check failed on %s: %s", self.host, exc)
            return OllamaHealthResponse(
                reachable=False,
                host=self.host,
                message=f"Ollama server is unreachable at {self.host}: {exc}",
            )

    def model_available(self) -> OllamaModelResponse:
        """Verifies whether the configured model is installed and ready in Ollama."""
        try:
            res = self.client.list()
            available_names: List[str] = []

            if hasattr(res, "models") and res.models:
                for m in res.models:
                    name = getattr(m, "model", None) or getattr(m, "name", "")
                    if name:
                        available_names.append(name)
            elif isinstance(res, dict) and "models" in res:
                available_names = [m.get("name", "") for m in res["models"]]

            # Allow exact match, name:tag, or tag prefix matching
            is_available = any(
                name == self.model
                or name.startswith(f"{self.model}:")
                or self.model.startswith(f"{name}:")
                for name in available_names
            )

            if is_available:
                message = f"Configured model '{self.model}' is available."
            else:
                message = f"Configured model '{self.model}' not found on host '{self.host}'."

            return OllamaModelResponse(
                available=is_available,
                model=self.model,
                host=self.host,
                available_models=available_names,
                message=message,
            )
        except Exception as exc:
            logger.warning("Ollama model check failed on %s: %s", self.host, exc)
            return OllamaModelResponse(
                available=False,
                model=self.model,
                host=self.host,
                available_models=[],
                message=f"Failed to query Ollama models: {exc}",
            )

    def select_tool(
        self,
        query: str,
        tools: Optional[List[Union[ToolDefinition, Dict[str, Any]]]] = None,
    ) -> ToolSelectionResult:
        """Executes a native tool-calling request against Ollama with temperature=0.0.
        
        Args:
            query: User prompt to evaluate.
            tools: Optional custom tools. If None, uses canonical tools/tools.json.
            
        Returns:
            Normalized ToolSelectionResult with tool_called, tool_name, arguments, etc.
        """
        if tools is None:
            tools = load_canonical_tools()

        formatted_tools = tools_to_ollama_format(tools)

        wall_start = time.perf_counter()
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": query}],
                tools=formatted_tools,
                options={"temperature": EVALUATION_TEMPERATURE},
            )
        except Exception as exc:
            err_str = str(exc)
            logger.error("Ollama chat execution failed: %s", err_str)
            if "ConnectError" in type(exc).__name__ or "connection" in err_str.lower():
                raise OllamaConnectionError(
                    message=f"Could not connect to Ollama daemon at {self.host}.",
                    host=self.host,
                ) from exc
            if "not found" in err_str.lower() or getattr(exc, "status_code", 0) == 404:
                raise OllamaModelNotFoundError(
                    model=self.model,
                    host=self.host,
                ) from exc
            raise OllamaAPIError(
                message=f"Ollama inference error: {err_str}",
            ) from exc

        wall_duration_ms = (time.perf_counter() - wall_start) * 1000.0

        # Duration in milliseconds
        duration_ms: float
        if hasattr(response, "total_duration") and response.total_duration is not None:
            duration_ms = round(response.total_duration / 1e6, 2)
        else:
            duration_ms = round(wall_duration_ms, 2)

        msg = getattr(response, "message", None)
        raw_content = getattr(msg, "content", "") if msg else ""
        tool_calls = getattr(msg, "tool_calls", None) if msg else None

        if tool_calls and len(tool_calls) > 0:
            first_call = tool_calls[0]
            func = getattr(first_call, "function", None)
            tool_name = getattr(func, "name", None) if func else None
            args = getattr(func, "arguments", {}) if func else {}

            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {"raw_arguments": args}

            if not isinstance(args, dict):
                args = {}

            return ToolSelectionResult(
                tool_called=True,
                tool_name=tool_name,
                arguments=args,
                model=self.model,
                raw_response=raw_content,
                duration_ms=duration_ms,
            )

        return ToolSelectionResult(
            tool_called=False,
            tool_name=None,
            arguments=None,
            model=self.model,
            raw_response=raw_content,
            duration_ms=duration_ms,
        )

    def generate_text(
        self,
        messages: List[Dict[str, str]],
        format: Optional[Union[str, Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> str:
        """Executes a chat completion call against Ollama and returns the raw message content."""
        try:
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "options": {"temperature": temperature},
            }
            if format is not None:
                kwargs["format"] = format

            response = self.client.chat(**kwargs)
            msg = getattr(response, "message", None)
            return getattr(msg, "content", "") if msg else ""
        except Exception as exc:
            err_str = str(exc)
            logger.error("Ollama generate_text failed: %s", err_str)
            if "ConnectError" in type(exc).__name__ or "connection" in err_str.lower():
                raise OllamaConnectionError(
                    message=f"Could not connect to Ollama daemon at {self.host}.",
                    host=self.host,
                ) from exc
            if "not found" in err_str.lower() or getattr(exc, "status_code", 0) == 404:
                raise OllamaModelNotFoundError(
                    model=self.model,
                    host=self.host,
                ) from exc
            raise OllamaAPIError(
                message=f"Ollama generation error: {err_str}",
            ) from exc

    def generate_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """Executes a structured JSON chat completion call against Ollama and parses the dictionary."""
        raw_text = self.generate_text(messages=messages, format="json", temperature=temperature)
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Ollama JSON response: %s\nRaw text: %s", exc, raw_text)
            raise OllamaAPIError(
                message=f"Ollama returned invalid JSON: {exc}. Raw content: {raw_text[:200]}"
            ) from exc

# Global default instance
ollama_service = OllamaService()
