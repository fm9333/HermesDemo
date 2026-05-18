from hermes_app.core.database import Database
from hermes_app.services.memory import MemoryService
from hermes_app.services.tools import ToolRegistry


def test_tool_registry_lists_whitelisted_tools(tmp_path):
    db = Database(tmp_path / "tools.db")
    db.init()
    registry = ToolRegistry(db, MemoryService(db))

    tools = registry.list()
    tool_ids = {tool.tool_id for tool in tools}

    assert "reminder.create" in tool_ids
    assert "memory.confirm_candidate" in tool_ids
    assert all(tool.enabled for tool in tools)


def test_tool_registry_blocks_unknown_tool(tmp_path):
    db = Database(tmp_path / "tools.db")
    db.init()
    registry = ToolRegistry(db, MemoryService(db))

    result = registry.execute("unknown.tool", {})

    assert result["status"] == "blocked"
