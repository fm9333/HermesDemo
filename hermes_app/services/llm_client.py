from __future__ import annotations

import time
from typing import Any

import httpx

from hermes_app.services.llm_providers import LLMProviderService
from hermes_app.services.prompt_library import PromptLibrary
from hermes_app.services.settings import SettingsService


class LLMClient:
    def __init__(
        self,
        providers: LLMProviderService,
        prompts: PromptLibrary,
        settings: SettingsService | None = None,
    ):
        self.providers = providers
        self.prompts = prompts
        self.settings = settings

    def chat(
        self,
        message: str,
        provider_id: str | None = None,
        prompt_id: str = "hermes.agent.core",
        context: dict | None = None,
        messages: list[dict[str, str]] | None = None,
        contains_file_context: bool = False,
    ) -> dict:
        provider = self.providers.get_runtime(provider_id)
        if not provider:
            return {
                "status": "not_configured",
                "reply": "",
                "message": "未配置可用的 LLM Provider。",
                "provider_id": provider_id,
            }
        if contains_file_context and not self._can_process_file_context(provider):
            return {
                "status": "blocked_by_policy",
                "reply": "",
                "message": "当前策略禁止云模型处理文件内容。请在模型 Provider 和设置中显式允许，或改用本地模型。",
                "provider_id": provider["provider_id"],
                "model": provider["model"],
            }

        system_prompt = self.prompts.render(prompt_id, context=context)
        request_messages = messages or [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]
        payload: dict[str, Any] = {
            "model": provider["model"],
            "messages": request_messages,
            "temperature": provider["temperature"],
        }
        if provider["max_output_tokens"] > 0:
            payload["max_tokens"] = provider["max_output_tokens"]

        start = time.perf_counter()
        safe_request = {
            "model": provider["model"],
            "messages": request_messages,
            "temperature": provider["temperature"],
            "max_tokens": provider["max_output_tokens"],
        }
        try:
            response_json = self._post_json(provider, payload)
            latency_ms = int((time.perf_counter() - start) * 1000)
            reply = self._extract_chat_content(response_json)
            call = self.providers.record_call(
                provider["provider_id"],
                provider["model"],
                prompt_id,
                "ok",
                safe_request,
                response_json,
                latency_ms=latency_ms,
            )
            return {
                "status": "ok",
                "reply": reply,
                "provider_id": provider["provider_id"],
                "model": provider["model"],
                "prompt_id": prompt_id,
                "latency_ms": latency_ms,
                "call_id": call["id"],
                "raw": response_json,
            }
        except Exception as exc:  # noqa: BLE001 - surfaced as provider_error instead of crashing chat.
            latency_ms = int((time.perf_counter() - start) * 1000)
            error = str(exc)
            call = self.providers.record_call(
                provider["provider_id"],
                provider["model"],
                prompt_id,
                "error",
                safe_request,
                {},
                error=error,
                latency_ms=latency_ms,
            )
            return {
                "status": "provider_error",
                "reply": "",
                "provider_id": provider["provider_id"],
                "model": provider["model"],
                "prompt_id": prompt_id,
                "error": error,
                "latency_ms": latency_ms,
                "call_id": call["id"],
            }

    def test_provider(self, provider_id: str) -> dict:
        provider = self.providers.get_runtime(provider_id)
        if not provider:
            raise KeyError(f"Provider not found or disabled: {provider_id}")
        result = self.chat(
            "请只回复 Hermes LLM provider ok",
            provider_id=provider_id,
            prompt_id="hermes.agent.core",
            context={"purpose": "provider connectivity test"},
        )
        return {
            "provider_id": provider_id,
            "status": result["status"],
            "model": result.get("model"),
            "latency_ms": result.get("latency_ms", 0),
            "reply_preview": result.get("reply", "")[:120],
            "error": result.get("error", ""),
            "call_id": result.get("call_id"),
        }

    def _post_json(self, provider: dict, payload: dict) -> dict:
        url = self._endpoint_url(provider)
        headers = {"Content-Type": "application/json"}
        if provider.get("api_key"):
            headers["Authorization"] = f"Bearer {provider['api_key']}"
        with httpx.Client(timeout=provider["timeout_seconds"]) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def _endpoint_url(self, provider: dict) -> str:
        base_url = provider["base_url"].rstrip("/")
        endpoint_path = provider["endpoint_path"] or "/chat/completions"
        if not endpoint_path.startswith("/"):
            endpoint_path = "/" + endpoint_path
        return base_url + endpoint_path

    def _extract_chat_content(self, payload: dict) -> str:
        choices = payload.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict):
                    parts.append(str(part.get("text") or part.get("content") or ""))
                else:
                    parts.append(str(part))
            return "".join(parts).strip()
        return str(content).strip()

    def _can_process_file_context(self, provider: dict) -> bool:
        if provider.get("provider_type") == "local_openai_compatible":
            return True
        global_allowed = False
        if self.settings:
            setting = self.settings.get("llm_allow_cloud_file_context")
            global_allowed = bool(setting and setting["value"])
        return global_allowed and bool(provider.get("allow_file_context"))
