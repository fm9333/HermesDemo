from hermes_app.core.database import Database
from hermes_app.services.wardrobe import WardrobeService


def test_wardrobe_service_crud_archive_flow(tmp_path):
    db = Database(tmp_path / "wardrobe.db")
    db.init()
    service = WardrobeService(db)

    item = service.create("黑色外套", category="outerwear", color="黑色")
    assert item["status"] == "active"

    updated = service.update(item["id"], name="黑色通勤外套", color="黑色")
    assert updated["name"] == "黑色通勤外套"

    archived = service.set_status(item["id"], "archived")
    assert archived["status"] == "archived"

