import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSvgWidgets import QSvgWidget
import styles

class StartPage(QWidget):
    fileDropped = Signal(str)
    openRequested = Signal(str)
    deleteRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
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
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)

        title = QLabel("Dokumenty")
        title.setStyleSheet(styles.HEADER_TEXT)
        main_layout.addWidget(title)

        self.upload_frame = QFrame()
        self.upload_frame.setStyleSheet(styles.UPLOAD_ZONE_STYLE)
        self.upload_frame.setFixedHeight(250)
        
        up_layout = QVBoxLayout(self.upload_frame)
        up_layout.setSpacing(10)
        
        self.pdf_icon = QLabel()
        icon_path = os.path.join("src", "assets", "pdf_file.svg")
        
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            pixmap = QIcon(icon_path).pixmap(QSize(50, 50))
            self.pdf_icon.setPixmap(pixmap)
        else:
            self.pdf_icon.setText("📄")
            
        self.pdf_icon.setFixedSize(70, 70)
        
        self.pdf_icon.setAlignment(Qt.AlignCenter)
        
        self.pdf_icon.setStyleSheet("""
            QLabel {
                background-color: #BDDCFF; /* Jasnoniebieskie tło (dopasuj odcień jeśli potrzebujesz) */
                border-radius: 35px;       /* 50px to dokładnie połowa ze 100px = idealne kółko */
                border: none;
            }
        """)
        
        txt_drag = QLabel("Przeciągnij tu plik")
        txt_drag.setStyleSheet("font-weight: bold; font-size: 14px; border: none;")
        
        self.add_btn = QPushButton("+ Dodaj plik")
        self.add_btn.setStyleSheet(styles.BLUE_BUTTON_STYLE)
        self.add_btn.setCursor(Qt.PointingHandCursor)

        up_layout.addStretch()
        up_layout.addWidget(self.pdf_icon, alignment=Qt.AlignCenter)
        up_layout.addWidget(txt_drag, alignment=Qt.AlignCenter)
        up_layout.addWidget(QLabel("albo", styleSheet="border:none; background: transparent;"), alignment=Qt.AlignCenter)
        up_layout.addWidget(self.add_btn, alignment=Qt.AlignCenter)
        up_layout.addStretch()
        
        main_layout.addWidget(self.upload_frame)

        search_section = QHBoxLayout()
        section_title = QLabel("Moje dokumenty")
        section_title.setStyleSheet(styles.SECTION_TITLE)
        
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
        main_layout.addLayout(search_section)

        self.table_container = QFrame()
        self.table_container.setStyleSheet(styles.TABLE_CONTAINER)
        self.table_layout = QVBoxLayout(self.table_container)
        self.table_layout.setContentsMargins(15, 10, 15, 10)
        self.table_layout.setSpacing(0)
        
        main_layout.addWidget(self.table_container)
        main_layout.addStretch()

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
        header_layout.setContentsMargins(30, 0, 0, 10) 
        
        h_name = QLabel("nazwa pliku"); h_name.setStyleSheet(styles.TABLE_HEADER_TEXT)
        h_config = QLabel("plik konfiguracyjny"); h_config.setStyleSheet(styles.TABLE_HEADER_TEXT)
        h_date = QLabel("data dodania"); h_date.setStyleSheet(styles.TABLE_HEADER_TEXT)
        
        header_layout.addWidget(h_name, 4)
        header_layout.addWidget(h_config, 2)
        header_layout.addWidget(h_date, 1)
        header_layout.addWidget(QLabel(""), 0)
        self.table_layout.addWidget(header_row)

        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setStyleSheet("color: #E0E0E0;")
        self.table_layout.addWidget(line)

        for p in filtered:
            self.add_row(
                p.get('nazwa_pliku', 'Nieznany'), 
                p.get('sciezka_lokalna', ''), 
                p.get('data_dodania', 'Brak daty')
            )

    def add_row(self, name, path, date):
        row = QWidget()
        row_l = QHBoxLayout(row)
        row_l.setContentsMargins(0, 5, 0, 5)
        
        name_btn = QPushButton(f"{name}")
        name_btn.setStyleSheet("text-align: left; border: none; background: transparent; color: #000;")
        name_btn.setCursor(Qt.PointingHandCursor)
        name_btn.clicked.connect(lambda _, p=path: self.openRequested.emit(p))
        
        status = QLabel("✓ załączony"); status.setStyleSheet(styles.STATUS_BADGE_STYLE)
        date_lbl = QLabel(str(date)); date_lbl.setStyleSheet("color: #333; border: none;")
        
        del_btn = QPushButton("Usuń")
        del_btn.setStyleSheet(styles.DELETE_BTN_STYLE)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(lambda _, p=path: self.deleteRequested.emit(p))

        icon_path = os.path.join("src", "assets", "pdf_file.svg")
        
        if os.path.exists(icon_path):
            icon_widget = QSvgWidget(icon_path)
            icon_widget.setFixedSize(20, 24)
            icon_widget.setStyleSheet("background: transparent;")
        else:
            icon_widget = QLabel("📄")
            icon_widget.setFixedSize(24, 24)
            icon_widget.setStyleSheet("font-size: 18px; border: none; background: transparent;")

        row_l.addWidget(icon_widget, 0)
        row_l.addWidget(name_btn, 4)
        row_l.addWidget(status, 2, alignment=Qt.AlignLeft)
        row_l.addWidget(date_lbl, 1)
        row_l.addWidget(del_btn, 0)
        
        self.table_layout.addWidget(row)
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setStyleSheet("color: #F0F0F0;")
        self.table_layout.addWidget(line)