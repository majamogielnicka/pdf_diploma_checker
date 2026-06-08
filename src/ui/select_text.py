import webbrowser
from urllib.parse import quote_plus
from PySide6.QtWidgets import QMenu, QApplication, QRubberBand, QPushButton, QToolTip, QInputDialog, QFrame
from PySide6.QtCore import Qt, QPoint, QRect, QRectF, Signal, QPointF, QSize
from PySide6.QtGui import QAction
from PySide6.QtPdfWidgets import QPdfView
import styles

class ErrorMarker(QPushButton):
    """represents an error marker on PDF"""
    def __init__(self, error_data, parent=None):
        super().__init__(parent)
        self.data = error_data
        self.setFixedSize(16, 16)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(styles.ERROR_MARKER_STYLE)
        self.setText("!")
        self.clicked.connect(self.show_details)

    def show_details(self):
        """Displays a formatted tooltip with details about the error"""
        opis = self.data.get('comment', 'Brak szczegółowego opisu błędu')
        kat = self.data.get('category', 'Błąd')
        tekst = self.data.get('found_text', '')

        info = (f"<b>Kategoria:</b> {kat}<br>"
                f"<b>Opis:</b> {opis}<br>")
        
        if tekst and tekst != "[Brak tekstu]":
            info += f"<b>Dotyczy tekstu:</b> <i>{tekst}</i>"

        QToolTip.showText(self.mapToGlobal(QPoint(20, 0)), info)

class CommentMarker(QPushButton):
    """represents a custom comment marker added by the user"""
    def __init__(self, comment_data, parent=None):
        super().__init__(parent)
        self.data = comment_data
        self.setFixedSize(16, 16)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(styles.COMMENT_MARKER_STYLE)
        self.setText("C")
        self.clicked.connect(self.show_details)

    def show_details(self):
        """displays the user's comment text"""
        info = (f"<b>Twój komentarz:</b> {self.data.get('tekst_komentarza', '')}<br>"
                f"<b>Fragment:</b> {self.data.get('znaleziony_tekst', '')}")
        QToolTip.showText(self.mapToGlobal(QPoint(20, 0)), info)

class HighlightBox(QFrame):
    """A transparent frame overlay used to visually highlight a specific text on PDF"""
    def __init__(self, rect_data, parent=None):
        super().__init__(parent)
        self.data = rect_data
        self.setStyleSheet(styles.HIGHLIGHT_BOX_DEFAULT)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

class SelectablePdfView(QPdfView):
    """An extended PDF view that enables area-based text selection (via Shift key), adding custom user comments, and overlaying error markers and highlight boxes."""
    textCopied = Signal(str)
    commentAdded = Signal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.markers = []
        self.comment_markers = []
        self.highlight_boxes = []
        self.selection_box = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.selection_pdf_rect = None 
        self.selection_page_idx = -1
        self.selected_text = ""
        
        self.verticalScrollBar().valueChanged.connect(self.update_selection_box_pos)
        self.horizontalScrollBar().valueChanged.connect(self.update_selection_box_pos)
        self.verticalScrollBar().valueChanged.connect(self.update_markers_pos)
        self.horizontalScrollBar().valueChanged.connect(self.update_markers_pos)

    def clear_markers(self):
        """Removes all error marker"""
        for m in self.markers:
            m.deleteLater()
        self.markers = []


    def add_errors(self, errors_list):
        """Clears existing errors and overlays a new list of error markers and highlight boxes"""
        self.clear_markers()
        
        new_boxes = []
        for box in self.highlight_boxes:
            if getattr(box, 'is_error', False):
                box.deleteLater()
            else:
                new_boxes.append(box)
        self.highlight_boxes = new_boxes

        for err in errors_list:
            marker = ErrorMarker(err, self.viewport())
            self.markers.append(marker)
            coords = err.get("coords", err.get("wspolrzedne", {}))
            w = coords.get("w", 0)
            
            if w > 0:
                box = HighlightBox(err, self.viewport())
                box.is_error = True
                box.setStyleSheet(styles.HIGHLIGHT_BOX_ERROR)
                self.highlight_boxes.append(box)

        self.update_markers_pos()

    def update_markers_pos(self):
        """Recalculates and updates the pixel positions of all markers and highlight boxes 
        relative to the PDF document coordinates, factoring in the current zoom level, 
        scrollbar values, and page margins."""
        doc = self.document()
        if not doc or doc.pageCount() == 0: return

        dpi_x, dpi_y = self.logicalDpiX(), self.logicalDpiY()
        zoom = self.zoomFactor()
        
        scroll_x = self.horizontalScrollBar().value()
        scroll_y = self.verticalScrollBar().value()
        viewport_w = self.viewport().width()

        all_markers = self.markers + self.comment_markers

        for marker in all_markers:
            data = marker.data
            page_idx = data.get("page", data.get("strona", 1))
            coords = data.get("coords", data.get("wspolrzedne", {"x": 0, "y": 0, "w": 0, "h": 0}))
            
            if page_idx < 0 or page_idx >= doc.pageCount():
                continue

            target_page_y_px = self.documentMargins().top()
            for i in range(page_idx):
                size_pt = doc.pagePointSize(i)
                page_h_px = int((size_pt.height() * zoom * (dpi_y / 72.0)) + 0.5)
                target_page_y_px += page_h_px + self.pageSpacing()

            size_pt = doc.pagePointSize(page_idx)
            page_w_px = int((size_pt.width() * zoom * (dpi_x / 72.0)) + 0.5)
            
            if self.horizontalScrollBar().maximum() > 0:
                x_start_px = self.documentMargins().left()
            else:
                x_start_px = (viewport_w - page_w_px) // 2

            local_x_px = int((coords.get("x", 0) * zoom * (dpi_x / 72.0)) + 0.5)
            local_y_px = int((coords.get("y", 0) * zoom * (dpi_y / 72.0)) + 0.5)
            px_w = int((coords.get("w", 0) * zoom * (dpi_x / 72.0)) + 0.5)

            px_x = x_start_px + local_x_px - scroll_x
            px_y = target_page_y_px + local_y_px - scroll_y
            
            if px_w > 0:
                marker_x = px_x + (px_w // 2) - 8 
            else:
                marker_x = px_x - 8
                
            marker_y = px_y - 12
            
            marker.move(int(marker_x), int(marker_y))
            marker.show()
        for box in self.highlight_boxes:
            data = box.data
            page_idx = data.get("page", data.get("strona", 1))
            coords = data.get("coords", data.get("wspolrzedne", {"x": 0, "y": 0, "w": 0, "h": 0}))
            
            if page_idx < 0 or page_idx >= doc.pageCount():
                continue
                
            target_page_y_px = self.documentMargins().top()
            for i in range(page_idx):
                size_pt = doc.pagePointSize(i)
                page_h_px = int((size_pt.height() * zoom * (dpi_y / 72.0)) + 0.5)
                target_page_y_px += page_h_px + self.pageSpacing()

            size_pt = doc.pagePointSize(page_idx)
            page_w_px = int((size_pt.width() * zoom * (dpi_x / 72.0)) + 0.5)
            
            if self.horizontalScrollBar().maximum() > 0:
                x_start_px = self.documentMargins().left()
            else:
                x_start_px = (viewport_w - page_w_px) // 2

            local_x_px = coords.get("x", 0) * zoom * (dpi_x / 72.0)
            local_y_px = coords.get("y", 0) * zoom * (dpi_y / 72.0)
            px_w = coords.get("w", 0) * zoom * (dpi_x / 72.0)
            px_h = coords.get("h", 0) * zoom * (dpi_y / 72.0)

            px_x = x_start_px + local_x_px - scroll_x
            px_y = target_page_y_px + local_y_px - scroll_y

            if px_w > 0 and px_h > 0:
                box.setGeometry(int(px_x), int(px_y), int(px_w), int(px_h))
                box.show()
                
        for marker in all_markers:
            marker.raise_()

    def clear_comments(self):
        """Removes all comments"""
        for m in self.comment_markers:
            m.deleteLater()
        self.comment_markers = []

        new_boxes = []
        for b in self.highlight_boxes:
            if not getattr(b, 'is_error', False):
                b.deleteLater()
            else:
                new_boxes.append(b)
        self.highlight_boxes = new_boxes


    def resizeEvent(self, event):
        """Handles the widget resize event by triggering a recalculation"""
        super().resizeEvent(event)
        self.update_selection_box_pos()
        self.update_markers_pos()

    def update_selection_box_pos(self):
        """Updates the screen geometry of box selection"""
        if not self.origin.isNull() or self.selection_page_idx == -1 or not self.selection_pdf_rect:
            return
        
        doc = self.document()
        if not doc or doc.pageCount() <= self.selection_page_idx: return

        dpi_x, dpi_y = self.logicalDpiX(), self.logicalDpiY()
        zoom = self.zoomFactor()

        target_page_y_px = self.documentMargins().top()
        for i in range(self.selection_page_idx):
            size_pt = doc.pagePointSize(i)
            target_page_y_px += (size_pt.height() * zoom * (dpi_y / 72.0)) + self.pageSpacing()

        size_pt = doc.pagePointSize(self.selection_page_idx)
        page_w_px = size_pt.width() * zoom * (dpi_x / 72.0)
        viewport_w = self.viewport().width()
        
        if self.horizontalScrollBar().maximum() > 0:
            x_start_px = self.documentMargins().left()
        else:
            x_start_px = (viewport_w - page_w_px) / 2

        rect_pt = self.selection_pdf_rect
        px_x = x_start_px + (rect_pt.x() * zoom * (dpi_x / 72.0)) - self.horizontalScrollBar().value()
        px_y = target_page_y_px + (rect_pt.y() * zoom * (dpi_y / 72.0)) - self.verticalScrollBar().value()
        px_w = rect_pt.width() * zoom * (dpi_x / 72.0)
        px_h = rect_pt.height() * zoom * (dpi_y / 72.0)

        self.selection_box.setGeometry(int(px_x), int(px_y), int(px_w), int(px_h))
        self.selection_box.show()

    def mousePressEvent(self, event):
        """Handles mouse press events. Right-clicking inside an active selection triggers 
        the context menu. Left-clicking while holding the Shift key initializes a new 
        bounding box selection."""
        if event.button() == Qt.RightButton:
            if self.selection_box.isVisible() and self.selection_box.geometry().contains(event.position().toPoint()):
                self.show_context_menu(event.globalPosition().toPoint())
            return

        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier:
            self.origin = event.position().toPoint()
            self.selection_box.setGeometry(QRect(self.origin, QSize(0,0)))
            self.selection_box.show()
            self.selected_text = ""
            self.selection_pdf_rect = None
            self.selection_page_idx = -1
            event.accept()
            return
            
        if event.button() == Qt.LeftButton:
            self.selection_box.hide()
            self.selected_text = ""
            self.selection_pdf_rect = None
            self.selection_page_idx = -1

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handles mouse move events"""
        if not self.origin.isNull() and event.modifiers() == Qt.ShiftModifier:
            self.selection_box.setGeometry(QRect(self.origin, event.position().toPoint()).normalized())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handles mouse release events. Finalizes the selection box area bounding 
        coordinates and initiates the text extraction process."""
        if not self.origin.isNull():
            rect = self.selection_box.geometry()
            self.origin = QPoint()
            self.extract_text(rect)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def extract_text(self, rect):
        """Extracts text from a specified pixel coordinate bounding box on the screen.
        Scans the selected area line-by-line"""
        doc = self.document()
        if not doc or doc.pageCount() == 0: return
        
        v_val = self.verticalScrollBar().value()
        h_val = self.horizontalScrollBar().value()
        dpi_x, dpi_y = self.logicalDpiX(), self.logicalDpiY()

        current_y_px = self.documentMargins().top()
        
        current_y_px = self.documentMargins().top()
        
        for i in range(doc.pageCount()):
            size_pt = doc.pagePointSize(i)
            page_w_px = int((size_pt.width() * self.zoomFactor() * (dpi_x / 72.0)) + 0.5)
            page_h_px = int((size_pt.height() * self.zoomFactor() * (dpi_y / 72.0)) + 0.5)
            
            center_y_px = rect.center().y() + v_val
            
            if current_y_px <= center_y_px <= current_y_px + page_h_px:
                viewport_w = self.viewport().width()
                x_start_px = self.documentMargins().left() if self.horizontalScrollBar().maximum() > 0 else (viewport_w - page_w_px) / 2
                
                px1 = rect.left() + h_val - x_start_px
                py1 = rect.top() + v_val - current_y_px
                px2 = rect.right() + h_val - x_start_px
                py2 = rect.bottom() + v_val - current_y_px
                
                pt_x1 = (px1 / self.zoomFactor()) * (72.0 / dpi_x)
                pt_y1 = (py1 / self.zoomFactor()) * (72.0 / dpi_y)
                pt_x2 = (px2 / self.zoomFactor()) * (72.0 / dpi_x)
                pt_y2 = (py2 / self.zoomFactor()) * (72.0 / dpi_y)
                
                start_x, end_x = min(pt_x1, pt_x2), max(pt_x1, pt_x2)
                start_y, end_y = min(pt_y1, pt_y2), max(pt_y1, pt_y2)

                self.selection_page_idx = i
                self.selection_pdf_rect = QRectF(start_x, start_y, end_x - start_x, end_y - start_y)
                
                collected_lines = []
                current_scan_y = start_y
                while current_scan_y <= end_y:
                    pt_start = QPointF(max(0, start_x), current_scan_y)
                    pt_end = QPointF(min(size_pt.width(), end_x), current_scan_y)
                    selection = doc.getSelection(i, pt_start, pt_end)
                    
                    if selection and selection.text():
                        chunk = selection.text().strip()
                        if chunk and (not collected_lines or collected_lines[-1] != chunk):
                            collected_lines.append(chunk)
                    current_scan_y += 4.0 
                
                self.selected_text = " ".join(collected_lines)
                self.update_selection_box_pos()
                break
            current_y_px += page_h_px + self.pageSpacing()

    def show_context_menu(self, global_pos):
        """Displays a pop-up context menu offering options to copy text, check for 
        plagiarism, or add a custom comment."""
        menu = QMenu(self)
        copy_action = QAction("Skopiuj tekst", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        
        plagiat_action = QAction("Sprawdź plagiat", self)
        plagiat_action.triggered.connect(self.check_plagiarism) 
        
        comment_action = QAction("Dodaj komentarz", self)
        comment_action.triggered.connect(self.add_custom_comment)
        comment_action.setEnabled(bool(self.selected_text)) 

        menu.addAction(copy_action)
        menu.addAction(plagiat_action)
        menu.addAction(comment_action)
        menu.exec(global_pos)

    def add_custom_comment(self):
        """Opens an input dialog prompting the user for comment text linked to the current selection."""
        if not self.selection_pdf_rect or self.selection_page_idx == -1:
            return
            
        text, ok = QInputDialog.getText(self, "Dodaj komentarz", "Wpisz treść komentarza:")
        if ok and text:
            comment_data = {
                "strona": self.selection_page_idx + 1, 
                "wspolrzedne": {
                    "x": self.selection_pdf_rect.x(), 
                    "y": self.selection_pdf_rect.y(),
                    "w": self.selection_pdf_rect.width(),
                    "h": self.selection_pdf_rect.height() 
                },
                "tekst_komentarza": text,
                "znaleziony_tekst": self.selected_text
            }
            
            box = HighlightBox(comment_data, self.viewport())
            box.is_error = False
            box.setStyleSheet(styles.HIGHLIGHT_BOX_COMMENT)
            self.highlight_boxes.append(box)

            marker = CommentMarker(comment_data, self.viewport())
            self.comment_markers.append(marker)
            
            self.update_markers_pos()
            self.selection_box.hide()
            self.commentAdded.emit(comment_data)

    def copy_to_clipboard(self):
        """Copies the currently selected text fragment to the system clipboard."""
        QApplication.clipboard().setText(self.selected_text)

    def check_plagiarism(self):
        """Opens the system's default web browser to perform a Google Search of the 
        selected text fragment wrapped as an exact phrase query (in quotes). 
        Truncates the query to a maximum of 300 characters.
        """
        if not self.selected_text:
            return
            
        clean_text = " ".join(self.selected_text.split())
        
        if len(clean_text) > 300:
            clean_text = clean_text[:300]
            print("Ostrzeżenie: Przekroczono limit 300 znaków. Tekst został przycięty.")

        encoded_phrase = quote_plus(f'"{clean_text}"')
        webbrowser.open(f"https://www.google.com/search?q={encoded_phrase}")