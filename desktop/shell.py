from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QStyle, QSystemTrayIcon

from desktop.service_manager import DesktopServiceManager, DesktopServiceState


class HermesDesktopWindow(QMainWindow):
    def __init__(self, service_manager: DesktopServiceManager | None = None):
        super().__init__()
        self.service_manager = service_manager or DesktopServiceManager()
        self.service_state: DesktopServiceState = self.service_manager.start()
        self._allow_quit = False
        self.tray: QSystemTrayIcon | None = None

        self.setWindowTitle("Hermes Desktop")
        self.resize(1280, 820)
        self.setMinimumSize(1040, 680)

        self.web_view = QWebEngineView(self)
        self.web_view.setUrl(QUrl(self.service_state.client_url))
        self.setCentralWidget(self.web_view)
        self.statusBar().showMessage(
            f"Hermes local service: {self.service_state.base_url} · data: {self.service_state.app_root}"
        )

        self._setup_tray()

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = self._default_icon()
        self.setWindowIcon(icon)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("Hermes Desktop")

        menu = QMenu()
        show_action = QAction("打开 Hermes", self)
        show_action.triggered.connect(self.show_window)
        reload_action = QAction("刷新界面", self)
        reload_action.triggered.connect(self.web_view.reload)
        quit_action = QAction("退出 Hermes", self)
        quit_action.triggered.connect(self.quit_application)

        menu.addAction(show_action)
        menu.addAction(reload_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _default_icon(self) -> QIcon:
        return self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_window()

    def show_window(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_quit or not self.tray:
            self.service_manager.stop()
            event.accept()
            return

        event.ignore()
        self.hide()
        self.tray.showMessage("Hermes 仍在运行", "可从系统托盘重新打开或退出。", QSystemTrayIcon.MessageIcon.Information, 3000)

    def quit_application(self) -> None:
        self._allow_quit = True
        self.service_manager.stop()
        QApplication.instance().quit()

