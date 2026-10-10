from __future__ import annotations

from html import escape

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ..content import REAL_SYSTEM, Claim, StageAnswer
from . import theme


def label(text: str, name: str = "", wrap: bool = True) -> QLabel:
    widget = QLabel(text)
    widget.setWordWrap(wrap)
    widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    if name:
        widget.setObjectName(name)
    return widget


def chip(text: str, name: str = "chip") -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    return widget


def link_html(url: str) -> str:
    return f'<a style="color:{theme.ACCENT}; text-decoration:none" href="{escape(url, quote=True)}">{escape(url)}</a>'


def link_label(html: str, name: str = "citation") -> QLabel:
    widget = QLabel(html)
    widget.setObjectName(name)
    widget.setWordWrap(True)
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


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)
    return frame, layout


class ClaimView(QWidget):
    """One claim with its Citations, optionally preceded by a tick box."""

    def __init__(self, claim: Claim, tickable: bool = False):
        super().__init__()
        self.claim = claim
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setStyleSheet("background: transparent;")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self.tick: QCheckBox | None = None
        if tickable:
            self.tick = QCheckBox()
            self.tick.setToolTip("Tick if your answer covered this")
            row.addWidget(self.tick, 0, Qt.AlignmentFlag.AlignTop)
        column = QVBoxLayout()
        column.setSpacing(2)
        column.addWidget(label(claim.text, "synthesisText" if claim.synthesis else ""))
        if claim.synthesis:
            column.addWidget(label("Synthesis: no source stands behind this sentence.", "citation"))
        for citation in claim.citations:
            html = link_html(citation.url)
            if not citation.retrieved:
                html += f' &nbsp;<span style="color:{theme.BAD}">not retrieved</span>'
            column.addWidget(link_label(html))
        row.addLayout(column, 1)


class AnswerPanel(QFrame):
    """A Reference answer for one Stage: its kind, then its Key points."""

    def __init__(self, answer: StageAnswer, tickable: bool = True, heading: str = "Key points"):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        layout.addWidget(label(heading, "h3"))
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
        self.claims: list[ClaimView] = []
        for claim in answer.key_points:
            view = ClaimView(claim, tickable=tickable)
            self.claims.append(view)
            layout.addWidget(view)
