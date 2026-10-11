from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from ..content import Library
from . import icons, theme
from .canvas import CanvasEditor
from .pages import PagesView
from .questions import QuestionsView
from .widgets import Toolbar, button, eyebrow, label

AREAS = ("Questions", "Pages", "Sandbox")


def confirm_quit(parent: QWidget) -> bool:
    answer = QMessageBox.question(
        parent, "Quit and lose your work?",
        "Nothing is saved. Your typed answers and your Designs will be lost.",
        QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
        QMessageBox.StandardButton.Cancel,
    )
    return answer == QMessageBox.StandardButton.Discard


class SandboxView(QWidget):
    def __init__(self, library: Library):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        toolbar = Toolbar("Sandbox", "A canvas with no Question attached. Nothing here is checked or saved.")
        clear = button("Clear")
        toolbar.add_action(clear)
        layout.addWidget(toolbar)
        body = QVBoxLayout()
        body.setContentsMargins(20, 4, 20, 20)
        self.editor = CanvasEditor(library)
        clear.clicked.connect(self.editor.scene.clear_design)
        body.addWidget(self.editor)
        layout.addLayout(body, 1)


class NavButton(QPushButton):
    def __init__(self, text: str, icon_name: str):
        super().__init__(f"  {text}")
        self.caption = text
        self.setObjectName("navButton")
        self.setCheckable(True)
        self.setIconSize(QSize(17, 17))
        self._icons = {
            False: icons.icon(icon_name, theme.TEXT2, 17),
            True: icons.icon(icon_name, theme.LINK, 17),
        }
        self.toggled.connect(lambda checked: self.setIcon(self._icons[checked]))
        self.setIcon(self._icons[False])

    def text(self) -> str:
        return self.caption


class MainWindow(QMainWindow):
    def __init__(self, library: Library):
        super().__init__()
        self.setWindowTitle("System Design Rails")
        # Below this the Canvas is squeezed out between the palette and the inspector.
        self.setMinimumSize(1180, 720)
        self.resize(1280, 860)
        self.confirm = confirm_quit

        self.questions = QuestionsView(library)
        self.pages = PagesView(library)
        self.sandbox = SandboxView(library)
        self.stack = QStackedWidget()
        for view in (self.questions, self.pages, self.sandbox):
            self.stack.addWidget(view)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(224)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(10, 18, 10, 14)
        side.setSpacing(2)
        title = eyebrow("System Design Rails")
        title.setContentsMargins(10, 0, 10, 8)
        side.addWidget(title)
        self.nav = QButtonGroup(self)
        for index, (name, icon_name) in enumerate(zip(AREAS, ("questions", "pages", "sandbox"))):
            nav_button = NavButton(name, icon_name)
            self.nav.addButton(nav_button, index)
            side.addWidget(nav_button)
        side.addStretch(1)
        stats = QGridLayout()
        stats.setContentsMargins(10, 0, 10, 0)
        stats.setVerticalSpacing(3)
        for row, (name, count) in enumerate((
            ("Questions", len(library.questions)),
            ("Components", len(library.components)),
            ("Mechanisms", len(library.mechanisms)),
            ("Primary sources", len(library.sources)),
        )):
            stats.addWidget(label(name, "stat", wrap=False), row, 0)
            stats.addWidget(label(str(count), "statValue", wrap=False), row, 1, Qt.AlignmentFlag.AlignRight)
        side.addLayout(stats)

        central = QWidget()
        central.setObjectName("root")
        row = QHBoxLayout(central)
        row.setContentsMargins(8, 4, 0, 0)
        row.setSpacing(8)
        side_column = QVBoxLayout()
        side_column.setContentsMargins(0, 0, 0, 8)
        side_column.addWidget(sidebar)
        row.addLayout(side_column)
        row.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.nav.idClicked.connect(self.stack.setCurrentIndex)
        self.nav.button(0).setChecked(True)
        self.questions.open_page.connect(self.open_page)
        self.sandbox.editor.open_page.connect(self.open_page)

    def show_area(self, index: int) -> None:
        self.nav.button(index).setChecked(True)
        self.stack.setCurrentIndex(index)

    def open_page(self, page_id: str) -> None:
        self.show_area(AREAS.index("Pages"))
        self.pages.show_page(page_id)

    def has_work(self) -> bool:
        return self.questions.has_work() or not self.sandbox.editor.design.is_empty()

    def closeEvent(self, event) -> None:
        if self.has_work() and not self.confirm(self):
            event.ignore()
            return
        event.accept()
