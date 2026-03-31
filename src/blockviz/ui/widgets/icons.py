"""Inline SVG assets for cards and navigation icons."""

from __future__ import annotations

from typing import Final

from PySide6.QtCore import QByteArray, Qt, QSize
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_CARD_ICONS: Final[dict[str, str]] = {
    "brand": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="g1" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
          <stop stop-color="#8b5cf6"/>
          <stop offset="1" stop-color="#22d3ee"/>
        </linearGradient>
      </defs>
      <rect x="4" y="4" width="24" height="24" rx="9" fill="#10172d" stroke="url(#g1)" stroke-width="2"/>
      <path d="M10 18l6-8 6 8-6 4-6-4z" fill="url(#g1)"/>
      <circle cx="16" cy="18" r="2.2" fill="#f472b6"/>
    </svg>
    """,
    "dashboard": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <rect x="4" y="4" width="24" height="24" rx="8" fill="#10172d"/>
      <rect x="8" y="9" width="7" height="6" rx="2" fill="#8b5cf6"/>
      <rect x="17" y="9" width="7" height="10" rx="2" fill="#22d3ee"/>
      <rect x="8" y="17" width="7" height="6" rx="2" fill="#f472b6"/>
      <rect x="17" y="21" width="7" height="2" rx="1" fill="#cbd5ff"/>
    </svg>
    """,
    "blocks": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <path d="M16 4l9 5v10l-9 5-9-5V9l9-5z" fill="#111933" stroke="#22d3ee" stroke-width="1.6"/>
      <path d="M16 4v10m9-5-9 5-9-5" stroke="#8b5cf6" stroke-width="1.6" stroke-linecap="round"/>
      <path d="M16 14v10" stroke="#f472b6" stroke-width="1.6" stroke-linecap="round"/>
    </svg>
    """,
    "transactions": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <rect x="4" y="6" width="24" height="20" rx="8" fill="#111933"/>
      <path d="M10 12h12M18 9l4 3-4 3" stroke="#22d3ee" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M22 20H10M14 17l-4 3 4 3" stroke="#f472b6" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """,
    "address": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <rect x="5" y="7" width="22" height="18" rx="6" fill="#111933"/>
      <circle cx="12" cy="16" r="3" fill="#22d3ee"/>
      <path d="M17 21c0-2.5 2.8-4.5 5-4.5S27 18.5 27 21" stroke="#8b5cf6" stroke-width="1.7" stroke-linecap="round"/>
      <path d="M17 12h7" stroke="#f472b6" stroke-width="1.7" stroke-linecap="round"/>
    </svg>
    """,
    "rpc": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <circle cx="16" cy="16" r="10" fill="#111933" stroke="#22d3ee" stroke-width="1.6"/>
      <path d="M11 17c3-4 7-4 10 0" stroke="#8b5cf6" stroke-width="1.8" stroke-linecap="round"/>
      <circle cx="16" cy="19" r="2.2" fill="#f472b6"/>
    </svg>
    """,
    "block": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <path d="M16 4l10 6v12l-10 6-10-6V10l10-6z" fill="#111933" stroke="#8b5cf6" stroke-width="1.6"/>
      <path d="M16 4v12m10-6-10 6-10-6" stroke="#22d3ee" stroke-width="1.6" stroke-linecap="round"/>
    </svg>
    """,
    "transaction": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <rect x="5" y="8" width="22" height="16" rx="8" fill="#111933"/>
      <path d="M10 16h10M17 12l4 4-4 4" stroke="#22d3ee" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """,
    "gas": """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <path d="M13 5h6l5 6v14H8V11z" fill="#111933" stroke="#f472b6" stroke-width="1.4"/>
      <path d="M16 13l-2 5h4l-2 5" stroke="#22d3ee" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
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
