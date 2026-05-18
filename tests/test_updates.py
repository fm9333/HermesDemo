import json

from hermes_app.core.config import Settings
from hermes_app.core.database import Database
from hermes_app.services.settings import SettingsService
from hermes_app.services.updates import UpdateService


def test_update_service_reports_not_configured_by_default(tmp_path):
    db = Database(tmp_path / "updates.db")
    db.init()
    service = UpdateService(Settings(app_version="0.1.0"), SettingsService(db))

    result = service.check()

    assert result["status"] == "not_configured"
    assert result["current_version"] == "0.1.0"
    assert result["enabled"] is False


def test_update_service_detects_available_manifest(tmp_path):
    db = Database(tmp_path / "updates.db")
    db.init()
    app_settings = SettingsService(db)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"version": "0.2.0", "channel": "stable", "url": "https://example.com/Hermes.exe"}),
        encoding="utf-8",
    )
    app_settings.update("auto_update_enabled", True)
    app_settings.update("update_manifest_url", str(manifest))
    service = UpdateService(Settings(app_version="0.1.0"), app_settings)

    result = service.check()

    assert result["status"] == "update_available"
    assert result["latest_version"] == "0.2.0"
    assert result["manifest"]["url"] == "https://example.com/Hermes.exe"


def test_update_service_respects_channel(tmp_path):
    db = Database(tmp_path / "updates.db")
    db.init()
    app_settings = SettingsService(db)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"version": "0.2.0", "channel": "beta"}), encoding="utf-8")
    app_settings.update("update_manifest_url", str(manifest))
    service = UpdateService(Settings(app_version="0.1.0"), app_settings)

    result = service.check()

    assert result["status"] == "channel_mismatch"
