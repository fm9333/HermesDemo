from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from desktop.shell import HermesDesktopWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Hermes Desktop")
    app.setOrganizationName("Hermes")
    window = HermesDesktopWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

