from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup, QCheckBox, QGridLayout, QHBoxLayout, QPlainTextEdit, QPushButton, QSplitter,
    QStackedWidget, QTabWidget, QVBoxLayout, QWidget,
)

from ..checks import run_checks
from ..content import Library, Question, Scope
from .canvas import CanvasEditor, CanvasView, DesignScene
from .widgets import AnswerPanel, ClaimView, card, chip, label, link_html, link_label, scrollable

STAGES = ("Requirements", "Estimates", "API", "Data model", "Architecture", "Deep dives")

SCOPE_NOTE = (
    "This is the Scope the Question sets for itself. It defines the Question and asserts nothing "
    "about the world, so it carries no Citation."
)


class AttemptBox(QWidget):
    """A typed attempt followed by a Reveal of whatever `build_reveal` returns."""

    def __init__(self, instruction: str, build_reveal: Callable[[], QWidget], heading: str = ""):
        super().__init__()
        self.build_reveal = build_reveal
        self.revealed: QWidget | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        if heading:
            layout.addWidget(label(heading, "h2"))
        layout.addWidget(label(instruction, "muted"))
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Write your answer before you reveal.")
        self.editor.setMinimumHeight(150)
        layout.addWidget(self.editor)
        row = QHBoxLayout()
        self.button = QPushButton("Reveal Reference answer")
        self.button.setObjectName("primary")
        self.button.clicked.connect(self.reveal)
        row.addWidget(self.button)
        row.addStretch(1)
        layout.addLayout(row)
        self.slot = QVBoxLayout()
        layout.addLayout(self.slot)

    def reveal(self) -> None:
        if self.revealed is None:
            self.revealed = self.build_reveal()
            self.slot.addWidget(self.revealed)
            self.button.setText("Hide Reference answer")
        else:
            visible = not self.revealed.isVisibleTo(self)
            self.revealed.setVisible(visible)
            self.button.setText("Hide Reference answer" if visible else "Reveal Reference answer")

    def has_work(self) -> bool:
        return bool(self.editor.toPlainText().strip())


def tick_list(layout: QVBoxLayout, heading: str, items) -> None:
    layout.addWidget(label(heading, "h3"))
    for item in items:
        box = QCheckBox(item)
        box.setToolTip("Tick if your answer covered this")
        layout.addWidget(box)


def requirements_panel(scope: Scope) -> QWidget:
    frame, layout = card()
    layout.addWidget(chip("Scope set by this Question"))
    layout.addWidget(label(SCOPE_NOTE, "muted"))
    tick_list(layout, "Functional", scope.functional)
    tick_list(layout, "Non-functional", scope.non_functional)
    return frame


def estimates_panel(scope: Scope) -> QWidget:
    frame, layout = card()
    layout.addWidget(chip("Scope set by this Question"))
    layout.addWidget(label(SCOPE_NOTE, "muted"))
    layout.addWidget(label("Assumptions", "h3"))
    for assumption in scope.assumptions:
        layout.addWidget(label(f"•  {assumption}"))
    layout.addWidget(label("Arithmetic from those assumptions", "h3"))
    grid = QGridLayout()
    grid.setHorizontalSpacing(18)
    grid.setVerticalSpacing(8)
    for row, estimate in enumerate(scope.estimates):
        grid.addWidget(label(estimate.label), row, 0, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(label(estimate.working, "muted"), row, 1, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(label(estimate.result), row, 2, Qt.AlignmentFlag.AlignTop)
    grid.setColumnStretch(0, 2)
    grid.setColumnStretch(1, 4)
    grid.setColumnStretch(2, 2)
    layout.addLayout(grid)
    return frame


class ArchitectureStage(QWidget):
    open_page = pyqtSignal(str)

    def __init__(self, question: Question, library: Library):
        super().__init__()
        self.question = question
        self.library = library
        self.revealed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        top = QHBoxLayout()
        self.instruction = label(
            "Build your Design: place Blocks, connect them, and set their properties.", "muted")
        top.addWidget(self.instruction, 1)
        self.button = QPushButton("Reveal Reference answer")
        self.button.setObjectName("primary")
        self.button.clicked.connect(self.reveal)
        top.addWidget(self.button)
        layout.addLayout(top)

        self.editor = CanvasEditor(library)
        self.editor.open_page.connect(self.open_page.emit)
        self.editor.design_changed.connect(self._refresh_checks)

        self.tabs = QTabWidget()
        self.checks_host = QWidget()
        self.checks_layout = QVBoxLayout(self.checks_host)
        self.checks_layout.setContentsMargins(0, 8, 8, 8)
        self.checks_layout.setSpacing(8)
        self.tabs.addTab(scrollable(self.checks_host), "Checks")
        self.tabs.addTab(self._reference_tab(), "Reference answer")
        self.tabs.hide()

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.tabs)
        self.splitter.setChildrenCollapsible(False)
        layout.addWidget(self.splitter, 1)

    def _reference_tab(self) -> QWidget:
        self.reference_scene = DesignScene(self.library, self.question.architecture.design, read_only=True)
        self.reference_scene.block_activated.connect(self.open_page.emit)
        self.reference_view = CanvasView(self.reference_scene)
        notes = AnswerPanel(self.question.architecture.answer, tickable=False, heading="Reference Design")
        tab = QSplitter(Qt.Orientation.Horizontal)
        tab.addWidget(self.reference_view)
        tab.addWidget(scrollable(notes))
        tab.setSizes([640, 460])
        return tab

    def reveal(self) -> None:
        self.revealed = True
        self.button.hide()
        self.instruction.setText(
            "Revealed. Keep editing your Design: the Checks below are re-run on every change.")
        self.tabs.show()
        self.splitter.setSizes([440, 440])
        self._refresh_checks()
        self.reference_view.fit()

    def _refresh_checks(self) -> None:
        if not self.revealed:
            return
        while self.checks_layout.count():
            item = self.checks_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        results = run_checks(self.question.architecture.checks, self.editor.design)
        held = sum(result.passed for result in results)
        self.tabs.setTabText(0, f"Checks: {held} of {len(results)} hold")
        for result in results:
            frame, box = card()
            header = QHBoxLayout()
            header.addWidget(chip("Holds", "chipGood") if result.passed else chip("Not found", "chipBad"))
            header.addWidget(label(result.check.title), 1)
            box.addLayout(header)
            if not result.passed:
                box.addWidget(label(result.check.miss, "muted"))
            box.addWidget(ClaimView(result.check.rationale))
            self.checks_layout.addWidget(frame)
        self.checks_layout.addStretch(1)

    def has_work(self) -> bool:
        return not self.editor.design.is_empty()


class SessionView(QWidget):
    """One Practice session: a Question worked through its Stages. Nothing here is stored."""

    closed = pyqtSignal()
    open_page = pyqtSignal(str)

    def __init__(self, question: Question, library: Library):
        super().__init__()
        self.question = question
        self.library = library
        self.attempts: list[AttemptBox] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(10)

        back = QPushButton("‹  Questions")
        back.setObjectName("link")
        back.clicked.connect(self.closed.emit)
        layout.addWidget(back, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(label(question.title, "h1"))
        layout.addLayout(self._tags())
        layout.addWidget(label(question.prompt, "prompt"))

        bar = QHBoxLayout()
        bar.setSpacing(0)
        self.stack = QStackedWidget()
        self.stage_buttons = QButtonGroup(self)
        for index, name in enumerate(STAGES):
            button = QPushButton(f"{index + 1}  {name}")
            button.setObjectName("stage")
            button.setCheckable(True)
            self.stage_buttons.addButton(button, index)
            bar.addWidget(button)
        bar.addStretch(1)
        layout.addLayout(bar)
        layout.addWidget(self.stack, 1)

        scope = question.scope
        self._typed_stage(
            "List the functional and non-functional requirements you would agree with the interviewer.",
            lambda: requirements_panel(scope))
        self._typed_stage(
            "Estimate the load and the storage. State the assumptions you are making.",
            lambda: estimates_panel(scope))
        self._typed_stage(
            "Define the interface: the operations, what each takes and returns, and how failures show.",
            lambda: AnswerPanel(question.api))
        self._typed_stage(
            "Define what is stored: the records, their keys, and how they are looked up.",
            lambda: AnswerPanel(question.data_model))
        self.architecture = ArchitectureStage(question, library)
        self.architecture.open_page.connect(self.open_page.emit)
        self.stack.addWidget(self.architecture)
        self.stack.addWidget(self._deep_dives())

        self.stage_buttons.idClicked.connect(self.stack.setCurrentIndex)
        self.stage_buttons.button(0).setChecked(True)

    def _tags(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(chip(self.question.category.capitalize()))
        for tag in self.question.company_tags:
            row.addWidget(chip(f"{tag.company}: reported, not verified", "chipWarn"))
            for number, url in enumerate(tag.reports, start=1):
                report = link_label(link_html(url).replace(f">{url}<", f">candidate report {number}<"))
                report.setToolTip(url)
                report.setWordWrap(False)
                row.addWidget(report)
        row.addStretch(1)
        return row

    def _typed_stage(self, instruction: str, build_reveal: Callable[[], QWidget]) -> None:
        box = AttemptBox(instruction, build_reveal)
        self.attempts.append(box)
        self.stack.addWidget(self._page(box))

    def _deep_dives(self) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 8, 12, 8)
        layout.setSpacing(26)
        for dive in self.question.deep_dives:
            box = AttemptBox("Answer in your own words, then reveal.",
                             lambda dive=dive: self._dive_reveal(dive), heading=dive.prompt)
            self.attempts.append(box)
            layout.addWidget(box)
        layout.addStretch(1)
        return scrollable(host)

    def _dive_reveal(self, dive) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(AnswerPanel(dive.answer))
        if dive.pages:
            row = QHBoxLayout()
            row.addWidget(label("Read more:", "muted", wrap=False))
            for page_id in dive.pages:
                page = self.library.page(page_id)
                button = QPushButton(page.name)
                button.setObjectName("link")
                button.clicked.connect(lambda _=False, page_id=page_id: self.open_page.emit(page_id))
                row.addWidget(button)
            row.addStretch(1)
            layout.addLayout(row)
        return host

    @staticmethod
    def _page(inner: QWidget) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 8, 12, 8)
        layout.addWidget(inner)
        layout.addStretch(1)
        return scrollable(host)

    def go_to_stage(self, index: int) -> None:
        self.stage_buttons.button(index).setChecked(True)
        self.stack.setCurrentIndex(index)

    def has_work(self) -> bool:
        return self.architecture.has_work() or any(box.has_work() for box in self.attempts)
