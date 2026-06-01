MAIN_BG = "background-color: #FFFFFF;"
START_PAGE_BG = "background-color: #ffffff;"

HEADER_TEXT = "font-size: 24px; font-weight: bold; color: #000000; border: none;"
SECTION_TITLE = "font-size: 18px; font-weight: 500; color: #000000; border: none;"
NORMAL_LABEL_STYLE = "font-size: 16px; font-weight: bold; color: #000; padding-left: 10px; border: none;"
VERIFY_TITLE_STYLE = "font-size: 18px; font-weight: normal; color: #000; margin-top: 16px; margin-bottom: 10px; border: none;"
SEPARATOR_STYLE = "color: #aaa; font-weight: bold; border: none;"
LANG_BTN_STYLE = "font-weight: bold; color: #555; margin-right: 15px; border: none;"

UPLOAD_ZONE_STYLE = """
    QFrame {
        border: 2px dashed #478CD1;
        border-radius: 10px;
        background-color: #F2F7FD;
    }
"""

JSON_FRAME_STYLE = """
    QFrame {
        border: 1.5px dashed #478CD1;
        border-radius: 10px;
        background-color: #F2F7FD;
    }
"""

FILE_BADGE_FRAME = """
    QFrame {
        border: 1px solid #C4C4C4;
        border-radius: 8px;
        background-color: #FFFFFF;
    }
"""

BLUE_BUTTON_STYLE = """
    QPushButton {
        background-color: #2196F3;
        color: white;
        border-radius: 4px;
        padding: 6px 15px;
        font-weight: bold;
        font-size: 13px;
    }
    QPushButton:hover { 
        background-color: #1976D2; 
    }
"""

SORT_BTN_STYLE = """
    QPushButton {
        border: 1px solid #C4C4C4;
        border-radius: 4px;
        padding: 6px 10px;
        color: #333333;
        background-color: white;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #f5f5f5;
    }
"""

DELETE_BTN_STYLE = """
    QPushButton {
        color: #D32F2F; 
        font-weight: bold; 
        border: none; 
        background: none; 
        font-size: 13px;
    }
    QPushButton:hover {
        text-decoration: underline;
    }
"""

ANALIZA_BTN_STYLE = """
    QPushButton {
        background-color: #2196F3;
        color: white;
        border-radius: 8px;
        padding: 15px;
        font-weight: bold;
        font-size: 16px;
    }
    QPushButton:hover { background-color: #1976D2; }
"""

RAPORT_BTN_STYLE = """
    QPushButton {
        background-color: #2196F3;
        color: white;
        border-radius: 8px;
        padding: 15px;
        font-weight: bold;
        font-size: 16px;
    }
    QPushButton:hover { 
        background-color: #1976D2; 
    }
"""

MODE_BTN_STYLE = """
    QPushButton {
        border: 1.5px solid #C4C4C4;
        border-radius: 8px;
        padding: 5px 15px;
        background-color: white;
        font-size: 14px;
        color: #333333;
        text-align: center;
    }
    QPushButton:hover { 
        background-color: #f9f9f9; 
    }
    QPushButton:checked { 
        border: 2px solid #2196F3; 
        background-color: #F2F7FD; 
        color: #1E8CFA; 
        font-weight: bold;
    }
"""

ICON_BUTTON_STYLE = """
    QPushButton {
        border: none;
        background: transparent;
    }
    QPushButton:hover {
        background-color: #f0f0f0;
        border-radius: 4px;
    }
"""

SEARCH_STYLE = """
    QLineEdit {
        border: 1px solid #C4C4C4;
        border-radius: 4px;
        padding: 6px 10px;
        color: #333333;
        background-color: white;
    }
"""

CHECKBOX_STYLE = """
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 1px solid #C4C4C4;
        border-radius: 3px;
    }
    QCheckBox::indicator:checked {
        background-color: #2196F3;
        border: 1px solid #2196F3;
    }
"""

PROGRESS_BAR_STYLE = """
    QProgressBar {
        border-radius: 5px;
        text-align: center;
        background-color: #f0f0f0;
        height: 25px;
    }
    QProgressBar::chunk {
        border-radius: 5px;
        background-color: #2196F3;
    }
"""

TABLE_CONTAINER = "border-radius: 8px; background-color: white;"
TABLE_HEADER_TEXT = "color: #333333; font-weight: 400; font-size: 13px; border: none;"
TOOLBAR_STYLE = "background-color: white;"
RIGHT_PANEL_STYLE = "background-color: #f3f3f3;"
DIALOG_STYLE = "background-color: white; border-radius: 12px;"

PDF_VIEW_STYLE = """
    QPdfView {
        background-color: #E0E0E0;
        border: none;
    }
    QScrollBar:vertical {
        border: none;
        background: transparent; 
        width: 12px; 
        margin: 0px; 
    }
    QScrollBar::handle:vertical {
        background: #C4C4C4; 
        min-height: 30px; 
        border-radius: 6px; 
    }
    QScrollBar::handle:vertical:hover {
        background: #A0A0A0; 
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px; 
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none; 
    }
    QScrollBar:horizontal {
        border: none;
        background: transparent; 
        height: 12px; 
        margin: 0px; 
    }
    QScrollBar::handle:horizontal {
        background: #C4C4C4; 
        min-width: 30px; 
        border-radius: 6px; 
    }
    QScrollBar::handle:horizontal:hover {
        background: #A0A0A0; 
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px; 
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none; 
    }
"""

STATUS_BADGE_STYLE = """
    QLabel {
        background-color: #C8E6C9;
        color: #2E7D32;
        border-radius: 10px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 500;
        border: none;
    }
"""

BADGE_FRAME_SUCCESS = "QFrame { background-color: #D1EEDC; border-radius: 13px; border: none; }"
BADGE_ICON_SUCCESS = "QLabel { background-color: #2CA05A; color: white; border-radius: 10px; font-weight: bold; font-size: 13px; }"

BADGE_FRAME_ERROR = "QFrame { background-color: #F8D7DA; border-radius: 13px; border: none; }"
BADGE_ICON_ERROR = "QLabel { background-color: #DC3545; color: white; border-radius: 10px; font-weight: bold; font-size: 13px; }"

BADGE_TEXT_DEFAULT = "color: #000; font-weight: bold; font-size: 12px; border: none; background: transparent;"
BADGE_TEXT_ERROR = "color: #721C24; font-size: 14px; border: none; background: transparent;"

FILE_BADGE_INNER_LABELS = "border: none;"
FILE_BADGE_NAME_LABEL = "font-weight: bold; font-size: 14px; color: #000; border: none;"
FILE_BADGE_INFO_LABEL = "color: #666; font-size: 12px; border: none;"
JSON_ICON_CIRCLE = "QLabel { background-color: #BDDCFF; color: #1E8CFA; font-weight: bold; font-size: 15px; border-radius: 30px; border: none; }"
SECTION_TITLE_DARK = "font-size: 13px; font-weight: bold; color: #333;"

CONTENT_GRADE_FRAME = "QFrame { background-color: #F0F7FF; border: 2px solid #90C8FF; border-radius: 8px; }"
CONTENT_GRADE_TITLE = "color: #333; font-size: 14px; font-weight: bold; border: none; background: transparent;"
CONTENT_GRADE_VALUE = "color: #0056b3; font-size: 32px; font-weight: bold; border: none; background: transparent;"
CONTENT_GRADE_DETAILS = "color: #666; font-size: 12px; border: none; background: transparent;"
CONTENT_GRADE_MISSING = "color: #7f8c8d; font-style: italic; border: none; padding-left: 2px;"

ROW_LABEL_CLEAN = "color: #444; font-size: 13px; border: none;"
STATS_FRAME_STYLE = "QFrame { background-color: #F9F9F9; border: 1px solid #D3D3D3; border-radius: 8px; }"
STATS_ROW_NAME = "color: #555; font-size: 12px; border: none; background: transparent;"
STATS_ROW_VALUE = "color: #0056b3; font-size: 12px; border: none; background: transparent;"

TABLE_HEADER_ROW_TEXT = "color: #333; font-size: 13px; font-weight: normal; border: none; background: transparent;"
TABLE_ROW_NAME_BUTTON = """
    QPushButton {
        text-align: left; 
        font-weight: bold; 
        font-size: 14px; 
        color: #000; 
        border: none; 
        background: transparent;
    }
    QPushButton:hover { text-decoration: underline; }
"""
TABLE_ROW_SUBTITLE = "color: #666; font-size: 12px; border: none; background: transparent;"
TABLE_ROW_DATE = "color: #333; border: none; background: transparent; font-size: 13px;"

ERROR_MARKER_STYLE = """
    QPushButton {
        background-color: rgba(255, 0, 0, 180);
        border: 2px solid white;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        padding: 0px;
    }
    QPushButton:hover { background-color: red; }
"""

COMMENT_MARKER_STYLE = """
    QPushButton {
        background-color: rgba(0, 120, 255, 180);
        border: 2px solid white;
        border-radius: 8px;
        color: white;
        font-weight: bold;
    }
    QPushButton:hover { background-color: blue; }
"""

HIGHLIGHT_BOX_ERROR = "background-color: rgba(255, 0, 0, 60); border: none;"
HIGHLIGHT_BOX_COMMENT = "background-color: rgba(0, 120, 255, 60); border: none;"
HIGHLIGHT_BOX_DEFAULT = "background-color: rgba(0, 150, 255, 70); border: none;"
OFF_TOPIC_TITLE_STYLE = "font-size: 11px; font-weight: bold; color: #D32F2F; margin-top: 8px; background: transparent; border: none;"
OFF_TOPIC_ITEM_STYLE = "color: #C62828; font-size: 11px; padding-left: 5px; background: transparent; border: none;"