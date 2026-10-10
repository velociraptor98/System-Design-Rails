from __future__ import annotations

import random

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QFrame, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QStackedWidget,
    QVBoxLayout, QWidget,
)

from ..content import Library, Page, RecallPrompt
from . import icons, theme
from .widgets import (
    EditorCard, Toolbar, add_claims, button, card, chip, clear_layout, discard, label, rule, scrollable,
)

PAGE_ID = Qt.ItemDataRole.UserRole


class RecallDrill(QWidget):
    finished = pyqtSignal()

    def __init__(self, library: Library, prompts: list[RecallPrompt]):
        super().__init__()
        self.library = library
        self.prompts = prompts
        self.index = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.toolbar = Toolbar("", " ", with_back=True)
        self.toolbar.back.connect(self.finished.emit)
        self.next_button = button("Next")
        self.next_button.clicked.connect(self.next)
        self.reveal_button = button("Reveal Answer", "cta", icon_name="reveal", icon_color="#ffffff")
        self.reveal_button.clicked.connect(self.reveal)
        self.toolbar.add_action(self.next_button)
        self.toolbar.add_action(self.reveal_button)
        outer.addWidget(self.toolbar)

        body = QVBoxLayout()
        body.setContentsMargins(32, 4, 32, 32)
        body.setSpacing(16)
        self.prompt = label("", "prompt")
        self.prompt.setMaximumWidth(760)
        body.addWidget(self.prompt)
        row = QHBoxLayout()
        row.setSpacing(14)
        self.card = EditorCard("Answer from memory, then reveal.")
        self.editor = self.card.editor
        row.addWidget(self.card, 5)
        self.answer_host = QWidget()
        self.answer_layout = QVBoxLayout(self.answer_host)
        self.answer_layout.setContentsMargins(0, 0, 10, 0)
        self.answer_area = scrollable(self.answer_host)
        self.answer_area.hide()
        row.addWidget(self.answer_area, 6)
        body.addLayout(row, 1)
        outer.addLayout(body, 1)
        self._show()

    def current(self) -> RecallPrompt:
        return self.prompts[self.index]

    def _show(self) -> None:
        prompt = self.current()
        page = self.library.page(prompt.page_id)
        self.toolbar.title.setText(f"Recall prompt {self.index + 1} of {len(self.prompts)}")
        self.toolbar.set_subtitle(page.name)
        self.prompt.setText(prompt.prompt)
        self.editor.clear()
        clear_layout(self.answer_layout)
        self.answer_area.hide()
        self.reveal_button.setEnabled(True)
        self.next_button.setText("Finish" if self.index == len(self.prompts) - 1 else "Next")

    def reveal(self) -> None:
        clear_layout(self.answer_layout)
        frame, box = card()
        box.addWidget(label("Answer", "h2"))
        add_claims(box, self.current().answer)
        self.answer_layout.addWidget(frame)
        self.answer_layout.addStretch(1)
        self.answer_area.show()
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

        toolbar = Toolbar("Pages")
        self.drill_button = button("Drill Recall Prompts", "cta", icon_name="drill", icon_color="#ffffff")
        self.drill_button.clicked.connect(self.start_drill)
        toolbar.add_action(self.drill_button)

        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("Search")
        self.search.addAction(icons.icon("search", theme.TEXT3, 14), QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(self._filter)
        self.listing = QListWidget()
        self.listing.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listing.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.listing.setTextElideMode(Qt.TextElideMode.ElideRight)
        self._add_group("COMPONENTS", library.components.values())
        self._add_group("MECHANISMS", library.mechanisms.values())
        self.drill_hint = label("", "hint")

        index = QFrame()
        index.setObjectName("card")
        index.setFixedWidth(264)
        column = QVBoxLayout(index)
        column.setContentsMargins(0, 10, 0, 0)
        column.setSpacing(4)
        search_row = QHBoxLayout()
        search_row.setContentsMargins(10, 0, 10, 0)
        search_row.addWidget(self.search)
        column.addLayout(search_row)
        column.addWidget(self.listing, 1)
        column.addWidget(rule())
        self.drill_hint.setContentsMargins(14, 8, 14, 10)
        column.addWidget(self.drill_hint)

        self.page_host = QWidget()
        self.page_layout = QVBoxLayout(self.page_host)
        self.page_layout.setContentsMargins(0, 0, 10, 0)
        self.page_layout.setSpacing(14)

        browse = QWidget()
        browse_layout = QVBoxLayout(browse)
        browse_layout.setContentsMargins(0, 0, 0, 0)
        browse_layout.setSpacing(0)
        browse_layout.addWidget(toolbar)
        columns = QHBoxLayout()
        columns.setContentsMargins(20, 0, 20, 20)
        columns.setSpacing(14)
        columns.addWidget(index)
        columns.addWidget(scrollable(self.page_host), 1)
        browse_layout.addLayout(columns, 1)

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
        font = header.font()
        font.setPixelSize(11)
        font.setWeight(QFont.Weight.DemiBold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.3)
        header.setFont(font)
        self.listing.addItem(header)
        for page in sorted(pages, key=lambda p: p.name):
            item = QListWidgetItem(page.name)
            item.setData(PAGE_ID, page.id)
            self.listing.addItem(item)

    def _filter(self, text: str) -> None:
        needle = text.strip().casefold()
        for row in range(self.listing.count()):
            item = self.listing.item(row)
            if item.data(PAGE_ID):
                item.setHidden(bool(needle) and needle not in item.text().casefold())

    def selected_pages(self) -> list[Page]:
        return [self.library.page(item.data(PAGE_ID)) for item in self.listing.selectedItems()]

    def show_page(self, page_id: str) -> None:
        self._end_drill()
        self.search.clear()
        for row in range(self.listing.count()):
            item = self.listing.item(row)
            if item.data(PAGE_ID) == page_id:
                self.listing.clearSelection()
                self.listing.setCurrentItem(item)
                item.setSelected(True)
                return

    def _selection_changed(self) -> None:
        pages = self.selected_pages()
        prompts = sum(len(page.recall) for page in pages)
        self.drill_button.setEnabled(prompts > 0)
        if len(pages) > 1:
            self.drill_hint.setText(f"{len(pages)} pages selected: {prompts} Recall prompts, shuffled.")
        else:
            self.drill_hint.setText("Select several pages (⌘-click or Shift-click) to drill across them.")
        current = self.listing.currentItem()
        if current is not None and current.data(PAGE_ID):
            self._render(self.library.page(current.data(PAGE_ID)))

    def _render(self, page: Page) -> None:
        clear_layout(self.page_layout)
        heading = QVBoxLayout()
        heading.setContentsMargins(4, 0, 4, 4)
        heading.setSpacing(12)
        title = QHBoxLayout()
        title.setSpacing(12)
        title.addWidget(label(page.name, "h1", wrap=False))
        title.addWidget(chip(page.kind.capitalize()), 0, Qt.AlignmentFlag.AlignVCenter)
        title.addStretch(1)
        heading.addLayout(title)

        if page.kind == "component":
            related = [self.library.mechanisms[m] for m in page.mechanisms]
            caption = "Mechanisms inside it"
        else:
            related = [c for c in self.library.components.values() if page.id in c.mechanisms]
            caption = "Used by"
        if related:
            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(label(caption, "muted", wrap=False))
            for other in related:
                link = button(other.name, "chipLink")
                link.clicked.connect(lambda _=False, page_id=other.id: self.show_page(page_id))
                row.addWidget(link)
            row.addStretch(1)
            heading.addLayout(row)
        self.page_layout.addLayout(heading)

        for section in page.sections:
            frame, box = card()
            box.addWidget(label(section.heading, "h2"))
            add_claims(box, section.claims)
            self.page_layout.addWidget(frame)
        footer = label(f"{len(page.recall)} Recall prompts on this page.", "hint")
        footer.setContentsMargins(4, 0, 4, 0)
        self.page_layout.addWidget(footer)
        self.page_layout.addStretch(1)

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
            discard(self.drill)
            self.drill = None
        self.stack.setCurrentIndex(0)
