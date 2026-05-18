from fastapi.testclient import TestClient

from hermes_app.main import app, backup_service, export_service


def test_release_e2e_core_local_product_flow(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_service, "root", tmp_path / "backups")
    monkeypatch.setattr(export_service, "root", tmp_path / "exports")
    backup_service.root.mkdir(parents=True, exist_ok=True)
    export_service.root.mkdir(parents=True, exist_ok=True)

    with TestClient(app) as client:
        chat = client.post("/api/chat", json={"message": "帮我反方挑战 桌面智能体发布验收"})
        assert chat.status_code == 200
        action_id = chat.json()["actions"][0]["id"]

        confirmed = client.post(f"/api/actions/{action_id}/confirm")
        assert confirmed.status_code == 200
        idea_id = confirmed.json()["result"]["idea_id"]

        todo = client.post(f"/api/ideas/{idea_id}/to-todo")
        assert todo.status_code == 200
        assert todo.json()["todos"]

        review = client.post("/api/weekly-reviews/generate")
        assert review.status_code == 200
        assert any(item["idea_id"] == idea_id for item in review.json()["highlights"])

        home = client.get("/api/home/cards")
        assert home.status_code == 200
        home_types = {card["type"] for card in home.json()}
        assert "weekly_review" in home_types

        backup = client.post("/api/backups", json={"note": "e2e"})
        assert backup.status_code == 200
        assert backup.json()["note"] == "e2e"

        export = client.post("/api/exports", json={"note": "e2e", "tables": ["idea_cards", "todo_items"]})
        assert export.status_code == 200
        assert export.json()["tables"] == ["idea_cards", "todo_items"]

        migrations = client.get("/api/database/migrations")
        assert migrations.status_code == 200
        assert migrations.json()

        indexes = client.get("/api/performance/indexes")
        assert indexes.status_code == 200
        assert any(item["name"] == "idx_idea_cards_status_created" for item in indexes.json())

        recovery = client.get("/api/runtime/recovery")
        assert recovery.status_code == 200
        assert recovery.json()["state"]["status"] == "running"
