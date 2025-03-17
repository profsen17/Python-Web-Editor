import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QTreeWidget, 
                            QTreeWidgetItem, QSplitter, QWidget, QVBoxLayout, 
                            QAction, QMenu, QHBoxLayout, QFileDialog, QMessageBox,
                            QToolBar, QPushButton, QLabel, QInputDialog, QLineEdit,
                            QTabWidget, QGridLayout, QScrollArea, QDialog, QComboBox, QFormLayout, QStackedWidget)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QMimeData, QPoint, QSize
from PyQt5.QtGui import QIcon, QTextDocument, QColor, QDrag, QPainter, QPen, QBrush
from fuzzywuzzy import fuzz

from PyQt5.QtWidgets import QTextEdit, QCompleter
from PyQt5.QtGui import QPainter, QTextFormat, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtCore import QRect, QStringListModel

class CodeEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.line_number_area = LineNumberArea(self)

        self.completer = None
        self.setup_completer()
        self.setup_auto_indent()

        # Connect signals for updating line numbers
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)

    def setup_completer(self):
        # Define completion lists for HTML, CSS, and JS
        html_tags = ["div", "span", "p", "h1", "h2", "h3", "img", "a", "ul", "li", "table", "tr", "td", "input", "form", "body", "head", "html"]
        css_properties = ["color", "background", "font-size", "margin", "padding", "border", "display", "flex", "grid", "position", "top", "left", "width", "height"]
        js_functions = ["function", "var", "let", "const", "if", "else", "for", "while", "return", "console.log", "document", "getElementById", "addEventListener"]

        # Combine all completions (we'll filter based on file type later)
        completions = html_tags + css_properties + js_functions
        self.completer = QCompleter(completions, self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)

    def setup_auto_indent(self):
        self.textChanged.connect(self.handle_auto_indent)

    def line_number_area_width(self):
        digits = 1
        max_blocks = max(1, self.blockCount())
        while max_blocks >= 10:
            max_blocks /= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.line_number_area.width() - 3, self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def keyPressEvent(self, event):
        if self.completer and self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return
        super().keyPressEvent(event)

        # Auto-indent logic for specific keys
        cursor = self.textCursor()
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            block = cursor.block()
            text = block.text()
            indent = len(text) - len(text.lstrip())
            cursor.insertText('\n' + ' ' * indent)
            self.setTextCursor(cursor)
            return

        # Formatting with Ctrl+Shift+F
        if event.key() == Qt.Key_F and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self.format_code()
            return

        # Autocompletion logic
        if event.text() and event.text().isalnum():
            self.show_completions()

    def handle_auto_indent(self):
        cursor = self.textCursor()
        block = cursor.block()
        text = block.text()
        if text.rstrip().endswith(('{', '<')):
            cursor.movePosition(cursor.EndOfBlock)
            indent = len(text) - len(text.lstrip())
            cursor.insertText('\n' + ' ' * (indent + 2) + '\n' + ' ' * indent)
            cursor.movePosition(cursor.Up)
            cursor.movePosition(cursor.EndOfBlock)
            self.setTextCursor(cursor)

    def format_code(self):
        # Basic formatting: re-indent based on braces
        cursor = self.textCursor()
        cursor.select(cursor.Document)
        text = cursor.selectedText()
        lines = text.split('\n')
        indent_level = 0
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line.endswith('}') or line.endswith('>'):
                indent_level = max(0, indent_level - 2)
            formatted_line = ' ' * indent_level + line
            if line.endswith('{') or line.endswith('<'):
                indent_level += 2
            formatted_lines.append(formatted_line)
        cursor.insertText('\n'.join(formatted_lines))
        self.setTextCursor(cursor)

    def show_completions(self):
        cursor = self.textCursor()
        cursor.select(cursor.WordUnderCursor)
        prefix = cursor.selectedText()

        if len(prefix) < 1:
            self.completer.popup().hide()
            return

        # Filter completions based on file type (if available)
        file_path = self.parent().current_file if hasattr(self.parent(), 'current_file') else ''
        completions = []
        if file_path.endswith('.html'):
            completions = ["div", "span", "p", "h1", "h2", "h3", "img", "a", "ul", "li", "table", "tr", "td", "input", "form", "body", "head", "html"]
        elif file_path.endswith('.css'):
            completions = ["color", "background", "font-size", "margin", "padding", "border", "display", "flex", "grid", "position", "top", "left", "width", "height"]
        elif file_path.endswith('.js'):
            completions = ["function", "var", "let", "const", "if", "else", "for", "while", "return", "console.log", "document", "getElementById", "addEventListener"]

        self.completer.setModel(QStringListModel(completions))
        self.completer.setCompletionPrefix(prefix)
        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)

    def insert_completion(self, completion):
        cursor = self.textCursor()
        cursor.select(cursor.WordUnderCursor)
        cursor.insertText(completion)
        self.setTextCursor(cursor)

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)
        
class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # HTML rules
        html_tag_format = QTextCharFormat()
        html_tag_format.setForeground(Qt.darkBlue)
        html_tag_format.setFontWeight(QFont.Bold)
        html_tags = ["div", "span", "p", "h1", "h2", "h3", "img", "a", "ul", "li", "table", "tr", "td", "input", "form", "body", "head", "html"]
        for tag in html_tags:
            pattern = f"\\b{tag}\\b"
            self.highlighting_rules.append((QRegExp(pattern), html_tag_format))

        # CSS rules
        css_property_format = QTextCharFormat()
        css_property_format.setForeground(Qt.darkGreen)
        css_properties = ["color", "background", "font-size", "margin", "padding", "border", "display", "flex", "grid", "position", "top", "left", "width", "height"]
        for prop in css_properties:
            pattern = f"\\b{prop}\\b"
            self.highlighting_rules.append((QRegExp(pattern), css_property_format))

        # JS rules
        js_keyword_format = QTextCharFormat()
        js_keyword_format.setForeground(Qt.darkRed)
        js_keywords = ["function", "var", "let", "const", "if", "else", "for", "while", "return"]
        for keyword in js_keywords:
            pattern = f"\\b{keyword}\\b"
            self.highlighting_rules.append((QRegExp(pattern), js_keyword_format))

        # Comment rules
        comment_format = QTextCharFormat()
        comment_format.setForeground(Qt.gray)
        self.highlighting_rules.append((QRegExp("//[^\n]*"), comment_format))
        self.highlighting_rules.append((QRegExp("/\\*[^\\*/]*\\*/"), comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        # Apply file-specific highlighting based on current file
        file_path = self.document().parent().parent().current_file if hasattr(self.document().parent().parent(), 'current_file') else ''
        if file_path.endswith('.html'):
            self.apply_html_highlighting(text)
        elif file_path.endswith('.css'):
            self.apply_css_highlighting(text)
        elif file_path.endswith('.js'):
            self.apply_js_highlighting(text)

    def apply_html_highlighting(self, text):
        tag_format = QTextCharFormat()
        tag_format.setForeground(Qt.darkBlue)
        expression = QRegExp("<[^>]+>")
        index = expression.indexIn(text)
        while index >= 0:
            length = expression.matchedLength()
            self.setFormat(index, length, tag_format)
            index = expression.indexIn(text, index + length)

    def apply_css_highlighting(self, text):
        selector_format = QTextCharFormat()
        selector_format.setForeground(Qt.darkMagenta)
        expression = QRegExp("[a-zA-Z][a-zA-Z0-9-]*\\s*\\{")
        index = expression.indexIn(text)
        while index >= 0:
            length = expression.matchedLength() - 1  # Exclude the '{'
            self.setFormat(index, length, selector_format)
            index = expression.indexIn(text, index + length)

    def apply_js_highlighting(self, text):
        string_format = QTextCharFormat()
        string_format.setForeground(Qt.darkCyan)
        expression = QRegExp("\"[^\"]*\"|'[^']*'")
        index = expression.indexIn(text)
        while index >= 0:
            length = expression.matchedLength()
            self.setFormat(index, length, string_format)
            index = expression.indexIn(text, index + length)
