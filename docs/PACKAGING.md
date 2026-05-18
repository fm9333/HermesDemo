# Hermes Desktop Packaging

## Windows build

```powershell
python -m pip install -r requirements-desktop.txt
powershell -ExecutionPolicy Bypass -File scripts\build_desktop.ps1
```

The PyInstaller output is written to `dist\HermesDesktop`.

## Included resources

- `desktop/main.py` is the desktop entrypoint.
- `hermes_app/web` is bundled for the local Web UI.
- `README.md` and the product development plan are bundled as reference docs.

## Smoke check after build

```powershell
dist\HermesDesktop\HermesDesktop.exe
```

Expected result: the desktop shell starts, launches the embedded local FastAPI service on a random localhost port, and loads the local UI with a tokenized URL.
