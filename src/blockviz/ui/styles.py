"""Centralized palettes and stylesheet helpers."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

DEFAULT_THEME = "nebula"
_THEME_ORDER = ("nebula", "aurora", "ocean", "ember")
_THEME_LABELS = {
    "nebula": "Nebula",
    "aurora": "Aurora",
    "ocean": "Ocean",
    "ember": "Ember",
}
_THEME_PRESETS = {
    "nebula": {
        "background": "#050816",
        "surface": "#0a1022",
        "card": "#111933",
        "elevated": "#182349",
        "primary": "#8b5cf6",
        "accent": "#22d3ee",
        "highlight": "#f472b6",
        "success": "#34d399",
        "warning": "#f59e0b",
        "text": "#eef2ff",
        "subtle_text": "#a4b3d9",
        "muted_text": "#6f7ea8",
        "border": "rgba(151, 173, 255, 0.16)",
        "soft_border": "rgba(151, 173, 255, 0.08)",
        "hover": "rgba(139, 92, 246, 0.14)",
        "input_background": "rgba(10, 16, 34, 0.92)",
    },
    "aurora": {
        "background": "#041510",
        "surface": "#09211a",
        "card": "#0f2c23",
        "elevated": "#15392d",
        "primary": "#10b981",
        "accent": "#2dd4bf",
        "highlight": "#84cc16",
        "success": "#34d399",
        "warning": "#fbbf24",
        "text": "#ecfdf5",
        "subtle_text": "#9fd6c1",
        "muted_text": "#5f917d",
        "border": "rgba(125, 211, 177, 0.16)",
        "soft_border": "rgba(125, 211, 177, 0.08)",
        "hover": "rgba(16, 185, 129, 0.14)",
        "input_background": "rgba(9, 33, 26, 0.92)",
    },
    "ocean": {
        "background": "#06111f",
        "surface": "#0c1d33",
        "card": "#122742",
        "elevated": "#183458",
        "primary": "#3b82f6",
        "accent": "#22d3ee",
        "highlight": "#818cf8",
        "success": "#34d399",
        "warning": "#f59e0b",
        "text": "#eff6ff",
        "subtle_text": "#a7c7f2",
        "muted_text": "#698ab4",
        "border": "rgba(125, 169, 255, 0.16)",
        "soft_border": "rgba(125, 169, 255, 0.08)",
        "hover": "rgba(59, 130, 246, 0.14)",
        "input_background": "rgba(12, 29, 51, 0.92)",
    },
    "ember": {
        "background": "#160804",
        "surface": "#26100a",
        "card": "#34160f",
        "elevated": "#482015",
        "primary": "#f97316",
        "accent": "#fb7185",
        "highlight": "#f59e0b",
        "success": "#34d399",
        "warning": "#fbbf24",
        "text": "#fff7ed",
        "subtle_text": "#f2c3a7",
        "muted_text": "#b7866a",
        "border": "rgba(251, 146, 60, 0.16)",
        "soft_border": "rgba(251, 146, 60, 0.08)",
        "hover": "rgba(249, 115, 22, 0.14)",
        "input_background": "rgba(38, 16, 10, 0.92)",
    },
}

CURRENT_THEME = DEFAULT_THEME
BACKGROUND_COLOR = QColor("#050816")
SURFACE_COLOR = QColor("#0a1022")
CARD_COLOR = QColor("#111933")
ELEVATED_CARD_COLOR = QColor("#182349")
PRIMARY_COLOR = QColor("#8b5cf6")
ACCENT_COLOR = QColor("#22d3ee")
HIGHLIGHT_COLOR = QColor("#f472b6")
SUCCESS_COLOR = QColor("#34d399")
WARNING_COLOR = QColor("#f59e0b")
TEXT_COLOR = QColor("#eef2ff")
SUBTLE_TEXT_COLOR = QColor("#a4b3d9")
MUTED_TEXT_COLOR = QColor("#6f7ea8")
BORDER_COLOR = "rgba(151, 173, 255, 0.16)"
SOFT_BORDER_COLOR = "rgba(151, 173, 255, 0.08)"
HOVER_COLOR = "rgba(139, 92, 246, 0.14)"
INPUT_BACKGROUND = "rgba(10, 16, 34, 0.92)"


def _rgba(color: QColor, alpha: float) -> str:
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha:.2f})"


def normalize_theme_name(theme_name: str | None) -> str:
    if not theme_name:
        return DEFAULT_THEME
    candidate = str(theme_name).strip().lower()
    return candidate if candidate in _THEME_PRESETS else DEFAULT_THEME


def theme_display_name(theme_name: str | None) -> str:
    normalized = normalize_theme_name(theme_name)
    return _THEME_LABELS[normalized]


def available_theme_options() -> list[tuple[str, str]]:
    return [(key, _THEME_LABELS[key]) for key in _THEME_ORDER]


def current_theme_name() -> str:
    return CURRENT_THEME


def set_theme(theme_name: str | None) -> str:
    normalized = normalize_theme_name(theme_name)
    preset = _THEME_PRESETS[normalized]
    global CURRENT_THEME
    global BACKGROUND_COLOR, SURFACE_COLOR, CARD_COLOR, ELEVATED_CARD_COLOR
    global PRIMARY_COLOR, ACCENT_COLOR, HIGHLIGHT_COLOR, SUCCESS_COLOR, WARNING_COLOR
    global TEXT_COLOR, SUBTLE_TEXT_COLOR, MUTED_TEXT_COLOR
    global BORDER_COLOR, SOFT_BORDER_COLOR, HOVER_COLOR, INPUT_BACKGROUND

    CURRENT_THEME = normalized
    BACKGROUND_COLOR = QColor(preset["background"])
    SURFACE_COLOR = QColor(preset["surface"])
    CARD_COLOR = QColor(preset["card"])
    ELEVATED_CARD_COLOR = QColor(preset["elevated"])
    PRIMARY_COLOR = QColor(preset["primary"])
    ACCENT_COLOR = QColor(preset["accent"])
    HIGHLIGHT_COLOR = QColor(preset["highlight"])
    SUCCESS_COLOR = QColor(preset["success"])
    WARNING_COLOR = QColor(preset["warning"])
    TEXT_COLOR = QColor(preset["text"])
    SUBTLE_TEXT_COLOR = QColor(preset["subtle_text"])
    MUTED_TEXT_COLOR = QColor(preset["muted_text"])
    BORDER_COLOR = str(preset["border"])
    SOFT_BORDER_COLOR = str(preset["soft_border"])
    HOVER_COLOR = str(preset["hover"])
    INPUT_BACKGROUND = str(preset["input_background"])
    return normalized


def _build_base_stylesheet() -> str:
    return f"""
QMainWindow {{
    background: qradialgradient(cx:0.12, cy:0.08, radius:1.15, fx:0.12, fy:0.08,
        stop:0 {_rgba(ACCENT_COLOR, 0.12)},
        stop:0.35 {_rgba(PRIMARY_COLOR, 0.10)},
        stop:1 {BACKGROUND_COLOR.name()});
}}
QWidget {{
    color: {TEXT_COLOR.name()};
    font-family: 'Inter', 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
}}
QStatusBar {{
    background: {_rgba(SURFACE_COLOR, 0.90)};
    color: {SUBTLE_TEXT_COLOR.name()};
    border-top: 1px solid {SOFT_BORDER_COLOR};
    padding-left: 12px;
}}
QStatusBar::item {{
    border: none;
}}
QLabel {{
    background: transparent;
}}
QLineEdit, QComboBox {{
    background-color: {INPUT_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 14px;
    padding: 11px 14px;
    color: {TEXT_COLOR.name()};
    selection-background-color: {_rgba(PRIMARY_COLOR, 0.38)};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {_rgba(ACCENT_COLOR, 0.55)};
    background-color: {_rgba(SURFACE_COLOR, 1.0)};
}}
QLineEdit::placeholder {{
    color: {MUTED_TEXT_COLOR.name()};
}}
QPushButton {{
    border-radius: 14px;
    padding: 10px 16px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {PRIMARY_COLOR.name()}, stop:1 {HIGHLIGHT_COLOR.name()});
    color: {TEXT_COLOR.name()};
    border: 1px solid {_rgba(HIGHLIGHT_COLOR, 0.24)};
    font-weight: 700;
}}
QPushButton:hover {{
    border: 1px solid {_rgba(ACCENT_COLOR, 0.34)};
}}
QPushButton:pressed {{
    background: {PRIMARY_COLOR.darker(110).name()};
}}
QPushButton:disabled {{
    background: rgba(255, 255, 255, 0.06);
    color: rgba(255, 255, 255, 0.34);
    border: 1px solid {SOFT_BORDER_COLOR};
}}
QListWidget {{
    background-color: {_rgba(CARD_COLOR, 0.72)};
    color: {TEXT_COLOR.name()};
    border: 1px solid {SOFT_BORDER_COLOR};
    border-radius: 22px;
    padding: 10px;
    outline: none;
}}
QListWidget::item {{
    padding: 14px 16px;
    border-radius: 14px;
    margin: 3px 0;
}}
QListWidget::item:hover {{
    background-color: {HOVER_COLOR};
}}
QListWidget::item:selected {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {_rgba(PRIMARY_COLOR, 0.28)}, stop:1 {_rgba(ACCENT_COLOR, 0.18)});
    border: 1px solid {_rgba(ACCENT_COLOR, 0.28)};
    color: {TEXT_COLOR.name()};
}}
QPlainTextEdit, QTextEdit {{
    background-color: {_rgba(BACKGROUND_COLOR, 0.92)};
    border: 1px solid {BORDER_COLOR};
    border-radius: 16px;
    font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.94);
    padding: 14px;
    selection-background-color: {_rgba(ACCENT_COLOR, 0.28)};
}}
QPlainTextEdit:focus, QTextEdit:focus {{
    border: 1px solid {_rgba(ACCENT_COLOR, 0.42)};
}}
QTableWidget {{
    background-color: {_rgba(CARD_COLOR, 0.72)};
    alternate-background-color: {_rgba(ELEVATED_CARD_COLOR, 0.88)};
    border: 1px solid {SOFT_BORDER_COLOR};
    border-radius: 20px;
    gridline-color: rgba(151, 173, 255, 0.06);
    padding: 8px;
    color: {TEXT_COLOR.name()};
    selection-background-color: rgba(255, 255, 255, 0.01);
    outline: none;
}}
QTableWidget::item:selected {{
    background: rgba(255, 255, 255, 0.01);
    color: {TEXT_COLOR.name()};
}}
QTableWidget::item:focus {{
    outline: none;
    border: none;
}}
QHeaderView::section {{
    background-color: transparent;
    color: {SUBTLE_TEXT_COLOR.name()};
    border: none;
    border-bottom: 1px solid {SOFT_BORDER_COLOR};
    padding: 13px 10px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.8px;
}}
QTableCornerButton::section {{
    background-color: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 6px 2px 6px 2px;
}}
QScrollBar::handle:vertical {{
    background: {_rgba(SUBTLE_TEXT_COLOR, 0.22)};
    border-radius: 5px;
    min-height: 28px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 2px 6px 2px 6px;
}}
QScrollBar::handle:horizontal {{
    background: {_rgba(SUBTLE_TEXT_COLOR, 0.22)};
    border-radius: 5px;
    min-width: 28px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QDialog {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {SURFACE_COLOR.name()}, stop:1 {CARD_COLOR.name()});
}}
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 6px;
    border: 1px solid {BORDER_COLOR};
    background: rgba(255, 255, 255, 0.04);
}}
QCheckBox::indicator:checked {{
    background: {ACCENT_COLOR.name()};
    border: 1px solid {_rgba(ACCENT_COLOR, 0.50)};
}}
"""


def panel_surface_stylesheet() -> str:
    return f"""
        background: {_rgba(SURFACE_COLOR, 0.84)};
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.03);
    """


def shell_frame_stylesheet() -> str:
    return f"""
        background: {_rgba(BACKGROUND_COLOR, 0.88)};
        border-radius: 32px;
        border: 1px solid {_rgba(SUBTLE_TEXT_COLOR, 0.08)};
    """


def content_shell_stylesheet() -> str:
    return f"""
        background: {_rgba(SURFACE_COLOR, 0.90)};
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.025);
    """


def sidebar_card_stylesheet() -> str:
    return f"""
        background: {_rgba(SURFACE_COLOR, 0.86)};
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.035);
    """


def hero_panel_stylesheet() -> str:
    return f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {_rgba(PRIMARY_COLOR, 0.18)},
            stop:0.42 {_rgba(ACCENT_COLOR, 0.10)},
            stop:1 {_rgba(CARD_COLOR, 0.98)});
        border-radius: 26px;
        border: 1px solid {_rgba(SUBTLE_TEXT_COLOR, 0.12)};
    """


def page_eyebrow_stylesheet() -> str:
    return f"font-size: 11px; font-weight: 800; color: {ACCENT_COLOR.name()}; letter-spacing: 2px; text-transform: uppercase;"


def page_title_stylesheet() -> str:
    return f"font-size: 30px; font-weight: 800; color: {TEXT_COLOR.name()}; letter-spacing: 0.2px;"


def page_subtitle_stylesheet() -> str:
    return f"font-size: 13px; color: {SUBTLE_TEXT_COLOR.name()}; line-height: 1.5;"


def section_title_stylesheet() -> str:
    return f"font-size: 16px; font-weight: 800; color: {TEXT_COLOR.name()}; letter-spacing: 0.4px;"


def hint_label_stylesheet() -> str:
    return f"color: {SUBTLE_TEXT_COLOR.name()}; font-size: 12px;"


def hint_banner_stylesheet() -> str:
    return f"""
        color: {TEXT_COLOR.name()};
        font-size: 12px;
        padding: 10px 14px;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid {SOFT_BORDER_COLOR};
    """


def status_pill_stylesheet(connected: bool | None = None) -> str:
    if connected is True:
        bg = _rgba(SUCCESS_COLOR, 0.14)
        border = _rgba(SUCCESS_COLOR, 0.28)
        color = SUCCESS_COLOR.name()
    elif connected is False:
        bg = _rgba(HIGHLIGHT_COLOR, 0.12)
        border = _rgba(HIGHLIGHT_COLOR, 0.24)
        color = HIGHLIGHT_COLOR.name()
    else:
        bg = _rgba(ACCENT_COLOR, 0.10)
        border = _rgba(ACCENT_COLOR, 0.22)
        color = ACCENT_COLOR.name()
    return f"""
        color: {color};
        font-size: 11px;
        font-weight: 800;
        padding: 7px 12px;
        border-radius: 999px;
        background: {bg};
        border: 1px solid {border};
    """


def inspector_nav_stylesheet() -> str:
    return f"""
        QListWidget {{
            background: transparent;
            color: {TEXT_COLOR.name()};
            border: none;
            border-radius: 18px;
            padding: 4px;
        }}
        QListWidget::item {{
            padding: 15px 16px;
            border-radius: 14px;
            margin: 3px 0;
        }}
        QListWidget::item:hover {{
            background-color: {_rgba(PRIMARY_COLOR, 0.10)};
        }}
        QListWidget::item:selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {_rgba(PRIMARY_COLOR, 0.22)}, stop:1 {_rgba(ACCENT_COLOR, 0.12)});
            border: none;
            color: {TEXT_COLOR.name()};
        }}
    """


def nav_button_stylesheet() -> str:
    return f"""
        QPushButton {{
            text-align: left;
            padding: 16px 18px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid transparent;
            border-radius: 18px;
            color: {TEXT_COLOR.name()};
            font-size: 13px;
            font-weight: 700;
        }}
        QPushButton:hover {{
            background: {_rgba(PRIMARY_COLOR, 0.10)};
            border: 1px solid {_rgba(PRIMARY_COLOR, 0.18)};
        }}
        QPushButton:checked {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {_rgba(PRIMARY_COLOR, 0.26)}, stop:1 {_rgba(ACCENT_COLOR, 0.16)});
            border: 1px solid {_rgba(ACCENT_COLOR, 0.26)};
        }}
        QPushButton:pressed {{
            background: {_rgba(PRIMARY_COLOR, 0.18)};
        }}
    """


def icon_button_stylesheet() -> str:
    return f"""
        QPushButton {{
            background: rgba(255, 255, 255, 0.035);
            border: none;
            border-radius: 12px;
            color: rgba(255, 255, 255, 0.88);
            font-size: 14px;
            padding: 0;
        }}
        QPushButton:hover {{
            background: {_rgba(ACCENT_COLOR, 0.10)};
            border: none;
            color: {TEXT_COLOR.name()};
        }}
        QPushButton:pressed {{
            background: {_rgba(PRIMARY_COLOR, 0.14)};
        }}
    """


def accent_button_stylesheet() -> str:
    return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {PRIMARY_COLOR.darker(112).name()},
                stop:0.55 {PRIMARY_COLOR.name()},
                stop:1 {HIGHLIGHT_COLOR.name()});
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-bottom: 1px solid {_rgba(ACCENT_COLOR, 0.18)};
            border-radius: 15px;
            color: #ffffff;
            font-size: 12px;
            font-weight: 800;
            padding: 10px 17px;
            min-height: 18px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {PRIMARY_COLOR.darker(103).name()},
                stop:0.52 {PRIMARY_COLOR.lighter(112).name()},
                stop:1 {HIGHLIGHT_COLOR.lighter(114).name()});
            border: 1px solid {_rgba(ACCENT_COLOR, 0.52)};
            border-bottom: 1px solid rgba(255, 255, 255, 0.24);
            color: #ffffff;
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {PRIMARY_COLOR.darker(118).name()},
                stop:1 {HIGHLIGHT_COLOR.darker(115).name()});
            border: 1px solid {_rgba(ACCENT_COLOR, 0.26)};
            padding-top: 11px;
            padding-bottom: 9px;
        }}
        QPushButton:disabled {{
            background: rgba(255, 255, 255, 0.08);
            color: rgba(255, 255, 255, 0.35);
            border: 1px solid {SOFT_BORDER_COLOR};
        }}
    """


def secondary_button_stylesheet() -> str:
    return f"""
        QPushButton {{
            background: rgba(255, 255, 255, 0.035);
            border: none;
            border-radius: 14px;
            color: {TEXT_COLOR.name()};
            font-size: 12px;
            font-weight: 700;
            padding: 9px 15px;
        }}
        QPushButton:hover {{
            background: {_rgba(ACCENT_COLOR, 0.08)};
            border: none;
        }}
        QPushButton:disabled {{
            background: rgba(255, 255, 255, 0.04);
            color: rgba(255, 255, 255, 0.35);
            border: none;
        }}
    """


def text_view_stylesheet() -> str:
    return f"""
        QPlainTextEdit {{
            background-color: {_rgba(BACKGROUND_COLOR, 0.72)};
            border: none;
            border-radius: 18px;
            font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.94);
            padding: 14px;
            selection-background-color: {_rgba(ACCENT_COLOR, 0.30)};
        }}
        QPlainTextEdit:focus {{
            background-color: {_rgba(BACKGROUND_COLOR, 0.80)};
        }}
    """


def table_widget_stylesheet() -> str:
    return f"""
        QTableWidget {{
            background-color: {_rgba(CARD_COLOR, 0.76)};
            alternate-background-color: {_rgba(ELEVATED_CARD_COLOR, 0.92)};
            border: 1px solid {SOFT_BORDER_COLOR};
            border-radius: 20px;
            gridline-color: rgba(151, 173, 255, 0.06);
            padding: 10px;
        }}
        QTableWidget::item {{
            padding: 10px;
            border: none;
        }}
        QTableWidget::item:hover {{
            background-color: {_rgba(ACCENT_COLOR, 0.04)};
        }}
        QHeaderView::section {{
            background: transparent;
            border: none;
            border-bottom: 1px solid {SOFT_BORDER_COLOR};
            color: {SUBTLE_TEXT_COLOR.name()};
            padding: 13px 10px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.8px;
        }}
    """


def _build_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, BACKGROUND_COLOR)
    palette.setColor(QPalette.AlternateBase, ELEVATED_CARD_COLOR)
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


def apply_theme(app: QApplication, theme_name: str | None = None) -> str:
    """Apply palettes, fonts, and stylesheets to the QApplication."""
    applied_theme = set_theme(theme_name)
    app.setPalette(_build_palette())
    app.setStyleSheet(_build_base_stylesheet())
    app.setFont(QFont("Inter", 10))
    return applied_theme
