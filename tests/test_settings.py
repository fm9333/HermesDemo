from hermes_app.core.database import Database
from hermes_app.services.settings import SettingsService


def test_settings_service_defaults_update_and_validation(tmp_path):
    db = Database(tmp_path / "settings.db")
    db.init()
    service = SettingsService(db)

    settings = {item["key"]: item["value"] for item in service.list()}
    assert settings["autonomy_enabled"] is True
    assert settings["red_zone_policy"] == "block"

    updated = service.update("autonomy_enabled", False)
    assert updated["value"] is False

    try:
        service.update("red_zone_policy", "unsafe")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid red_zone_policy to fail.")

