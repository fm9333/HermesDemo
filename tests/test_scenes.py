from hermes_app.core.database import Database
from hermes_app.services.scenes import SceneService


def test_scene_service_create_run_pause_flow(tmp_path):
    db = Database(tmp_path / "scenes.db")
    db.init()
    service = SceneService(db)

    scene = service.create(
        "雨天通勤提醒",
        source="idea",
        context_signal="weather.rain",
        opportunity="umbrella_reminder",
        output_type="reminder",
    )
    assert scene["status"] == "active"
    assert service.get_by_source_context("idea", "weather.rain")["id"] == scene["id"]

    run = service.run(scene["id"])
    assert run["status"] == "ok"
    assert run["output"]["type"] == "reminder"

    positive = service.record_feedback(
        scene["id"],
        rating="positive",
        reason="useful",
        run_id=run["run_id"],
        payload={"source": "test"},
    )
    assert positive["rating"] == "positive"
    assert positive["payload"]["source"] == "test"
    assert round(service.get(scene["id"])["effect_score"], 2) == 0.3

    misfire = service.record_feedback(scene["id"], rating="misfire", reason="too noisy")
    assert misfire["rating"] == "misfire"
    assert service.get(scene["id"])["effect_score"] == 0
    assert len(service.list_feedback(scene["id"])) == 2

    paused = service.pause(scene["id"])
    assert paused["status"] == "paused"

    skipped = service.run(scene["id"])
    assert skipped["status"] == "skipped"
