from __future__ import annotations

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

# name: (stroke width, drawing), all on a 24x24 grid.
ICONS = {
    "questions": (1.8, '<path d="M9.1 9a3 3 0 1 1 4.3 2.7c-.9.5-1.4 1.1-1.4 2.1"/><circle cx="12" cy="12" r="9.5"/><path d="M12 17.2h.01"/>'),
    "pages": (1.8, '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z"/><path d="M4 5.5v16M8.5 7.5h7"/>'),
    "sandbox": (1.8, '<path d="M12 2.8 20 7.4v9.2l-8 4.6-8-4.6V7.4z"/><path d="M4.2 7.6 12 12l7.8-4.4M12 12v9"/>'),
    "back": (2.6, '<path d="M15 4.5 7.5 12l7.5 7.5"/>'),
    "reveal": (2.0, '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>'),
    "drill": (2.0, '<path d="M3 12a9 9 0 0 1 15.5-6.2L21 8.5M21 3v5.5h-5.5M21 12a9 9 0 0 1-15.5 6.2L3 15.5M3 21v-5.5h5.5"/>'),
    "search": (2.2, '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m20 20-4.8-4.8"/>'),
    "external": (2.4, '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>'),
}


def svg(name: str, color: str) -> bytes:
    width, drawing = ICONS[name]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">{drawing}</svg>'
    ).encode()


def pixmap(name: str, color: str, size: int) -> QPixmap:
    scale = 2
    image = QPixmap(size * scale, size * scale)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    QSvgRenderer(QByteArray(svg(name, color))).render(painter, QRectF(0, 0, size * scale, size * scale))
    painter.end()
    image.setDevicePixelRatio(scale)
    return image


def icon(name: str, color: str, size: int) -> QIcon:
    return QIcon(pixmap(name, color, size))
