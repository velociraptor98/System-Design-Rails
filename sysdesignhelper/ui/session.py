from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWIDGETSIZE_MAX, QGridLayout, QHBoxLayout, QSplitter, QStackedWidget, QVBoxLayout, QWidget,
)

from ..checks import run_checks
from ..content import Library, Question, Scope
from . import theme
from .canvas import CanvasEditor, CanvasView, DesignScene
from .widgets import (
    ClaimView, EditorCard, SegmentedControl, Tabs, Toolbar, answer_panel, button, card, chip, clear_layout,
    eyebrow, label, link_html, rule, scrollable, tick_row,
)

STAGES = ("Requirements", "Estimates", "API", "Data model", "Architecture", "Deep dives")
ARCHITECTURE = STAGES.index("Architecture")

SCOPE_NOTE = (
    "This is the Scope the Question sets for itself. It defines the Question and asserts nothing "
    "about the world, so it carries no Citation."
)


class AttemptBox(QWidget):
    """A typed attempt followed by a Reveal of whatever `build_reveal` returns.

    The full-height form puts the answer beside the editor and is revealed from the toolbar;
    the inline form stacks them and carries its own button.
    """

    def __init__(self, instruction: str, build_reveal: Callable[[], QWidget], heading: str = "",
                 inline: bool = False):
        super().__init__()
        self.build_reveal = build_reveal
        self.inline = inline
        self.revealed: QWidget | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        if heading:
            layout.addWidget(label(heading, "h2"))
        layout.addWidget(label(instruction, "muted"))
        editor_card = EditorCard("Write your answer before you reveal.")
        self.editor = editor_card.editor
        self.button = None
        if inline:
            editor_card.setFixedHeight(132)
            layout.addWidget(editor_card)
            row = QHBoxLayout()
            self.button = button("Reveal Answer", icon_name="reveal")
            self.button.clicked.connect(self.reveal)
            row.addWidget(self.button)
            row.addStretch(1)
            layout.addLayout(row)
            self.slot = QVBoxLayout()
            layout.addLayout(self.slot)
        else:
            self.slot = QHBoxLayout()
            self.slot.setSpacing(14)
            self.slot.addWidget(editor_card, 5)
            layout.addLayout(self.slot, 1)

    def is_revealed(self) -> bool:
        return self.revealed is not None and not self.revealed.isHidden()

    def reveal(self) -> None:
        if self.revealed is None:
            answer = self.build_reveal()
            if self.inline:
                self.revealed = answer
                self.slot.addWidget(answer)
            else:
                host = QWidget()
                column = QVBoxLayout(host)
                column.setContentsMargins(0, 0, 10, 0)
                column.addWidget(answer)
                column.addStretch(1)
                self.revealed = scrollable(host)
                self.slot.addWidget(self.revealed, 6)
            # A widget added to a visible parent is only shown on the next event-loop pass.
            self.revealed.show()
        else:
            self.revealed.setVisible(self.revealed.isHidden())
        if self.button is not None:
            self.button.setText("Hide Answer" if self.is_revealed() else "Reveal Answer")

    def has_work(self) -> bool:
        return bool(self.editor.toPlainText().strip())


def tick_list(layout: QVBoxLayout, heading: str, items) -> None:
    layout.addWidget(eyebrow(heading))
    for item in items:
        layout.addWidget(tick_row(item))


def requirements_panel(scope: Scope) -> QWidget:
    frame, layout = card()
    layout.addWidget(label("Scope set by this Question", "h2"))
    layout.addWidget(label(SCOPE_NOTE, "muted"))
    tick_list(layout, "Functional", scope.functional)
    tick_list(layout, "Non-functional", scope.non_functional)
    return frame


def estimates_panel(scope: Scope) -> QWidget:
    frame, layout = card()
    layout.addWidget(label("Scope set by this Question", "h2"))
    layout.addWidget(label(SCOPE_NOTE, "muted"))
    layout.addWidget(eyebrow("Assumptions"))
    for assumption in scope.assumptions:
        layout.addWidget(label(f"•  {assumption}", "body"))
    layout.addWidget(eyebrow("Arithmetic from those assumptions"))
    grid = QGridLayout()
    grid.setHorizontalSpacing(18)
    grid.setVerticalSpacing(10)
    for row, estimate in enumerate(scope.estimates):
        grid.addWidget(label(estimate.label, "body"), row, 0, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(label(estimate.working, "muted"), row, 1, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(label(estimate.result, "body"), row, 2, Qt.AlignmentFlag.AlignTop)
    grid.setColumnStretch(0, 3)
    grid.setColumnStretch(1, 4)
    grid.setColumnStretch(2, 3)
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
        layout.setSpacing(14)
        self.instruction = label("Build your design: place blocks, connect them, and set their properties.", "muted")
        self.instruction.setContentsMargins(4, 0, 4, 0)
        layout.addWidget(self.instruction)

        self.editor = CanvasEditor(library)
        self.editor.open_page.connect(self.open_page.emit)
        self.editor.design_changed.connect(self._refresh_checks)

        self.checks_host = QWidget()
        self.checks_layout = QVBoxLayout(self.checks_host)
        self.checks_layout.setContentsMargins(0, 0, 10, 0)
        self.checks_layout.setSpacing(10)
        self.tabs = Tabs([
            ("Checks", scrollable(self.checks_host)),
            ("Reference answer", self._reference_tab()),
        ])
        self.tabs.hide()

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.tabs)
        self.splitter.setChildrenCollapsible(False)
        layout.addWidget(self.splitter, 1)

    def _reference_tab(self) -> QWidget:
        scene = DesignScene(self.library, self.question.architecture.design, read_only=True)
        scene.block_activated.connect(self.open_page.emit)
        self.reference_view = CanvasView(scene)
        host = QWidget()
        column = QVBoxLayout(host)
        column.setContentsMargins(0, 0, 10, 0)
        column.addWidget(answer_panel(self.question.architecture.answer, tickable=False, heading="Reference design"))
        column.addStretch(1)
        tab = QSplitter(Qt.Orientation.Horizontal)
        tab.addWidget(self.reference_view)
        tab.addWidget(scrollable(host))
        tab.setSizes([620, 420])
        return tab

    def is_revealed(self) -> bool:
        return self.revealed and not self.tabs.isHidden()

    def reveal(self) -> None:
        if self.revealed:
            self.tabs.setVisible(self.tabs.isHidden())
            return
        self.revealed = True
        self.instruction.setText("Revealed. Keep editing your design: the Checks are re-run on every change.")
        self.tabs.show()
        self.splitter.setSizes([330, 420])
        self._refresh_checks()
        self.reference_view.fit()

    def _refresh_checks(self) -> None:
        if not self.revealed:
            return
        clear_layout(self.checks_layout)
        results = run_checks(self.question.architecture.checks, self.editor.design)
        held = sum(result.passed for result in results)
        self.tabs.setTabText(0, f"Checks: {held} of {len(results)} hold")
        for result in results:
            frame, box = card()
            header = QHBoxLayout()
            header.setSpacing(10)
            header.addWidget(chip("Holds", "chipGood") if result.passed else chip("Not found", "chipBad"))
            header.addWidget(label(result.check.title, "h2"), 1)
            box.addLayout(header)
            if not result.passed:
                box.addWidget(label(result.check.miss, "muted"))
            box.addWidget(rule())
            box.addWidget(ClaimView(result.check.rationale))
            self.checks_layout.addWidget(frame)
        self.checks_layout.addStretch(1)

    def has_work(self) -> bool:
        return not self.editor.design.is_empty()


class SessionView(QWidget):
    closed = pyqtSignal()
    open_page = pyqtSignal(str)

    def __init__(self, question: Question, library: Library):
        super().__init__()
        self.question = question
        self.library = library
        self.attempts: list[AttemptBox] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.toolbar = Toolbar(question.title, self._subtitle(), with_back=True)
        self.toolbar.back.connect(self.closed.emit)
        self.cta = button("Reveal Answer", "cta", icon_name="reveal", icon_color="#ffffff")
        self.cta.clicked.connect(self.toggle_reveal)
        self.toolbar.add_action(self.cta)
        outer.addWidget(self.toolbar)

        self.body = QVBoxLayout()
        self.body.setSpacing(18)
        outer.addLayout(self.body, 1)
        self.prompt = label(question.prompt, "prompt")
        self.prompt.setMaximumWidth(760)
        self.body.addWidget(self.prompt)
        self.stages = SegmentedControl(STAGES)
        self.body.addWidget(self.stages)
        self.stack = QStackedWidget()
        self.body.addWidget(self.stack, 1)

        scope = question.scope
        self._typed_stage(
            "List the functional and non-functional requirements you would agree with the interviewer.",
            lambda: requirements_panel(scope))
        self._typed_stage(
            "Estimate the load and the storage. State the assumptions you are making.",
            lambda: estimates_panel(scope))
        self._typed_stage(
            "Define the interface: the operations, what each takes and returns, and how failures show.",
            lambda: answer_panel(question.api))
        self._typed_stage(
            "Define what is stored: the records, their keys, and how they are looked up.",
            lambda: answer_panel(question.data_model))
        self.architecture = ArchitectureStage(question, library)
        self.architecture.open_page.connect(self.open_page.emit)
        self.stack.addWidget(self.architecture)
        self.stack.addWidget(self._deep_dives())

        self.stages.selected.connect(self.go_to_stage)
        self.go_to_stage(0)

    def _subtitle(self) -> str:
        parts = [self.question.category.capitalize()]
        for tag in self.question.company_tags:
            links = ", ".join(
                link_html(url, f"report {number}") for number, url in enumerate(tag.reports, start=1))
            parts.append(f'<span style="color:{theme.WARN}">Reported at {tag.company}, not verified</span> ({links})')
        return "  ·  ".join(parts)

    def _typed_stage(self, instruction: str, build_reveal: Callable[[], QWidget]) -> None:
        box = AttemptBox(instruction, build_reveal)
        self.attempts.append(box)
        self.stack.addWidget(box)

    def _deep_dives(self) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(30)
        for dive in self.question.deep_dives:
            box = AttemptBox("Answer in your own words, then reveal.",
                             lambda dive=dive: self._dive_reveal(dive), heading=dive.prompt, inline=True)
            self.attempts.append(box)
            layout.addWidget(box)
        layout.addStretch(1)
        return scrollable(host)

    def _dive_reveal(self, dive) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(answer_panel(dive.answer))
        if dive.pages:
            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(label("Read more", "muted", wrap=False))
            for page_id in dive.pages:
                page = self.library.page(page_id)
                link = button(page.name, "chipLink")
                link.clicked.connect(lambda _=False, page_id=page_id: self.open_page.emit(page_id))
                row.addWidget(link)
            row.addStretch(1)
            layout.addLayout(row)
        return host

    def _current_revealable(self):
        index = self.stack.currentIndex()
        if index == ARCHITECTURE:
            return self.architecture
        if index < ARCHITECTURE:
            return self.attempts[index]
        return None

    def _sync_toolbar(self) -> None:
        target = self._current_revealable()
        self.cta.setVisible(target is not None)
        if target is not None:
            self.cta.setText("Hide Answer" if target.is_revealed() else "Reveal Answer")

    def toggle_reveal(self) -> None:
        target = self._current_revealable()
        if target is not None:
            target.reveal()
            self._sync_toolbar()

    def go_to_stage(self, index: int) -> None:
        self.stages.set_current(index)
        self.stack.setCurrentIndex(index)
        wide = index == ARCHITECTURE
        margin = 20 if wide else 32
        self.body.setContentsMargins(margin, 4, margin, margin)
        self.prompt.setVisible(not wide)
        self.stages.setMaximumWidth(QWIDGETSIZE_MAX if wide else 820)
        self._sync_toolbar()

    def has_work(self) -> bool:
        return self.architecture.has_work() or any(box.has_work() for box in self.attempts)
