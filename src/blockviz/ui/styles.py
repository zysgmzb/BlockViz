"""Centralized palettes and stylesheet helpers."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

# Primary BlockViz color tokens
BACKGROUND_COLOR = QColor("#0f111b")
SURFACE_COLOR = QColor("#191c29")
CARD_COLOR = QColor("#1f2333")
PRIMARY_COLOR = QColor("#4f7dff")
ACCENT_COLOR = QColor("#4ff0b4")
TEXT_COLOR = QColor("#f7f8fb")
SUBTLE_TEXT_COLOR = QColor("#97a0c3")

BASE_STYLESHEET = """
QMainWindow {
    background-color: #0f111b;
}
QStatusBar {
    background: #191c29;
    color: #f7f8fb;
    border: 0;
}
QLineEdit, QComboBox, QListWidget {
    background-color: #1f2333;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 6px 10px;
    color: #f7f8fb;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #4f7dff;
}
QPushButton {
    border-radius: 8px;
    padding: 8px 14px;
    background-color: #4f7dff;
    color: #f7f8fb;
    border: none;
    font-weight: 600;
}
QPushButton:disabled {
    background-color: rgba(255, 255, 255, 0.12);
    color: rgba(255, 255, 255, 0.4);
}
"""


def _build_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, BACKGROUND_COLOR)
    palette.setColor(QPalette.AlternateBase, SURFACE_COLOR)
    palette.setColor(QPalette.Base, SURFACE_COLOR)
    palette.setColor(QPalette.Button, PRIMARY_COLOR)
    palette.setColor(QPalette.ButtonText, TEXT_COLOR)
    palette.setColor(QPalette.WindowText, TEXT_COLOR)
    palette.setColor(QPalette.Text, TEXT_COLOR)
    palette.setColor(QPalette.ToolTipBase, CARD_COLOR)
    palette.setColor(QPalette.ToolTipText, TEXT_COLOR)
    palette.setColor(QPalette.Highlight, PRIMARY_COLOR)
    palette.setColor(QPalette.HighlightedText, TEXT_COLOR)
    palette.setColor(QPalette.Link, ACCENT_COLOR)
    palette.setColor(QPalette.Disabled, QPalette.Text, SUBTLE_TEXT_COLOR)
    return palette


def apply_theme(app: QApplication) -> None:
    """Apply palettes, fonts, and stylesheets to the QApplication."""
    palette = _build_palette()
    app.setPalette(palette)
    app.setStyleSheet(BASE_STYLESHEET)
    font = QFont("Segoe UI", 10)
    app.setFont(font)
