from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QMessageBox, QStackedWidget, QVBoxLayout, QWidget,
)

from ..content import CATEGORIES, Library, Question
from .session import SessionView
from .widgets import chip, label, scrollable


def confirm_discard(parent: QWidget) -> bool:
    answer = QMessageBox.question(
        parent, "Discard this Practice session?",
        "Nothing is saved. Your typed answers and your Design will be lost.",
        QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
        QMessageBox.StandardButton.Cancel,
    )
    return answer == QMessageBox.StandardButton.Discard


class QuestionCard(QFrame):
    chosen = pyqtSignal(str)

    def __init__(self, question: Question):
        super().__init__()
        self.question = question
        self.setObjectName("questionCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        title = label(question.title, "h2")
        title.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(title)
        prompt = label(question.prompt, "muted")
        prompt.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(prompt)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(chip(question.category.capitalize()))
        for tag in question.company_tags:
            row.addWidget(chip(f"{tag.company}: reported", "chipWarn"))
        if not question.company_tags:
            row.addWidget(chip("No company report found"))
        row.addStretch(1)
        layout.addLayout(row)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.chosen.emit(self.question.id)


class QuestionsView(QWidget):
    open_page = pyqtSignal(str)

    def __init__(self, library: Library):
        super().__init__()
        self.library = library
        self.session: SessionView | None = None
        self.confirm = confirm_discard

        self.stack = QStackedWidget()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.stack)

        self.list_page = QWidget()
        layout = QVBoxLayout(self.list_page)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)
        layout.addWidget(label("Questions", "h1"))
        layout.addWidget(label(
            "Pick a Question and work through its six Stages. Company tags come from LeetCode candidate "
            "reports and are not verified.", "muted"))

        filters = QHBoxLayout()
        self.category = QComboBox()
        self.category.addItem("All categories", "")
        for category in CATEGORIES:
            self.category.addItem(category.capitalize(), category)
        self.company = QComboBox()
        self.company.addItem("All companies", "")
        for company in library.companies():
            self.company.addItem(company, company)
        filters.addWidget(self.category)
        filters.addWidget(self.company)
        filters.addStretch(1)
        layout.addLayout(filters)

        self.cards_host = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setContentsMargins(0, 0, 12, 0)
        self.cards_layout.setSpacing(12)
        layout.addWidget(scrollable(self.cards_host), 1)
        self.stack.addWidget(self.list_page)

        self.category.currentIndexChanged.connect(self._refresh)
        self.company.currentIndexChanged.connect(self._refresh)
        self._refresh()

    def visible_questions(self) -> list[Question]:
        category, company = self.category.currentData(), self.company.currentData()
        return [
            question for question in self.library.questions.values()
            if (not category or question.category == category)
            and (not company or any(tag.company == company for tag in question.company_tags))
        ]

    def _refresh(self) -> None:
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        questions = self.visible_questions()
        for question in questions:
            question_card = QuestionCard(question)
            question_card.chosen.connect(self.start_session)
            self.cards_layout.addWidget(question_card)
        if not questions:
            self.cards_layout.addWidget(label("No Question matches these filters.", "muted"))
        self.cards_layout.addStretch(1)

    def start_session(self, question_id: str) -> None:
        self._drop_session()
        self.session = SessionView(self.library.questions[question_id], self.library)
        self.session.closed.connect(self.close_session)
        self.session.open_page.connect(self.open_page.emit)
        self.stack.addWidget(self.session)
        self.stack.setCurrentWidget(self.session)

    def close_session(self) -> None:
        if self.session is None:
            return
        if self.session.has_work() and not self.confirm(self):
            return
        self._drop_session()

    def _drop_session(self) -> None:
        if self.session is not None:
            self.stack.removeWidget(self.session)
            self.session.deleteLater()
            self.session = None
        self.stack.setCurrentWidget(self.list_page)

    def has_work(self) -> bool:
        return self.session is not None and self.session.has_work()
