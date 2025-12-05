"""Inline SVG assets for InfoCard icons."""

from __future__ import annotations

from typing import Final

from PySide6.QtCore import QByteArray, Qt, QSize
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_CARD_ICONS: Final[dict[str, str]] = {
    "block": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <rect x="4" y="10" width="24" height="18" rx="6" fill="#2c3148"/>
        <path d="M8 14h16v2H8zm0 6h10v2H8z" fill="#4f7dff"/>
    </svg>
    """,
    "transaction": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="12" fill="#253046"/>
        <path d="M11 16h10M16 11l5 5-5 5" stroke="#4ff0b4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """,
    "gas": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 6h8l4 6v14H8V12z" fill="#2b2f45"/>
        <path d="M12 6v20M20 6v20" stroke="#97a0c3" stroke-width="1.5" stroke-linecap="round"/>
        <path d="M16 20l-2 4h4z" fill="#f5a524"/>
    </svg>
    """,
    "address": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <rect x="6" y="8" width="20" height="16" rx="4" fill="#2b2f45"/>
        <circle cx="12" cy="16" r="3" fill="#4f7dff"/>
        <path d="M16 22c0-2 3-3 4-3s4 1 4 3" stroke="#4ff0b4" stroke-width="1.4" stroke-linecap="round"/>
    </svg>
    """,
}


def get_icon_svg(name: str | None) -> str | None:
    """Return SVG markup for a given icon name."""
    if not name:
        return None
    return _CARD_ICONS.get(name)


def build_icon(name: str | None, size: int = 18) -> QIcon | None:
    """Render the SVG as a QIcon."""
    svg = get_icon_svg(name)
    if not svg:
        return None
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)
