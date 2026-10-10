from __future__ import annotations

from html import escape
from urllib.parse import urlsplit

from PyQt6.QtCore import QEvent, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import (
    QButtonGroup, QCheckBox, QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from ..content import REAL_SYSTEM, Claim, StageAnswer
from . import icons, theme


def label(text: str, name: str = "", wrap: bool = True) -> QLabel:
    widget = QLabel(text)
    widget.setWordWrap(wrap)
    widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    if name:
        widget.setObjectName(name)
    return widget


def eyebrow(text: str) -> QLabel:
    widget = QLabel(text.upper())
    widget.setObjectName("h3")
    font = widget.font()
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.3)
    widget.setFont(font)
    return widget


def chip(text: str, name: str = "chip") -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    return widget


def rule() -> QFrame:
    line = QFrame()
    line.setObjectName("rule")
    return line


def button(text: str, name: str = "pill", icon_name: str = "", icon_color: str = theme.TEXT) -> QPushButton:
    widget = QPushButton(f" {text}" if icon_name else text)
    widget.setObjectName(name)
    if icon_name:
        widget.setIcon(icons.icon(icon_name, icon_color, 15))
        widget.setIconSize(QSize(15, 15))
    return widget


def source_text(url: str) -> str:
    parts = urlsplit(url)
    host = parts.netloc.removeprefix("www.")
    tail = parts.path.rstrip("/").rsplit("/", 1)[-1]
    return f"{host} — {tail}" if tail else host


def link_html(url: str, text: str | None = None) -> str:
    shown = escape(text if text is not None else url)
    return f'<a style="color:{theme.LINK}; text-decoration:none" href="{escape(url, quote=True)}">{shown}</a>'


def link_label(html: str, name: str = "citation") -> QLabel:
    widget = QLabel(html)
    widget.setObjectName(name)
    widget.setTextFormat(Qt.TextFormat.RichText)
    widget.setOpenExternalLinks(True)
    widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
    return widget


def scrollable(inner: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setWidget(inner)
    return area


def card(name: str = "card") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName(name)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 16, 20, 18)
    layout.setSpacing(10)
    return frame, layout


def clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget() is not None:
            discard(item.widget())
        elif item.layout() is not None:
            clear_layout(item.layout())


def discard(widget: QWidget) -> None:
    # Hidden first: backgrounds are transparent, so a widget awaiting deletion would show through.
    widget.hide()
    widget.deleteLater()


class Toolbar(QWidget):
    """The strip at the top of each area: optional back button, title, then actions on the right."""

    back = pyqtSignal()

    def __init__(self, title: str, subtitle: str = "", with_back: bool = False):
        super().__init__()
        self.setFixedHeight(60)
        row = QHBoxLayout(self)
        row.setContentsMargins(18 if with_back else 24, 8, 20, 10)
        row.setSpacing(12)
        if with_back:
            back = QPushButton()
            back.setObjectName("roundButton")
            back.setIcon(icons.icon("back", theme.TEXT, 14))
            back.setIconSize(QSize(14, 14))
            back.setToolTip("Back")
            back.clicked.connect(self.back.emit)
            row.addWidget(back)
        column = QVBoxLayout()
        column.setSpacing(1)
        self.title = QLabel(title)
        self.title.setObjectName("toolbarTitle")
        column.addStretch(1)
        column.addWidget(self.title)
        self.subtitle = link_label(subtitle, "toolbarSubtitle")
        self.subtitle.setVisible(bool(subtitle))
        column.addWidget(self.subtitle)
        column.addStretch(1)
        row.addLayout(column)
        row.addStretch(1)
        self.actions = QHBoxLayout()
        self.actions.setSpacing(10)
        row.addLayout(self.actions)

    def set_subtitle(self, html: str) -> None:
        self.subtitle.setText(html)
        self.subtitle.setVisible(bool(html))

    def add_action(self, widget: QWidget) -> None:
        self.actions.addWidget(widget)


class SegmentButton(QPushButton):
    def __init__(self, number: str, text: str):
        super().__init__()
        self.number = number
        self.caption = text
        self.setCheckable(True)
        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAccessibleName(text)

    def text(self) -> str:
        return self.caption

    def sizeHint(self) -> QSize:
        return QSize(self.fontMetrics().horizontalAdvance(self.number + self.caption) + 40, 30)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(theme.SEG_SELECTED))
            painter.drawRoundedRect(QRectF(self.rect()), 15, 15)
        number_font = QFont(self.font())
        number_font.setPixelSize(11)
        number_font.setWeight(QFont.Weight.DemiBold)
        text_font = QFont(self.font())
        text_font.setPixelSize(13)
        text_font.setWeight(QFont.Weight.Medium)
        painter.setFont(number_font)
        number_width = painter.fontMetrics().horizontalAdvance(self.number) if self.number else 0
        painter.setFont(text_font)
        text_width = painter.fontMetrics().horizontalAdvance(self.caption)
        gap = 7 if self.number else 0
        x = (self.width() - number_width - gap - text_width) / 2
        active = self.isChecked() or self.underMouse()
        if self.number:
            painter.setFont(number_font)
            painter.setPen(QColor(theme.LINK if self.isChecked() else theme.TEXT3))
            painter.drawText(QRectF(x, 0, number_width, self.height()), Qt.AlignmentFlag.AlignVCenter, self.number)
        painter.setFont(text_font)
        painter.setPen(QColor(theme.TEXT if active else theme.TEXT2))
        painter.drawText(QRectF(x + number_width + gap, 0, text_width + 2, self.height()),
                         Qt.AlignmentFlag.AlignVCenter, self.caption)

    def enterEvent(self, event) -> None:
        self.update()

    def leaveEvent(self, event) -> None:
        self.update()


class SegmentedControl(QFrame):
    selected = pyqtSignal(int)

    def __init__(self, names, numbered: bool = True):
        super().__init__()
        self.setObjectName("segmented")
        self.setFixedHeight(36)
        row = QHBoxLayout(self)
        row.setContentsMargins(3, 3, 3, 3)
        row.setSpacing(2)
        self.group = QButtonGroup(self)
        for index, name in enumerate(names):
            segment = SegmentButton(str(index + 1) if numbered else "", name)
            self.group.addButton(segment, index)
            row.addWidget(segment)
        self.group.idClicked.connect(self.selected.emit)
        self.set_current(0)

    def buttons(self) -> list[SegmentButton]:
        return self.group.buttons()

    def set_current(self, index: int) -> None:
        self.group.button(index).setChecked(True)

    def set_text(self, index: int, text: str) -> None:
        segment = self.group.button(index)
        segment.caption = text
        segment.update()


class Tabs(QWidget):
    """A segmented control switching between a few panels."""

    def __init__(self, tabs):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.control = SegmentedControl([text for text, _ in tabs], numbered=False)
        self.control.setMaximumWidth(210 * len(tabs))
        self.stack = QStackedWidget()
        for _, panel in tabs:
            self.stack.addWidget(panel)
        layout.addWidget(self.control)
        layout.addWidget(self.stack, 1)
        self.control.selected.connect(self.stack.setCurrentIndex)

    def tabText(self, index: int) -> str:
        return self.control.buttons()[index].caption

    def setTabText(self, index: int, text: str) -> None:
        self.control.set_text(index, text)

    def setCurrentIndex(self, index: int) -> None:
        self.control.set_current(index)
        self.stack.setCurrentIndex(index)


def tick_row(text: str) -> QWidget:
    """A tick box with a label that wraps, which QCheckBox's own text cannot do."""
    host = QWidget()
    row = QHBoxLayout(host)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(10)
    box = QCheckBox()
    box.setToolTip("Tick if your answer covered this")
    row.addWidget(box, 0, Qt.AlignmentFlag.AlignTop)
    row.addWidget(label(text, "body"), 1)
    return host


class Stepper(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, value: int, minimum: int = 1, maximum: int = 100000):
        super().__init__()
        self._value, self.minimum, self.maximum = value, minimum, maximum
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addStretch(1)
        self.display = QLabel(str(value))
        self.display.setMinimumWidth(18)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self.display)
        frame = QFrame()
        frame.setObjectName("stepper")
        inner = QHBoxLayout(frame)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)
        for text, delta, tip in (("−", -1, "Decrease"), ("+", 1, "Increase")):
            step = QPushButton(text)
            step.setObjectName("stepButton")
            step.setToolTip(tip)
            step.setAutoRepeat(True)
            step.clicked.connect(lambda _=False, delta=delta: self.setValue(self._value + delta))
            inner.addWidget(step)
        row.addWidget(frame)

    def value(self) -> int:
        return self._value

    def setValue(self, value: int) -> None:
        value = max(self.minimum, min(self.maximum, value))
        if value != self._value:
            self._value = value
            self.display.setText(str(value))
            self.valueChanged.emit(value)


class EditorCard(QFrame):
    """A text area inside a rounded card whose border lights up while it has focus."""

    def __init__(self, placeholder: str):
        super().__init__()
        self.setObjectName("editorCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 6, 12)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(placeholder)
        self.editor.installEventFilter(self)
        layout.addWidget(self.editor)

    def eventFilter(self, watched, event) -> bool:
        if event.type() in (QEvent.Type.FocusIn, QEvent.Type.FocusOut):
            self.setProperty("focused", event.type() == QEvent.Type.FocusIn)
            self.style().unpolish(self)
            self.style().polish(self)
        return False


class ClaimView(QWidget):
    """One claim with its Citations, optionally preceded by a tick box."""

    def __init__(self, claim: Claim, tickable: bool = False):
        super().__init__()
        self.claim = claim
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        self.tick: QCheckBox | None = None
        if tickable:
            self.tick = QCheckBox()
            self.tick.setToolTip("Tick if your answer covered this")
            row.addWidget(self.tick, 0, Qt.AlignmentFlag.AlignTop)
        column = QVBoxLayout()
        column.setSpacing(5)
        column.addWidget(label(claim.text, "synthesisText" if claim.synthesis else "body"))
        if claim.synthesis:
            column.addWidget(label("Synthesis: no source stands behind this sentence.", "synthesisNote"))
        for citation in claim.citations:
            source = QHBoxLayout()
            source.setSpacing(5)
            mark = QLabel()
            mark.setPixmap(icons.pixmap("external", theme.LINK, 11))
            source.addWidget(mark)
            html = link_html(citation.url, source_text(citation.url))
            if not citation.retrieved:
                html += f' &nbsp;<span style="color:{theme.DANGER}">not retrieved</span>'
            link = link_label(html)
            link.setToolTip(citation.url)
            source.addWidget(link)
            source.addStretch(1)
            column.addLayout(source)
        row.addLayout(column, 1)


def add_claims(layout: QVBoxLayout, claims, tickable: bool = False) -> list[ClaimView]:
    views = []
    for index, claim in enumerate(claims):
        if index:
            layout.addWidget(rule())
        view = ClaimView(claim, tickable=tickable)
        views.append(view)
        layout.addWidget(view)
    return views


class AnswerPanel(QFrame):
    """A Reference answer for one Stage: its kind, then its Key points."""

    def __init__(self, answer: StageAnswer, tickable: bool = True, heading: str = "Key points"):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 18)
        layout.setSpacing(10)
        layout.addWidget(label(heading, "h2"))
        if answer.kind == REAL_SYSTEM:
            layout.addWidget(label(
                f"Real-system answer: {answer.system}. Every sentence reports what its source published.",
                "realSystem",
            ))
        else:
            layout.addWidget(label(
                "Synthesized answer. No published real system fits this Stage, so this answer was composed "
                "for the Question. Sentences with a link are backed by that source. Sentences in italics are "
                "judgement with no source behind them; treat them as one reasonable answer, not the answer.",
                "disclaimer",
            ))
        self.claims = add_claims(layout, answer.key_points, tickable=tickable)
