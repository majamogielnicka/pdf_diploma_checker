import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QGraphicsDropShadowEffect 
from PySide6.QtGui import QColor
import styles

class StartPage(QWidget):
    fileDropped = Signal(str)
    openRequested = Signal(str)
    deleteRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(styles.START_PAGE_BG)
        
        self.sort_newest = True
        self.all_files = [] 
        self.search_text = ""
        
        self.setup_ui()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith('.pdf'): self.fileDropped.emit(path)
            event.acceptProposedAction()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(70)
        self.header_frame.setStyleSheet("background-color: #FFFFFF; border: none;")

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(30, 0, 30, 0)

        title = QLabel("Dokumenty")
        title.setStyleSheet(styles.HEADER_TEXT + " background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        shadow = QGraphicsDropShadowEffect(self.header_frame)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.header_frame.setGraphicsEffect(shadow)
        main_layout.addWidget(self.header_frame)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        self.upload_frame = QFrame()
        self.upload_frame.setStyleSheet(styles.UPLOAD_ZONE_STYLE)
        self.upload_frame.setFixedHeight(250)
        
        up_layout = QVBoxLayout(self.upload_frame)
        up_layout.setSpacing(10)
        
        self.pdf_icon = QLabel()
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "assets", "pdf_file.svg")
        
        if os.path.exists(icon_path):
            self.pdf_icon.setPixmap(QIcon(icon_path).pixmap(QSize(50, 50)))
        else:
            self.pdf_icon.setText("📄")
            
        self.pdf_icon.setFixedSize(70, 70)
        self.pdf_icon.setAlignment(Qt.AlignCenter)
        self.pdf_icon.setStyleSheet("""
            QLabel {
                background-color: #BDDCFF;
                border-radius: 35px;
                border: none;
            }
        """)
        
        txt_drag = QLabel("Przeciągnij tu plik")
        txt_drag.setStyleSheet("font-weight: bold; font-size: 14px; border: none; background: transparent;")
        
        self.add_btn = QPushButton("+ Dodaj plik")
        self.add_btn.setStyleSheet(styles.BLUE_BUTTON_STYLE)
        self.add_btn.setCursor(Qt.PointingHandCursor)

        up_layout.addStretch()
        up_layout.addWidget(self.pdf_icon, alignment=Qt.AlignCenter)
        up_layout.addWidget(txt_drag, alignment=Qt.AlignCenter)
        up_layout.addWidget(QLabel("albo", styleSheet="border:none; background: transparent;"), alignment=Qt.AlignCenter)
        up_layout.addWidget(self.add_btn, alignment=Qt.AlignCenter)
        up_layout.addStretch()
        
        content_layout.addWidget(self.upload_frame)

        self.docs_card = QFrame()
        self.docs_card.setObjectName("DocsCard")
        self.docs_card.setStyleSheet("""
            QFrame#DocsCard {
                background-color: #FFFFFF;
                border: 1px solid #C4C4C4;
                border-radius: 8px;
            }
        """)
        
        card_layout = QVBoxLayout(self.docs_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        search_section = QHBoxLayout()
        section_title = QLabel("Moje dokumenty")
        section_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; border: none; background: transparent;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Szukaj po nazwie...")
        self.search_input.setStyleSheet(styles.SEARCH_STYLE)
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.on_search)
        
        self.sort_btn = QPushButton("⇅ Sortuj od: najnowszego")
        self.sort_btn.setStyleSheet(styles.SORT_BTN_STYLE)
        self.sort_btn.setCursor(Qt.PointingHandCursor)
        self.sort_btn.setFixedWidth(185) 
        self.sort_btn.clicked.connect(self.toggle_sort)

        search_section.addWidget(section_title)
        search_section.addStretch()
        search_section.addWidget(self.search_input)
        search_section.addWidget(self.sort_btn)
        card_layout.addLayout(search_section)

        self.table_container = QWidget()
        self.table_container.setStyleSheet("border: none; background: transparent;")
        self.table_layout = QVBoxLayout(self.table_container)
        self.table_layout.setContentsMargins(0, 10, 0, 0)
        self.table_layout.setSpacing(0)
        
        card_layout.addWidget(self.table_container)
        card_layout.addStretch()

        content_layout.addWidget(self.docs_card)
        main_layout.addWidget(self.content_widget)
        self.header_frame.raise_()

    def on_search(self, text):
        self.search_text = text.lower()
        self._apply_sort_and_render()

    def toggle_sort(self):
        self.sort_newest = not self.sort_newest
        if self.sort_newest:
            self.sort_btn.setText("⇅ Sortuj od: najnowszego")
        else:
            self.sort_btn.setText("⇅ Sortuj od: najstarszego")
        self._apply_sort_and_render()

    def render_doc_list(self, pliki):
        self.all_files = pliki 
        self._apply_sort_and_render()

    def _apply_sort_and_render(self):
        filtered = [p for p in self.all_files if self.search_text in p.get('nazwa_pliku', '').lower()]
        filtered.sort(key=lambda x: (x.get('data_dodania', ''), x.get('nazwa_pliku', '')), reverse=self.sort_newest)

        while self.table_layout.count():
            child = self.table_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        header_row = QWidget()
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(5, 0, 0, 5) 
        
        header_style = "color: #333; font-size: 13px; font-weight: normal; border: none; background: transparent;"
        
        h_name = QLabel("nazwa pliku"); h_name.setStyleSheet(header_style)
        h_config = QLabel("plik konfiguracyjny"); h_config.setStyleSheet(header_style)
        h_date = QLabel("data dodania"); h_date.setStyleSheet(header_style)
        
        header_layout.addWidget(QLabel(""), 0)
        header_layout.addWidget(h_name)
        
        header_layout.addStretch()
        
        header_layout.addWidget(h_config)
        header_layout.addSpacing(80)
        header_layout.addWidget(h_date)
        header_layout.addSpacing(90)
        self.table_layout.addWidget(header_row)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #C4C4C4; border: none;")
        self.table_layout.addWidget(line)

        for p in filtered:
            has_config = p.get('plik_konfiguracyjny', True) 

            self.add_row(
                name=p.get('nazwa_pliku', 'Nieznany'), 
                path=p.get('sciezka_lokalna', ''), 
                date=p.get('data_dodania', 'Brak daty'),
                has_config=has_config
            )

    def add_row(self, name, path, date, has_config=True):
        row = QWidget()
        row_l = QHBoxLayout(row)
        row_l.setContentsMargins(5, 10, 5, 10)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "assets", "pdf_file.svg")
        if os.path.exists(icon_path):
            icon_widget = QSvgWidget(icon_path)
            icon_widget.setFixedSize(30, 36) 
            icon_widget.setStyleSheet("background: transparent;")
        else:
            icon_widget = QLabel("📄")
            icon_widget.setFixedSize(36, 36)
            icon_widget.setStyleSheet("font-size: 24px; border: none; background: transparent;")

        text_container = QWidget()
        text_container.setStyleSheet("background: transparent; border: none;")
        text_vbox = QVBoxLayout(text_container)
        text_vbox.setContentsMargins(10, 0, 0, 0)
        text_vbox.setSpacing(2)
        
        name_btn = QPushButton(name)
        name_btn.setStyleSheet("""
            QPushButton {
                text-align: left; 
                font-weight: bold; 
                font-size: 14px; 
                color: #000; 
                border: none; 
                background: transparent;
            }
            QPushButton:hover { text-decoration: underline; }
        """)
        name_btn.setCursor(Qt.PointingHandCursor)
        name_btn.clicked.connect(lambda _, p=path: self.openRequested.emit(p))
        
        subtitle = QLabel("Plik PDF")
        subtitle.setStyleSheet("color: #666; font-size: 12px; border: none; background: transparent;")
        
        text_vbox.addWidget(name_btn)
        text_vbox.addWidget(subtitle)

        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        badge = QFrame()
        badge_layout = QHBoxLayout(badge)
        badge.setFixedHeight(26)
        badge_layout.setContentsMargins(2, 0, 8, 0)
        badge_layout.setSpacing(4)

        if has_config:
            badge.setStyleSheet("""
                QFrame {
                    background-color: #D1EEDC;
                    border-radius: 13px;
                }
            """)
            
            icon_circle = QLabel()
            icon_circle.setAlignment(Qt.AlignCenter)
            icon_circle.setFixedSize(20, 20)
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            tick_path = os.path.join(current_dir, "assets", "tick.svg")
            if os.path.exists(tick_path):
                from PySide6.QtGui import QIcon
                icon_circle.setPixmap(QIcon(tick_path).pixmap(QSize(12, 12)))
            else:
                icon_circle.setText("✓")
                
            icon_circle.setStyleSheet("""
                QLabel {
                    background-color: #2CA05A;
                    color: white;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 13px;
                }
            """)
            
            text_lbl = QLabel("załączony")
            text_lbl.setStyleSheet("color: #000; font-size: 12px; border: none; background: transparent;")
            
            badge_layout.addWidget(icon_circle)
            badge_layout.addWidget(text_lbl)
            
        else:
            badge.setStyleSheet("""
                QFrame {
                    background-color: #F8D7DA; 
                    border-radius: 14px; 
                }
            """)
            
            icon_circle = QLabel()
            icon_circle.setAlignment(Qt.AlignCenter)
            icon_circle.setFixedSize(20, 20)
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            cross_path = os.path.join(current_dir, "assets", "cross.svg")
            if os.path.exists(cross_path):
                from PySide6.QtGui import QIcon
                icon_circle.setPixmap(QIcon(cross_path).pixmap(QSize(10, 10)))
            else:
                icon_circle.setText("✕")
                
            icon_circle.setStyleSheet("""
                QLabel {
                    background-color: #DC3545; 
                    color: white;
                    border-radius: 10px; 
                    font-weight: bold;
                    font-size: 13px;
                }
            """)
            
            text_lbl = QLabel("brak")
            text_lbl.setStyleSheet("color: #721C24; font-size: 14px; border: none; background: transparent;")
            
            badge_layout.addWidget(icon_circle)
            badge_layout.addWidget(text_lbl)

        status_layout.addWidget(badge)
        status_layout.addStretch()

        date_lbl = QLabel(str(date))
        date_lbl.setStyleSheet("color: #333; border: none; background: transparent; font-size: 13px;")
        
        del_btn = QPushButton("Usuń")
        del_btn.setStyleSheet("""
            QPushButton {
                color: #D32F2F; 
                font-weight: bold; 
                border: none; 
                background: transparent; 
                font-size: 13px;
            }
            QPushButton:hover { text-decoration: underline; }
        """)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(lambda checked=False, p=path: self.deleteRequested.emit(p))
        status_container.setFixedWidth(200)
        date_lbl.setFixedWidth(100)
        del_btn.setFixedWidth(50)
        row_l.addWidget(icon_widget)
        row_l.addWidget(text_container)
        
        row_l.addStretch() 
        
        row_l.addWidget(status_container)
        row_l.addWidget(date_lbl)
        row_l.addWidget(del_btn, alignment=Qt.AlignRight)
        
        self.table_layout.addWidget(row)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #C4C4C4; border: none;")
        self.table_layout.addWidget(line)