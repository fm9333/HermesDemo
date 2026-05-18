from hermes_app.core.database import Database
from hermes_app.services.autonomy import AutonomyZoneClassifier
from hermes_app.services.evals import EvalRunner


def test_eval_runner_runs_and_records_autonomy_suite(tmp_path):
    db = Database(tmp_path / "evals.db")
    db.init()
    runner = EvalRunner(db, AutonomyZoneClassifier())

    suites = runner.list_suites()
    assert suites[0]["suite_id"] == "autonomy.zone.basic"

    run = runner.run("autonomy.zone.basic")
    assert run["status"] == "passed"
    assert run["score"] == 1
    assert len(run["results"]) == 3

    runs = runner.list_runs(suite_id="autonomy.zone.basic")
    assert runs[0]["id"] == run["id"]

