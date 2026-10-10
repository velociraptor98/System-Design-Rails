BG = "#14161a"
SURFACE = "#1b1e24"
RAISED = "#23272f"
BORDER = "#2e333d"
TEXT = "#e7e9ee"
MUTED = "#98a1b0"
ACCENT = "#6ea8fe"
GOOD = "#5fcf8a"
WARN = "#e5b567"
BAD = "#ef7d7d"

STYLESHEET = f"""
* {{ font-size: 13px; }}
QWidget {{ background: {BG}; color: {TEXT}; }}
QToolTip {{ background: {RAISED}; color: {TEXT}; border: 1px solid {BORDER}; padding: 4px; }}

#sidebar {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
#sidebar QLabel {{ background: transparent; }}
#appTitle {{ font-size: 15px; font-weight: 600; }}
#navButton {{
    background: transparent; border: none; border-radius: 6px;
    padding: 9px 12px; text-align: left; color: {MUTED};
}}
#navButton:hover {{ background: {RAISED}; color: {TEXT}; }}
#navButton:checked {{ background: {RAISED}; color: {TEXT}; font-weight: 600; }}

#h1 {{ font-size: 22px; font-weight: 600; }}
#h2 {{ font-size: 16px; font-weight: 600; }}
#h3 {{ font-size: 13px; font-weight: 600; color: {MUTED}; }}
#muted {{ color: {MUTED}; }}
#prompt {{ font-size: 14px; }}

#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}
#card QLabel, #card QCheckBox {{ background: transparent; }}
#questionCard {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}
#questionCard:hover {{ border-color: {ACCENT}; }}
#questionCard QLabel {{ background: transparent; }}

QLabel#chip {{
    background: {RAISED}; color: {MUTED}; border-radius: 9px;
    padding: 2px 8px; font-size: 11px;
}}
QLabel#chipGood {{ background: #1f3a2b; color: {GOOD}; border-radius: 9px; padding: 2px 8px; font-size: 11px; }}
QLabel#chipWarn {{ background: #3d3320; color: {WARN}; border-radius: 9px; padding: 2px 8px; font-size: 11px; }}
QLabel#chipBad {{ background: #40262a; color: {BAD}; border-radius: 9px; padding: 2px 8px; font-size: 11px; }}
QLabel#disclaimer {{
    background: #3d3320; color: {WARN}; border-radius: 6px; padding: 8px 10px;
}}
QLabel#realSystem {{
    background: #1f3a2b; color: {GOOD}; border-radius: 6px; padding: 8px 10px;
}}
QLabel#citation {{ color: {MUTED}; font-size: 11px; background: transparent; }}
QLabel#synthesisText {{ color: {WARN}; font-style: italic; }}

QPushButton {{
    background: {RAISED}; border: 1px solid {BORDER}; border-radius: 6px; padding: 6px 14px;
}}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton:disabled {{ color: {MUTED}; }}
QPushButton#primary {{ background: {ACCENT}; color: #0d1117; border: none; font-weight: 600; }}
QPushButton#primary:hover {{ background: #8bbaff; }}
QPushButton#link {{ background: transparent; border: none; color: {ACCENT}; padding: 2px 0; text-align: left; }}
QPushButton#link:hover {{ text-decoration: underline; }}
QPushButton#stage {{
    background: transparent; border: none; border-bottom: 2px solid transparent;
    border-radius: 0; padding: 8px 14px; color: {MUTED};
}}
QPushButton#stage:hover {{ color: {TEXT}; }}
QPushButton#stage:checked {{ color: {TEXT}; border-bottom: 2px solid {ACCENT}; font-weight: 600; }}

QPlainTextEdit, QLineEdit, QSpinBox, QComboBox {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 6px; padding: 5px 7px;
    selection-background-color: {ACCENT}; selection-color: #0d1117;
}}
QPlainTextEdit:focus, QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QLineEdit:disabled {{ color: {MUTED}; background: {BG}; }}
QComboBox QAbstractItemView {{ background: {SURFACE}; border: 1px solid {BORDER}; selection-background-color: {RAISED}; }}

QListWidget {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; outline: none; padding: 4px; }}
QListWidget::item {{ padding: 6px 8px; border-radius: 5px; }}
QListWidget::item:selected {{ background: {RAISED}; color: {TEXT}; }}
QListWidget::item:disabled {{ color: {MUTED}; font-size: 11px; }}

QScrollArea {{ border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 5px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QSplitter::handle {{ background: {BORDER}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}
QGraphicsView {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 8px; }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ background: transparent; color: {MUTED}; padding: 7px 14px; border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {TEXT}; border-bottom: 2px solid {ACCENT}; }}
QCheckBox::indicator {{ width: 15px; height: 15px; border: 1px solid {MUTED}; border-radius: 4px; background: {SURFACE}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
"""
