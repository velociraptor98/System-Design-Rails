from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QMessageBox

from .content import ContentError, load_library
from .ui import theme
from .ui.main_window import MainWindow


def apply_theme(app: QApplication) -> None:
    # Fusion ignores the macOS light/dark setting, which is what keeps the app dark always;
    # the colour scheme hint does the same for the native window chrome.
    app.setStyle("Fusion")
    app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    palette = QPalette()
    for role, color in (
        (QPalette.ColorRole.Window, theme.WIN),
        (QPalette.ColorRole.Base, theme.CARD),
        (QPalette.ColorRole.AlternateBase, theme.NODE),
        (QPalette.ColorRole.Button, theme.NODE),
        (QPalette.ColorRole.WindowText, theme.TEXT),
        (QPalette.ColorRole.Text, theme.TEXT),
        (QPalette.ColorRole.ButtonText, theme.TEXT),
        (QPalette.ColorRole.PlaceholderText, theme.TEXT2),
        (QPalette.ColorRole.ToolTipBase, theme.NODE),
        (QPalette.ColorRole.ToolTipText, theme.TEXT),
        (QPalette.ColorRole.Highlight, theme.ACCENT),
        (QPalette.ColorRole.HighlightedText, "#ffffff"),
        (QPalette.ColorRole.Link, theme.LINK),
    ):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(theme.STYLESHEET)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("System Design Rails")
    apply_theme(app)
    try:
        library = load_library()
    except ContentError as error:
        QMessageBox.critical(None, "Content could not be loaded", str(error))
        return 1
    window = MainWindow(library)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
