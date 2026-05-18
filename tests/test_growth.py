from hermes_app.core.database import Database
from hermes_app.services.growth import GrowthLogService


def test_growth_log_service_create_list_rollback(tmp_path):
    db = Database(tmp_path / "growth.db")
    db.init()
    service = GrowthLogService(db)

    log = service.create(
        title="优化摘要模板",
        zone="green",
        source_task="eval",
        impact="提升摘要稳定性",
        payload={"suite_id": "autonomy.zone.basic"},
    )
    assert log["status"] == "active"
    assert log["payload"]["suite_id"] == "autonomy.zone.basic"

    listed = service.list(status="active")
    assert listed[0]["id"] == log["id"]

    rolled_back = service.rollback(log["id"])
    assert rolled_back["status"] == "rolled_back"
    assert rolled_back["rolled_back_at"]

