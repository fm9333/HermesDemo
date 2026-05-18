import pytest

from hermes_app.core.database import Database
from hermes_app.schemas import MemoryCandidate
from hermes_app.services.memory import MemoryService


def test_memory_candidate_confirm_and_reject(tmp_path):
    db = Database(tmp_path / "memory.db")
    db.init()
    service = MemoryService(db)

    record = service.create_candidate(
        MemoryCandidate(memory_type="preference", key="news", value="喜欢科技新闻"),
        source="test",
    )
    assert record["status"] == "pending"

    item = service.confirm_candidate(record["id"])
    assert item["value"] == "喜欢科技新闻"
    assert service.get_candidate(record["id"])["status"] == "confirmed"

    rejected = service.create_candidate(
        MemoryCandidate(memory_type="preference", key="food", value="不吃香菜"),
        source="test",
    )
    service.reject_candidate(rejected["id"])
    assert service.get_candidate(rejected["id"])["status"] == "rejected"

    with pytest.raises(ValueError):
        service.confirm_candidate(rejected["id"])

