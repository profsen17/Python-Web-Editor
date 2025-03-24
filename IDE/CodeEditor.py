import json
import os
import re
from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QShortcut, QCompleter
from PyQt5.QtCore import Qt, QSize, QRect, QTimer, QStringListModel
from PyQt5.QtGui import (QPainter, QPen, QColor, QFont, QTextCharFormat, 
                        QTextCursor, QKeySequence, QSyntaxHighlighter)

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, file_path=None, editor=None):
        super().__init__(document)
        self.file_path = file_path
        self.editor = editor
        self.highlighting_rules = []
        self.load_highlighting_rules()

    def load_highlighting_rules(self):
        """Load syntax highlighting rules from JSON files based on file extension."""
        self.highlighting_rules.clear()
        if not self.file_path or not self.editor or not self.editor.parent_editor:
            return

        is_dark_mode = self.editor.parent_editor.is_dark_mode
        language = self.determine_language()
        json_path = os.path.join("IDE", "languages", f"{language}.json")

        if not os.path.exists(json_path):
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                rules = json.load(f)
        except Exception as e:
            print(f"Error loading {json_path}: {e}")
            return

        # Define color schemes
        colors = {
            "tag": "#E06C75" if not is_dark_mode else "#E06C75",  # Red for tags/properties/objects
            "attribute": "#D19A66" if not is_dark_mode else "#D19A66",  # Orange for attributes/methods
            "value": "#98C379" if not is_dark_mode else "#98C379",  # Green for values/strings
            "comment": "#6A9955" if not is_dark_mode else "#6A9955",  # Green for comments
            "keyword": "#C678DD" if not is_dark_mode else "#C678DD",  # Purple for keywords
        }

        if language == "html":
            # HTML tags
            tags = list(rules["tags"].keys())
            tag_pattern = r"<\s*(" + "|".join(map(re.escape, tags)) + r")(?:\s+[^>]*)?>|<\s*/\s*(" + "|".join(map(re.escape, tags)) + r")\s*>"
            tag_format = self.create_format({"foreground": colors["tag"], "fontWeight": "bold"})
            self.highlighting_rules.append((tag_pattern, tag_format))

            # HTML attributes
            all_attributes = rules["global_attributes"]
            for tag_data in rules["tags"].values():
                for attr in tag_data["attributes"]:
                    all_attributes.append(attr["name"])
            attr_pattern = r"\b(" + "|".join(map(re.escape, all_attributes)) + r")\s*="
            attr_format = self.create_format({"foreground": colors["attribute"]})
            self.highlighting_rules.append((attr_pattern, attr_format))

            # Strings (attribute values)
            string_pattern = r'"[^"\\]*(\\.[^"\\]*)*"|\'[^\']*\''
            string_format = self.create_format({"foreground": colors["value"]})
            self.highlighting_rules.append((string_pattern, string_format))

            # Comments
            comment_pattern = r"<!--[\s\S]*?-->"
            comment_format = self.create_format({"foreground": colors["comment"]})
            self.highlighting_rules.append((comment_pattern, comment_format))

        elif language == "css":
            # CSS properties
            properties = list(rules["properties"].keys())
            prop_pattern = r"\b(" + "|".join(map(re.escape, properties)) + r")\s*:"
            prop_format = self.create_format({"foreground": colors["tag"]})
            self.highlighting_rules.append((prop_pattern, prop_format))

            # CSS values (simplified for common values)
            value_pattern = r":\s*([#\w\d]+|[\d\.]+(?:px|em|rem|%)|\b(" + "|".join(["inherit", "initial", "unset"]) + r")\b)"
            value_format = self.create_format({"foreground": colors["value"]})
            self.highlighting_rules.append((value_pattern, value_format))

            # Comments
            comment_pattern = r"/\*[\s\S]*?\*/"
            comment_format = self.create_format({"foreground": colors["comment"]})
            self.highlighting_rules.append((comment_pattern, comment_format))

        elif language == "js":
            # JavaScript objects and methods
            objects = list(rules["objects"].keys())
            keywords = ["function", "var", "let", "const", "if", "else", "for", "while", "return"]
            keyword_pattern = r"\b(" + "|".join(map(re.escape, keywords + objects)) + r")\b"
            keyword_format = self.create_format({"foreground": colors["keyword"]})
            self.highlighting_rules.append((keyword_pattern, keyword_format))

            # Methods and properties
            all_methods = []
            for obj in rules["objects"].values():
                all_methods.extend([m["name"] for m in obj.get("methods", [])])
            method_pattern = r"\b(" + "|".join(map(re.escape, all_methods)) + r")\s*\("
            method_format = self.create_format({"foreground": colors["attribute"]})
            self.highlighting_rules.append((method_pattern, method_format))

            # Strings
            string_pattern = r'"[^"\\]*(\\.[^"\\]*)*"|\'[^\']*\''
            string_format = self.create_format({"foreground": colors["value"]})
            self.highlighting_rules.append((string_pattern, string_format))

            # Comments
            comment_pattern = r"//.*$|/\*[\s\S]*?\*/"
            comment_format = self.create_format({"foreground": colors["comment"]})
            self.highlighting_rules.append((comment_pattern, comment_format))

    def determine_language(self):
        """Determine the language based on file extension."""
        if not self.file_path:
            return "txt"
        if self.file_path.endswith('.html'):
            return "html"
        elif self.file_path.endswith('.css'):
            return "css"
        elif self.file_path.endswith('.js'):
            return "js"
        return "txt"

    def create_format(self, format_data):
        """Create a QTextCharFormat based on format data."""
        fmt = QTextCharFormat()
        if "foreground" in format_data:
            fmt.setForeground(QColor(format_data["foreground"]))
        if format_data.get("fontWeight") == "bold":
            fmt.setFontWeight(QFont.Bold)
        return fmt

    def update_highlighting(self):
        """Reload highlighting rules and rehighlight."""
        self.load_highlighting_rules()
        self.rehighlight()

    def highlightBlock(self, text):
        """Apply highlighting rules to the current block of text."""
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text, re.MULTILINE):
                start, end = match.start(), match.end()
                self.setFormat(start, end - start, format)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setUndoRedoEnabled(True)
        self.shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.shortcut_undo.activated.connect(self.undo)
        self.shortcut_redo = QShortcut(QKeySequence("Ctrl+Y"), self)
        self.shortcut_redo.activated.connect(self.redo)
        self.setFont(QFont("Courier", 10))
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)

        self.parent_editor = None
        self.file_path = None
        self.highlighter = None
        self.last_content = self.toPlainText()
        self.last_cursor_pos = self.textCursor().position()
        self.change_timer = QTimer(self)
        self.change_timer.setSingleShot(True)
        self.change_timer.timeout.connect(self.commit_change)
        self.textChanged.connect(self.on_text_changed)

        self.completer = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)

    def setFilePath(self, file_path):
        """Set the file path and initialize the highlighter."""
        self.file_path = file_path
        if self.highlighter:
            self.highlighter.setDocument(None)
        self.highlighter = SyntaxHighlighter(self.document(), file_path, self)
        self.update_completer()

    def line_number_area_width(self):
        """Calculate the width needed for the line number area."""
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_area_width(self, new_block_count):
        """Update the width of the line number area."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Update the line number area when the view is scrolled."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def lineNumberAreaPaintEvent(self, event):
        """Paint the line numbers."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.lightGray)
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.line_number_area.width() - 5, 
                                self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def on_text_changed(self):
        """Handle text changes and queue a commit."""
        if self.change_timer.isActive():
            self.change_timer.stop()
        self.change_timer.start(500)  # Delay of 500ms before committing

    def commit_change(self):
        """Commit the current text change to the parent editor's history."""
        current_content = self.toPlainText()
        current_cursor_pos = self.textCursor().position()
        if current_content != self.last_content and self.parent_editor and self.file_path:
            history_entry = self.parent_editor.file_histories.get(self.file_path)
            if history_entry:
                if history_entry["current_index"] < len(history_entry["history"]) - 1:
                    history_entry["history"] = history_entry["history"][:history_entry["current_index"] + 1]
                history_entry["history"].append({"content": current_content, "cursor_pos": current_cursor_pos})
                if len(history_entry["history"]) > history_entry["max_size"]:
                    history_entry["history"].pop(0)
                history_entry["current_index"] = len(history_entry["history"]) - 1
            self.last_content = current_content
            self.last_cursor_pos = current_cursor_pos
            self.parent_editor.save_current_file()

    def undo(self):
        """Perform an undo operation."""
        if self.parent_editor and self.file_path in self.parent_editor.file_histories:
            history_entry = self.parent_editor.file_histories[self.file_path]
            if history_entry["current_index"] > 0:
                history_entry["current_index"] -= 1
                state = history_entry["history"][history_entry["current_index"]]
                self.setPlainText(state["content"])
                cursor = self.textCursor()
                cursor.setPosition(state["cursor_pos"])
                self.setTextCursor(cursor)
                self.last_content = state["content"]
                self.last_cursor_pos = state["cursor_pos"]

    def redo(self):
        """Perform a redo operation."""
        if self.parent_editor and self.file_path in self.parent_editor.file_histories:
            history_entry = self.parent_editor.file_histories[self.file_path]
            if history_entry["current_index"] < len(history_entry["history"]) - 1:
                history_entry["current_index"] += 1
                state = history_entry["history"][history_entry["current_index"]]
                self.setPlainText(state["content"])
                cursor = self.textCursor()
                cursor.setPosition(state["cursor_pos"])
                self.setTextCursor(cursor)
                self.last_content = state["content"]
                self.last_cursor_pos = state["cursor_pos"]

    def update_completer(self):
        """Update the completer with relevant keywords based on file type."""
        if not self.file_path:
            return
        language = self.determine_language()
        json_path = os.path.join("IDE", "languages", f"{language}.json")
        if not os.path.exists(json_path):
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                rules = json.load(f)
        except Exception as e:
            print(f"Error loading {json_path}: {e}")
            return

        keywords = []
        if language == "html":
            keywords.extend(rules["global_attributes"])
            for tag, tag_data in rules["tags"].items():
                keywords.append(tag)
                keywords.extend([attr["name"] for attr in tag_data["attributes"]])
        elif language == "css":
            keywords.extend(rules["properties"].keys())
        elif language == "js":
            keywords.extend(["function", "var", "let", "const", "if", "else", "for", "while", "return"])
            for obj, obj_data in rules["objects"].items():
                keywords.append(obj)
                keywords.extend([m["name"] for m in obj_data.get("methods", [])])
                keywords.extend([p["name"] for p in obj_data.get("properties", [])])

        model = QStringListModel(list(set(keywords)), self.completer)  # Remove duplicates
        self.completer.setModel(model)

    def determine_language(self):
        """Determine the language based on file extension."""
        if not self.file_path:
            return "txt"
        if self.file_path.endswith('.html'):
            return "html"
        elif self.file_path.endswith('.css'):
            return "css"
        elif self.file_path.endswith('.js'):
            return "js"
        return "txt"

    def keyPressEvent(self, event):
        """Handle key presses for completer and auto-closing."""
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
                self.insert_completion(self.completer.currentCompletion())
                self.completer.popup().hide()
                event.accept()
                return
            elif event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Escape):
                return super().keyPressEvent(event)

        super().keyPressEvent(event)
        cursor = self.textCursor()
        if event.text() in "{[(":
            closing = "}" if event.text() == "{" else "]" if event.text() == "[" else ")"
            self.insertPlainText(closing)
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)
        elif event.text() == "<" and self.file_path and self.file_path.endswith('.html'):
            self.insertPlainText(">")
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)

        # Trigger completer
        text_under_cursor = self.textCursor().block().text()[:self.textCursor().positionInBlock()]
        if text_under_cursor.strip():
            prefix = re.split(r'\W+', text_under_cursor)[-1]
            if len(prefix) > 1:
                self.completer.setCompletionPrefix(prefix)
                cr = self.cursorRect()
                cr.setWidth(self.completer.popup().sizeHintForColumn(0) + 
                           self.completer.popup().verticalScrollBar().sizeHint().width())
                self.completer.complete(cr)

    def insert_completion(self, completion):
        """Insert the selected completion."""
        cursor = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        cursor.movePosition(QTextCursor.Left)
        cursor.movePosition(QTextCursor.EndOfWord)
        cursor.insertText(completion[-extra:])
        self.setTextCursor(cursor)
