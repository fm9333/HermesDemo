from hermes_app.core.database import Database
from hermes_app.services.scenes import SceneService


def test_scene_service_create_run_pause_flow(tmp_path):
    db = Database(tmp_path / "scenes.db")
    db.init()
    service = SceneService(db)

    scene = service.create(
        "雨天通勤提醒",
        context_signal="weather.rain",
        opportunity="umbrella_reminder",
        output_type="reminder",
    )
    assert scene["status"] == "active"

    run = service.run(scene["id"])
    assert run["status"] == "ok"
    assert run["output"]["type"] == "reminder"

    paused = service.pause(scene["id"])
    assert paused["status"] == "paused"

    skipped = service.run(scene["id"])
    assert skipped["status"] == "skipped"

