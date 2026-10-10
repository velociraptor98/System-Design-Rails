from __future__ import annotations

from PyQt6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QMainWindow, QMessageBox, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget,
)

from ..content import Library
from .canvas import CanvasEditor
from .pages import PagesView
from .questions import QuestionsView
from .widgets import label

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
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(10)
        top = QHBoxLayout()
        top.addWidget(label("Sandbox", "h1", wrap=False))
        top.addStretch(1)
        clear = QPushButton("Clear")
        top.addWidget(clear)
        layout.addLayout(top)
        layout.addWidget(label("A Canvas with no Question attached. Nothing here is checked or saved.", "muted"))
        self.editor = CanvasEditor(library)
        clear.clicked.connect(self.editor.scene.clear_design)
        layout.addWidget(self.editor, 1)


class MainWindow(QMainWindow):
    def __init__(self, library: Library):
        super().__init__()
        self.setWindowTitle("System Design Practice")
        # Below this the Canvas is squeezed out between the palette and the inspector.
        self.setMinimumSize(1180, 720)
        self.resize(1360, 860)
        self.confirm = confirm_quit

        self.questions = QuestionsView(library)
        self.pages = PagesView(library)
        self.sandbox = SandboxView(library)
        self.stack = QStackedWidget()
        for view in (self.questions, self.pages, self.sandbox):
            self.stack.addWidget(view)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(196)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(12, 18, 12, 14)
        side.setSpacing(4)
        side.addWidget(label("System Design\nPractice", "appTitle"))
        side.addSpacing(14)
        self.nav = QButtonGroup(self)
        for index, name in enumerate(AREAS):
            button = QPushButton(name)
            button.setObjectName("navButton")
            button.setCheckable(True)
            self.nav.addButton(button, index)
            side.addWidget(button)
        side.addStretch(1)
        side.addWidget(label(
            f"{len(library.questions)} Questions\n"
            f"{len(library.components)} Components\n"
            f"{len(library.mechanisms)} Mechanisms\n"
            f"{len(library.sources)} Primary sources", "muted"))

        central = QWidget()
        row = QHBoxLayout(central)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(sidebar)
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
