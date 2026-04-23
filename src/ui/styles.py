
MAIN_BG = "background-color: #FFFFFF;"
START_PAGE_BG = "background-color: #ffffff;"

HEADER_TEXT = "font-size: 24px; font-weight: bold; color: #000000; border: none;"
SECTION_TITLE = "font-size: 18px; font-weight: 500; color: #000000; border: none;"

UPLOAD_ZONE_STYLE = """
    QFrame {
        border: 2px dashed #478CD1;
        border-radius: 10px;
        background-color: #F2F7FD;
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

SEARCH_STYLE = """
    QLineEdit {
        border: 1px solid #C4C4C4;
        border-radius: 4px;
        padding: 6px 10px;
        color: #333333;
        background-color: white;
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

TABLE_CONTAINER =  "border-radius: 8px; background-color: white;"
TABLE_HEADER_TEXT = "color: #333333; font-weight: 400; font-size: 13px; border: none;"

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

TOOLBAR_STYLE = "background-color: white;"

NORMAL_LABEL_STYLE = "font-size: 16px; font-weight: bold; color: #000; padding-left: 10px; border: none;"

SEPARATOR_STYLE = "color: #aaa; font-weight: bold; border: none;"

LANG_BTN_STYLE = "font-weight: bold; color: #555; margin-right: 15px; border: none;"

RIGHT_PANEL_STYLE = "background-color: #f3f3f3;"

VERIFY_TITLE_STYLE = "font-size: 18px; font-weight: normal; color: #000; margin-top: 16px; margin-bottom: 10px; border: none;"

PDF_VIEW_STYLE = """
    /* Ewentualne tło i ramka samej przeglądarki PDF */
    QPdfView {
        background-color: #E0E0E0;
        border: none;
    }

    /* --- PIONOWY PASEK (Góra/Dół) --- */
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

    /* --- POZIOMY PASEK (Lewo/Prawo - po zrobieniu Zoom In) --- */
    QScrollBar:horizontal {
        border: none;
        background: transparent; 
        height: 12px; /* Grubość paska poziomego (height zamiast width) */
        margin: 0px; 
    }
    QScrollBar::handle:horizontal {
        background: #C4C4C4; 
        min-width: 30px; /* Szerokość uchwytu (min-width zamiast min-height) */
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

DIALOG_STYLE = "background-color: white; border-radius: 12px;"

JSON_FRAME_STYLE = """
    QFrame {
        border: 1.5px dashed #478CD1;
        border-radius: 10px;
        background-color: #F2F7FD;
    }
"""

MODE_BTN_STYLE = """
    QPushButton {
        border: 1.5px solid #C4C4C4;
        border-radius: 8px;
        padding: 25px;
        background-color: white;
        font-size: 14px;
        color: #333;
    }
    QPushButton:hover { background-color: #f9f9f9; }
    QPushButton:checked { 
        border: 2px solid #2196F3; 
        background-color: #F2F7FD; 
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


FILE_BADGE_FRAME = """
    QFrame {
        border: 1px solid #C4C4C4;
        border-radius: 8px;
        background-color: #FFFFFF;
        padding: 10px;
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