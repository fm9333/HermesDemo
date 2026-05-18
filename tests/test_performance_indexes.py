from hermes_app.core.database import Database


def test_database_creates_common_query_indexes(tmp_path):
    db = Database(tmp_path / "indexes.db")
    db.init()

    indexes = {item["name"]: item for item in db.list_indexes()}

    assert "idx_pending_actions_status_created" in indexes
    assert "idx_recommendations_status_created" in indexes
    assert "idx_news_articles_status_published" in indexes
    assert "idx_map_places_query_created" in indexes
    assert indexes["idx_map_places_query_created"]["tbl_name"] == "map_places"
