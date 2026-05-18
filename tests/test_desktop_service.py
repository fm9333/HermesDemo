import json
import urllib.error
import urllib.request

from desktop.service_manager import DesktopServiceManager


def _get_json(url: str, token: str | None = None):
    headers = {}
    if token:
        headers["X-Hermes-Token"] = token
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_desktop_service_starts_with_random_port_and_token(tmp_path):
    manager = DesktopServiceManager(app_data_dir=tmp_path)
    state = manager.start(timeout_seconds=15)
    try:
        status, health = _get_json(f"{state.base_url}/api/health")
        assert status == 200
        assert health["status"] == "ok"
        assert state.port != 8000
        assert state.database_path.parent.exists()

        try:
            _get_json(f"{state.base_url}/api/skills")
        except urllib.error.HTTPError as exc:
            assert exc.code == 401
        else:
            raise AssertionError("Expected local API to reject missing token.")

        status, skills = _get_json(f"{state.base_url}/api/skills", token=state.token)
        assert status == 200
        assert any(skill["skill_id"] == "document.summarize" for skill in skills)
    finally:
        manager.stop()

