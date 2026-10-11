"""Translucent design tokens are pre-blended over the window colour where Qt
needs a solid colour to paint with."""

from pathlib import Path

_CHEVRONS = (Path(__file__).parent / "chevrons.svg").as_posix()

WIN = "#1c1c1e"
SIDE = "#2b2b2f"
CARD = "#252528"
CANVAS = "#18181a"
NODE = "#2e2e33"
DOT = "#38383a"
GLASS = "#333336"
SEG_SELECTED = "#4a4a50"
TEXT = "#f5f5f7"
TEXT2 = "#a5a5ab"
TEXT3 = "#88888e"
ACCENT = "#0a6cd9"
LINK = "#6cb4ff"
DANGER = "#ff8a80"
GOOD = "#63d68a"
WARN = "#f0c36a"

LINE = "rgba(255, 255, 255, 9%)"
FIELD = "rgba(255, 255, 255, 6%)"
HOVER = "rgba(255, 255, 255, 6%)"
SEG = "rgba(255, 255, 255, 7%)"
SELECTED = "rgba(255, 255, 255, 11%)"

STYLESHEET = f"""
* {{ font-size: 13px; }}
QWidget {{ background: transparent; color: {TEXT}; }}
QMainWindow, #root {{ background: {WIN}; }}
QToolTip {{ background: {GLASS}; color: {TEXT}; border: 1px solid {DOT}; padding: 4px 6px; }}

#sidebar {{ background: {SIDE}; border: 1px solid {LINE}; border-radius: 18px; }}
#navButton {{
    border: none; border-radius: 10px; padding: 0 10px; min-height: 34px; max-height: 34px;
    text-align: left; font-size: 13.5px; font-weight: 500; color: {TEXT};
}}
#navButton:hover {{ background: {HOVER}; }}
#navButton:checked {{ background: {SELECTED}; }}
#stat {{ font-size: 11.5px; color: {TEXT3}; }}
#statValue {{ font-size: 11.5px; color: {TEXT2}; }}

#toolbarTitle {{ font-size: 15px; font-weight: 600; }}
#toolbarSubtitle {{ font-size: 11.5px; color: {TEXT2}; }}
#h1 {{ font-size: 28px; font-weight: 700; }}
#h2 {{ font-size: 15px; font-weight: 600; }}
#h3 {{ font-size: 11px; font-weight: 600; color: {TEXT3}; }}
#muted {{ color: {TEXT2}; }}
#hint {{ font-size: 11.5px; color: {TEXT3}; }}
#prompt {{ font-size: 15px; }}
#body {{ font-size: 13.5px; }}

#roundButton {{
    background: {GLASS}; border: 1px solid {LINE}; border-radius: 17px;
    min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px;
}}
#roundButton:hover {{ background: {SEG_SELECTED}; }}
QPushButton#cta {{
    background: {ACCENT}; color: #ffffff; border: none; border-radius: 17px;
    min-height: 34px; max-height: 34px; padding: 0 16px 0 13px; font-weight: 600;
}}
QPushButton#cta:hover {{ background: #1f7be3; }}
QPushButton#cta:disabled {{ background: {SEG}; color: {TEXT3}; border: 1px solid {LINE}; }}
QPushButton#pill, QPushButton#pillDanger {{
    background: {SEG}; border: 1px solid {LINE}; border-radius: 15px;
    min-height: 28px; max-height: 28px; padding: 0 14px; font-weight: 500;
}}
QPushButton#pill:hover, QPushButton#pillDanger:hover {{ background: {SELECTED}; }}
QPushButton#pill:disabled {{ color: {TEXT3}; }}
QPushButton#pillDanger {{ color: {DANGER}; }}
QPushButton#chipLink {{
    background: {SEG}; border: 1px solid {LINE}; border-radius: 12px; color: {LINK};
    min-height: 22px; max-height: 22px; padding: 0 10px; font-size: 12px; font-weight: 500;
}}
QPushButton#chipLink:hover {{ background: {SELECTED}; }}

#segmented {{ background: {SEG}; border-radius: 18px; }}
#stepper {{ background: {SEG}; border: 1px solid {LINE}; border-radius: 7px; }}
QPushButton#stepButton {{ border: none; font-size: 15px; min-width: 28px; max-width: 28px; min-height: 26px; max-height: 26px; }}
QPushButton#stepButton:hover {{ background: {HOVER}; }}

#card, #questionCard {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 16px; }}
#questionCard:hover {{ border-color: {LINK}; }}
#editorCard {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 14px; }}
#editorCard[focused="true"] {{ border-color: {LINK}; }}
#rule {{ background: {LINE}; max-height: 1px; min-height: 1px; }}

QLabel#chip {{
    background: {SEG}; border: 1px solid {LINE}; border-radius: 10px; color: {TEXT2};
    min-height: 16px; padding: 2px 10px; font-size: 12px; font-weight: 500;
}}
QLabel#chipGood, QLabel#chipWarn, QLabel#chipBad {{
    border-radius: 10px; min-height: 16px; padding: 3px 10px; font-size: 12px; font-weight: 500;
}}
QLabel#chipGood {{ background: rgba(99, 214, 138, 14%); color: {GOOD}; }}
QLabel#chipWarn {{ background: rgba(240, 195, 106, 14%); color: {WARN}; }}
QLabel#chipBad {{ background: rgba(255, 138, 128, 14%); color: {DANGER}; }}
QLabel#disclaimer {{ background: rgba(240, 195, 106, 12%); color: {WARN}; border-radius: 10px; padding: 9px 12px; }}
QLabel#realSystem {{ background: rgba(99, 214, 138, 12%); color: {GOOD}; border-radius: 10px; padding: 9px 12px; }}
QLabel#citation {{ color: {LINK}; font-size: 11.5px; }}
QLabel#synthesisText {{ color: {WARN}; font-style: italic; font-size: 13.5px; }}
QLabel#synthesisNote {{ color: {TEXT3}; font-size: 11.5px; }}
QLabel#fieldLabel {{ color: {TEXT2}; }}

QPlainTextEdit {{ border: none; font-size: 14px; selection-background-color: {ACCENT}; selection-color: #ffffff; }}
QLineEdit, QComboBox {{
    background: {FIELD}; border: 1px solid {LINE}; border-radius: 7px; padding: 0 9px;
    min-height: 26px; max-height: 26px; selection-background-color: {ACCENT}; selection-color: #ffffff;
}}
QLineEdit:focus, QComboBox:focus {{ border-color: {LINK}; }}
QLineEdit:disabled {{ color: {TEXT3}; }}
QLineEdit#search {{ border-radius: 15px; min-height: 28px; max-height: 28px; padding-left: 4px; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{ image: url({_CHEVRONS}); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{
    background: {GLASS}; border: 1px solid {DOT}; border-radius: 6px; padding: 4px;
    selection-background-color: {ACCENT}; selection-color: #ffffff; outline: none;
}}

QListWidget {{ border: none; outline: none; padding: 0 6px 8px 6px; }}
QListWidget::item {{ min-height: 28px; padding: 0 10px; border-radius: 7px; margin: 0; }}
QListWidget::item:hover {{ background: {HOVER}; }}
QListWidget::item:selected {{ background: {ACCENT}; color: #ffffff; }}
QListWidget::item:disabled {{ color: {TEXT3}; font-size: 11px; font-weight: 600; background: transparent; }}

QScrollArea {{ border: none; }}
QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px 1px; }}
QScrollBar::handle:vertical {{ background: rgba(255, 255, 255, 18%); border-radius: 3px; min-height: 30px; }}
QScrollBar:horizontal {{ background: transparent; height: 9px; margin: 1px 2px; }}
QScrollBar::handle:horizontal {{ background: rgba(255, 255, 255, 18%); border-radius: 3px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QSplitter::handle {{ background: transparent; }}
QSplitter::handle:horizontal {{ width: 14px; }}
QSplitter::handle:vertical {{ height: 14px; }}
QGraphicsView {{ background: {CANVAS}; border: 1px solid {LINE}; border-radius: 16px; }}
QCheckBox {{ spacing: 8px; font-size: 13.5px; }}
QCheckBox::indicator {{ width: 15px; height: 15px; border: 1px solid {TEXT3}; border-radius: 4px; background: {FIELD}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QMessageBox, QMessageBox QLabel {{ background: {CARD}; }}
"""
