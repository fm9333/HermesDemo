from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pyinstaller_spec_declares_desktop_entry_and_web_assets():
    spec = (ROOT / "packaging" / "hermes_desktop.spec").read_text(encoding="utf-8")

    assert "desktop" in spec
    assert "main.py" in spec
    assert "HermesDesktop" in spec
    assert "hermes_app\" / \"web" in spec
    assert "uvicorn.protocols.http.auto" in spec


def test_desktop_build_script_targets_packaging_spec():
    script = (ROOT / "scripts" / "build_desktop.ps1").read_text(encoding="utf-8")

    assert "packaging\\hermes_desktop.spec" in script
    assert "python -m PyInstaller" in script


def test_desktop_requirements_include_pyinstaller():
    requirements = (ROOT / "requirements-desktop.txt").read_text(encoding="utf-8").lower()

    assert "pyinstaller" in requirements
    assert "pyside6" in requirements
