from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QScrollArea, QLabel, QPushButton, QSplitter, QLineEdit
)
from PySide6.QtCore import Qt, QSize, QPointF, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from select_text import SelectablePdfView
import styles

class PDFReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Czytnik PDF")
        self.resize(1200, 800)
        
        self.document = QPdfDocument(self)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        #gorny pasek
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)

        #ustawienie poziome
        splitter = QSplitter(Qt.Horizontal)

        #miniaturki
        self.thumb_area = QScrollArea()
        self.thumb_area.setFixedWidth(150)
        self.thumb_area.setWidgetResizable(True)
        self.thumb_widget = QWidget()
        self.thumb_layout = QVBoxLayout(self.thumb_widget)
        self.thumb_layout.setAlignment(Qt.AlignTop)
        self.thumb_area.setWidget(self.thumb_widget)

        #widok calego pdf
        self.pdf_view = SelectablePdfView()
        self.pdf_view.setDocument(self.document)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setStyleSheet(styles.PDF_VIEW_STYLE)
        
        #zmiana nr strony przy przewijaniu
        self.pdf_view.pageNavigator().currentPageChanged.connect(self.update_page_input)

        #prawy panel
        self.right_panel = QWidget()
        self.right_panel.setFixedWidth(280)
        self.right_panel.setStyleSheet(styles.RIGHT_PANEL_STYLE)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(15, 20, 15, 20)
        
        verify_label = QLabel("Weryfikacja")
        verify_label.setStyleSheet(styles.VERIFY_TITLE_STYLE)
        right_layout.addWidget(verify_label)
        right_layout.addStretch()

        #dodanie wszystkiego do poziomego widoku
        splitter.addWidget(self.thumb_area)
        splitter.addWidget(self.pdf_view)
        splitter.addWidget(self.right_panel)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def _create_toolbar(self):
        #wyglad paska
        toolbar = QWidget()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet(styles.TOOLBAR_STYLE)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 0, 20, 0)
        toolbar_layout.setSpacing(0)

        #tytul
        self.title_label = QLabel("Nazwa_dokumentu")
        self.title_label.setStyleSheet(styles.NORMAL_LABEL_STYLE)
        toolbar_layout.addWidget(self.title_label)

        toolbar_layout.addStretch(1)

        #zoom and page number kontener
        self.nav_zoom_page_nr = QWidget() 
        nav_layout = QHBoxLayout(self.nav_zoom_page_nr)
        nav_layout.setSpacing(8) 
        nav_layout.setContentsMargins(0, 0, 0, 0)
        
        #wnumery stron
        self.page_input = QLineEdit("1")
        self.page_input.setFixedWidth(40)
        self.page_input.setAlignment(Qt.AlignCenter)
        self.total_pages_label = QLabel(" / 0 ")

        #separator
        separator = QLabel(" | ")
        separator.setStyleSheet(styles.SEPARATOR_STYLE)

        #zoom
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedSize(30, 30)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setFixedWidth(50)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(30, 30)

        #guziki
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.page_input.returnPressed.connect(self.jump_to_page)
        #ustawienie wszystkiego
        nav_layout.addWidget(self.page_input)
        nav_layout.addWidget(self.total_pages_label)
        nav_layout.addWidget(separator)
        nav_layout.addWidget(self.zoom_out_btn)
        nav_layout.addWidget(self.zoom_label)
        nav_layout.addWidget(self.zoom_in_btn)
        toolbar_layout.addWidget(self.nav_zoom_page_nr)
        toolbar_layout.addStretch(1)

        #jezyk
        lang_btn = QLabel("PL | EN")
        lang_btn.setStyleSheet(styles.LANG_BTN_STYLE)
        lang_btn.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        toolbar_layout.addWidget(lang_btn)
        
        return toolbar

    def load_pdf(self, path):
        self.document.load(path)
        #sprawdzanie czy dokment jest
        if self.document.pageCount() > 0:
            self.total_pages_label.setText(f" / {self.document.pageCount()} ")
            self.generate_thumbnails()
            self.pdf_view.setZoomFactor(1.0)
            self.update_zoom_label()

    def generate_thumbnails(self):
        #czyszczenie
        for i in reversed(range(self.thumb_layout.count())): 
            widget = self.thumb_layout.itemAt(i).widget()
            if widget: widget.setParent(None)

        #budowanie miniaturek
        for i in range(self.document.pageCount()):
            page_img = self.document.render(i, QSize(100, 140))
            btn = QPushButton()
            btn.setIcon(QPixmap.fromImage(page_img))
            btn.setIconSize(QSize(100, 140))
            btn.setFixedSize(110, 150)
            
            #skakanie do strony
            btn.clicked.connect(lambda checked, idx=i: self.pdf_view.pageNavigator().jump(idx, QPointF(0,0), self.pdf_view.zoomFactor()))
            self.thumb_layout.addWidget(btn)
            self.thumb_layout.addWidget(QLabel(f"{i+1}", alignment=Qt.AlignCenter))

    def zoom_in(self):
        self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() * 1.2)
        self.update_zoom_label()

    def zoom_out(self):
        self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() / 1.2)
        self.update_zoom_label()

    def update_zoom_label(self):
        self.zoom_label.setText(f"{int(self.pdf_view.zoomFactor() * 100)}%")

    def update_page_input(self, page_index):
        self.page_input.setText(str(page_index + 1))

    def jump_to_page(self):
        try:
            page_num = int(self.page_input.text()) - 1
            if 0 <= page_num < self.document.pageCount():
                self.pdf_view.pageNavigator().jump(page_num, QPointF(0, 0), self.pdf_view.zoomFactor())
            else:
                self.update_page_input(self.pdf_view.pageNavigator().currentPage())
        except ValueError:
            self.update_page_input(self.pdf_view.pageNavigator().currentPage())
