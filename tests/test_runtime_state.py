from hermes_app.services.runtime_state import RuntimeStateService


def test_runtime_state_detects_unclean_shutdown(tmp_path):
    first = RuntimeStateService(tmp_path)
    first.start()

    second = RuntimeStateService(tmp_path)

    recovery = second.status()["recovery"]
    assert recovery["status"] == "recovered"
    assert recovery["reason"] == "previous_runtime_not_cleanly_stopped"
    assert recovery["previous_pid"]


def test_runtime_state_records_clean_shutdown(tmp_path):
    service = RuntimeStateService(tmp_path)
    service.start()
    service.mark_clean_shutdown()

    restarted = RuntimeStateService(tmp_path)

    assert restarted.status()["recovery"]["status"] == "clean"
