from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit, QCheckBox
)
from PySide6.QtCore import Qt, Signal
import styles

class StartPage(QWidget):
    fileDropped = Signal(str)
    openRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet(styles.START_PAGE_BG)
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
        self.upload_frame.setFixedHeight(200)
        self.upload_frame.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        up_layout = QVBoxLayout(self.upload_frame)
        up_layout.setSpacing(5)
        
        pdf_icon = QLabel("📄")
        pdf_icon.setStyleSheet("font-size: 40px; color: #478CD1; border: none;")
        
        txt_drag = QLabel("Przeciągnij tu plik")
        txt_drag.setStyleSheet("font-weight: bold; font-size: 14px; border: none;")
        
        self.add_btn = QPushButton("+ Dodaj plik")
        self.add_btn.setStyleSheet(styles.BLUE_BUTTON_STYLE)
        self.add_btn.setCursor(Qt.PointingHandCursor) # Poprawne ustawienie kursora
        self.add_btn.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        up_layout.addWidget(pdf_icon, alignment=Qt.AlignCenter)
        up_layout.addWidget(txt_drag, alignment=Qt.AlignCenter)
        up_layout.addWidget(QLabel("albo", styleSheet="border:none;"), alignment=Qt.AlignCenter)
        up_layout.addWidget(self.add_btn, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.upload_frame)

        search_section = QHBoxLayout()
        section_title = QLabel("Moje dokumenty")
        section_title.setStyleSheet(styles.SECTION_TITLE)
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("Szukaj")
        search_input.setStyleSheet(styles.SEARCH_STYLE)
        search_input.setFixedWidth(300)
        
        sort_btn = QPushButton("⇅ Sortuj od: najnowszego")
        sort_btn.setStyleSheet(styles.SORT_BTN_STYLE)
        sort_btn.setCursor(Qt.PointingHandCursor)

        search_section.addWidget(section_title)
        search_section.addStretch()
        search_section.addWidget(search_input)
        search_section.addWidget(sort_btn)
        main_layout.addLayout(search_section)

        self.table_container = QFrame()
        self.table_container.setStyleSheet(styles.TABLE_CONTAINER)
        self.table_layout = QVBoxLayout(self.table_container)
        self.table_layout.setContentsMargins(15, 10, 15, 10)
        self.table_layout.setSpacing(0)
        
        main_layout.addWidget(self.table_container)
        main_layout.addStretch()

    def render_doc_list(self, pliki):
        """Czyści listę i renderuje ją na nowo na podstawie danych z JSON."""
        while self.table_layout.count():
            child = self.table_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        header_row = QWidget()
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(45, 0, 0, 10)
        
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

        for p in pliki:
            self.add_row(p['nazwa_pliku'], p['sciezka_lokalna'], p['data_dodania'])

    def add_row(self, name, path, date):
        row = QWidget()
        row_l = QHBoxLayout(row)
        row_l.setContentsMargins(0, 5, 0, 5)
        
        chk = QCheckBox(); chk.setStyleSheet(styles.CHECKBOX_STYLE)
        
        # Nazwa pliku jako przycisk, żeby można było w niego kliknąć i otworzyć
        name_btn = QPushButton(f"{name}")
        name_btn.setStyleSheet("text-align: left; border: none; background: transparent; color: #000;")
        name_btn.setCursor(Qt.PointingHandCursor)
        name_btn.clicked.connect(lambda: self.openRequested.emit(path))
        
        status = QLabel("✓ załączony"); status.setStyleSheet(styles.STATUS_BADGE_STYLE)
        date_lbl = QLabel(date); date_lbl.setStyleSheet("color: #333; border: none;")
        
        del_btn = QPushButton("Usuń")
        del_btn.setStyleSheet(styles.DELETE_BTN_STYLE)
        del_btn.setCursor(Qt.PointingHandCursor)

        row_l.addWidget(chk, 0)
        row_l.addWidget(QLabel("📄", styleSheet="font-size: 18px; border:none;"), 0)
        row_l.addWidget(name_btn, 4)
        row_l.addWidget(status, 2, alignment=Qt.AlignLeft)
        row_l.addWidget(date_lbl, 1)
        row_l.addWidget(del_btn, 0)
        
        self.table_layout.addWidget(row)
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setStyleSheet("color: #F0F0F0;")
        self.table_layout.addWidget(line)