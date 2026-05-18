from hermes_app.core.database import Database
from hermes_app.services.llm_client import LLMClient
from hermes_app.services.llm_providers import LLMProviderService
from hermes_app.services.prompt_library import PromptLibrary
from hermes_app.services.settings import SettingsService


def test_llm_provider_masks_api_key_and_sets_default(tmp_path):
    db = Database(tmp_path / "llm.db")
    db.init()
    service = LLMProviderService(db)

    provider = service.create(
        {
            "provider_id": "openai.test",
            "name": "OpenAI Test",
            "base_url": "https://api.openai.com/v1",
            "model": "test-model",
            "api_key": "sk-test-secret",
        }
    )

    assert provider["provider_id"] == "openai.test"
    assert provider["is_default"] is True
    assert provider["api_key_set"] is True
    assert provider["api_key_preview"] == "sk-t...cret"
    assert "sk-test-secret" not in str(provider)

    runtime = service.get_runtime("openai.test")
    assert runtime["api_key"] == "sk-test-secret"


def test_llm_client_uses_openai_compatible_chat_payload(tmp_path, monkeypatch):
    db = Database(tmp_path / "llm.db")
    db.init()
    providers = LLMProviderService(db)
    providers.create(
        {
            "provider_id": "local.test",
            "name": "Local Test",
            "provider_type": "local_openai_compatible",
            "base_url": "http://127.0.0.1:11434/v1",
            "model": "hermes-test",
            "api_key": "",
        }
    )
    client = LLMClient(providers, PromptLibrary())
    captured = {}

    def fake_post(provider, payload):
        captured["provider"] = provider
        captured["payload"] = payload
        return {"choices": [{"message": {"content": "Hermes LLM provider ok"}}]}

    monkeypatch.setattr(client, "_post_json", fake_post)

    result = client.chat("你好", provider_id="local.test")

    assert result["status"] == "ok"
    assert result["reply"] == "Hermes LLM provider ok"
    assert captured["provider"]["base_url"] == "http://127.0.0.1:11434/v1"
    assert captured["payload"]["model"] == "hermes-test"
    assert captured["payload"]["messages"][0]["role"] == "system"
    assert captured["payload"]["messages"][1] == {"role": "user", "content": "你好"}
    assert providers.list_calls()[0]["status"] == "ok"


def test_cloud_file_context_is_blocked_until_explicitly_allowed(tmp_path, monkeypatch):
    db = Database(tmp_path / "llm.db")
    db.init()
    settings = SettingsService(db)
    providers = LLMProviderService(db)
    providers.create(
        {
            "provider_id": "cloud.test",
            "name": "Cloud Test",
            "base_url": "https://api.openai.com/v1",
            "model": "test-model",
            "api_key": "secret",
            "allow_file_context": False,
        }
    )
    client = LLMClient(providers, PromptLibrary(), settings)

    def fail_post(provider, payload):
        raise AssertionError("cloud provider must not receive file context when policy blocks it")

    monkeypatch.setattr(client, "_post_json", fail_post)

    blocked = client.chat("private file text", provider_id="cloud.test", contains_file_context=True)
    assert blocked["status"] == "blocked_by_policy"

    settings.update("llm_allow_cloud_file_context", True)
    providers.update("cloud.test", {"allow_file_context": True})
    monkeypatch.setattr(
        client,
        "_post_json",
        lambda provider, payload: {"choices": [{"message": {"content": "allowed"}}]},
    )

    allowed = client.chat("private file text", provider_id="cloud.test", contains_file_context=True)
    assert allowed["status"] == "ok"
    assert allowed["reply"] == "allowed"


def test_prompt_library_contains_deep_skill_prompts():
    prompts = PromptLibrary()
    ids = {item["prompt_id"] for item in prompts.list()}

    assert "hermes.agent.core" in ids
    assert "hermes.planner.deep_thinking" in ids
    assert "skill.document.summarize" in ids
    assert "skill.document.contract_extract" in ids
    assert "skill.work.meeting_minutes" in ids
    assert "skill.data.table_analyze" in ids
    assert "skill.email.reply_draft" in ids
    assert "eval.skill_judge" in ids
    assert "隐藏推理过程" in prompts.get("hermes.agent.core").system_prompt
