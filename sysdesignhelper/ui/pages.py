from __future__ import annotations

import random

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from ..content import Library, Page, RecallPrompt
from .widgets import ClaimView, card, chip, label, scrollable


class RecallDrill(QWidget):
    finished = pyqtSignal()

    def __init__(self, library: Library, prompts: list[RecallPrompt]):
        super().__init__()
        self.library = library
        self.prompts = prompts
        self.index = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)
        back = QPushButton("‹  Back to Pages")
        back.setObjectName("link")
        back.clicked.connect(self.finished.emit)
        layout.addWidget(back, 0, Qt.AlignmentFlag.AlignLeft)
        self.progress = label("", "muted")
        layout.addWidget(self.progress)
        self.prompt = label("", "h2")
        layout.addWidget(self.prompt)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Answer from memory, then reveal.")
        self.editor.setFixedHeight(120)
        layout.addWidget(self.editor)
        row = QHBoxLayout()
        self.reveal_button = QPushButton("Reveal")
        self.reveal_button.setObjectName("primary")
        self.reveal_button.clicked.connect(self.reveal)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next)
        row.addWidget(self.reveal_button)
        row.addWidget(self.next_button)
        row.addStretch(1)
        layout.addLayout(row)
        self.answer_host = QWidget()
        self.answer_layout = QVBoxLayout(self.answer_host)
        self.answer_layout.setContentsMargins(0, 0, 12, 0)
        layout.addWidget(scrollable(self.answer_host), 1)
        self._show()

    def current(self) -> RecallPrompt:
        return self.prompts[self.index]

    def _clear_answer(self) -> None:
        while self.answer_layout.count():
            item = self.answer_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

    def _show(self) -> None:
        prompt = self.current()
        page = self.library.page(prompt.page_id)
        self.progress.setText(f"Recall prompt {self.index + 1} of {len(self.prompts)}  ·  {page.name}")
        self.prompt.setText(prompt.prompt)
        self.editor.clear()
        self._clear_answer()
        self.reveal_button.setEnabled(True)
        self.next_button.setText("Finish" if self.index == len(self.prompts) - 1 else "Next")

    def reveal(self) -> None:
        self._clear_answer()
        frame, box = card()
        for claim in self.current().answer:
            box.addWidget(ClaimView(claim))
        self.answer_layout.addWidget(frame)
        self.answer_layout.addStretch(1)
        self.reveal_button.setEnabled(False)

    def next(self) -> None:
        if self.index == len(self.prompts) - 1:
            self.finished.emit()
            return
        self.index += 1
        self._show()


class PagesView(QWidget):
    def __init__(self, library: Library):
        super().__init__()
        self.library = library
        self.drill: RecallDrill | None = None

        self.listing = QListWidget()
        self.listing.setFixedWidth(280)
        self.listing.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.listing.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.listing.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._add_group("COMPONENTS", library.components.values())
        self._add_group("MECHANISMS", library.mechanisms.values())
        self.drill_button = QPushButton("Drill Recall prompts")
        self.drill_button.setObjectName("primary")
        self.drill_button.clicked.connect(self.start_drill)
        self.drill_hint = label("", "muted")

        left = QVBoxLayout()
        left.setSpacing(8)
        left.addWidget(label("Pages", "h1"))
        left.addWidget(self.listing, 1)
        left.addWidget(self.drill_button)
        left.addWidget(self.drill_hint)

        self.page_host = QWidget()
        self.page_layout = QVBoxLayout(self.page_host)
        self.page_layout.setContentsMargins(0, 0, 12, 0)
        self.page_layout.setSpacing(12)
        browse = QWidget()
        browse_layout = QHBoxLayout(browse)
        browse_layout.setContentsMargins(24, 18, 24, 18)
        browse_layout.setSpacing(20)
        browse_layout.addLayout(left)
        browse_layout.addWidget(scrollable(self.page_host), 1)

        self.stack = QStackedWidget()
        self.stack.addWidget(browse)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.stack)

        self.listing.itemSelectionChanged.connect(self._selection_changed)
        self.listing.setCurrentRow(1)

    def _add_group(self, heading: str, pages) -> None:
        header = QListWidgetItem(heading)
        header.setFlags(Qt.ItemFlag.NoItemFlags)
        self.listing.addItem(header)
        for page in sorted(pages, key=lambda p: p.name):
            item = QListWidgetItem(page.name)
            item.setData(Qt.ItemDataRole.UserRole, page.id)
            self.listing.addItem(item)

    def selected_pages(self) -> list[Page]:
        return [self.library.page(item.data(Qt.ItemDataRole.UserRole)) for item in self.listing.selectedItems()]

    def show_page(self, page_id: str) -> None:
        self._end_drill()
        for row in range(self.listing.count()):
            item = self.listing.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == page_id:
                self.listing.clearSelection()
                self.listing.setCurrentItem(item)
                item.setSelected(True)
                return

    def _selection_changed(self) -> None:
        pages = self.selected_pages()
        prompts = sum(len(page.recall) for page in pages)
        self.drill_button.setEnabled(prompts > 0)
        if len(pages) > 1:
            self.drill_hint.setText(f"{len(pages)} Pages selected: {prompts} Recall prompts, shuffled.")
        else:
            self.drill_hint.setText("Select several Pages (Cmd-click or Shift-click) to drill across them.")
        current = self.listing.currentItem()
        if current is not None and current.data(Qt.ItemDataRole.UserRole):
            self._render(self.library.page(current.data(Qt.ItemDataRole.UserRole)))

    def _render(self, page: Page) -> None:
        while self.page_layout.count():
            item = self.page_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
            elif item.layout() is not None:
                self._discard(item.layout())
        header = QHBoxLayout()
        header.addWidget(label(page.name, "h1", wrap=False))
        header.addWidget(chip(page.kind.capitalize()))
        header.addStretch(1)
        self.page_layout.addLayout(header)

        if page.kind == "component":
            related = [self.library.mechanisms[m] for m in page.mechanisms]
            caption = "Mechanisms inside it:"
        else:
            related = [c for c in self.library.components.values() if page.id in c.mechanisms]
            caption = "Used by:"
        if related:
            row = QHBoxLayout()
            row.addWidget(label(caption, "muted", wrap=False))
            for other in related:
                button = QPushButton(other.name)
                button.setObjectName("link")
                button.clicked.connect(lambda _=False, page_id=other.id: self.show_page(page_id))
                row.addWidget(button)
            row.addStretch(1)
            self.page_layout.addLayout(row)

        for section in page.sections:
            frame, box = card()
            box.addWidget(label(section.heading, "h2"))
            for claim in section.claims:
                box.addWidget(ClaimView(claim))
            self.page_layout.addWidget(frame)
        self.page_layout.addWidget(label(
            f"{len(page.recall)} Recall prompts on this Page. Use the button on the left to drill them.", "muted"))
        self.page_layout.addStretch(1)

    def _discard(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

    def start_drill(self) -> None:
        prompts = [prompt for page in self.selected_pages() for prompt in page.recall]
        if not prompts:
            return
        if len(self.selected_pages()) > 1:
            random.shuffle(prompts)
        self._end_drill()
        self.drill = RecallDrill(self.library, prompts)
        self.drill.finished.connect(self._end_drill)
        self.stack.addWidget(self.drill)
        self.stack.setCurrentWidget(self.drill)

    def _end_drill(self) -> None:
        if self.drill is not None:
            self.stack.removeWidget(self.drill)
            self.drill.deleteLater()
            self.drill = None
        self.stack.setCurrentIndex(0)
