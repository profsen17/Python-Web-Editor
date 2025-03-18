import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QTreeWidget, 
                            QTreeWidgetItem, QSplitter, QWidget, QVBoxLayout, 
                            QAction, QMenu, QHBoxLayout, QFileDialog, QMessageBox,
                            QToolBar, QPushButton, QLabel, QInputDialog, QLineEdit,
                            QTabWidget, QGridLayout, QScrollArea, QDialog, QComboBox, QFormLayout, QStackedWidget)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QMimeData, QPoint, QSize, QRect, QStringListModel
from PyQt5.QtGui import QIcon, QTextDocument, QColor, QDrag, QPainter, QPen, QBrush, QPainter, QTextFormat, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtWidgets import QTextEdit, QCompleter
from fuzzywuzzy import fuzz

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
        html_tags = [
          "a", "abbr", "acronym", "address", "applet", "area", "article", "aside", "audio", 
          "b", "base", "basefont", "bdi", "bdo", "big", "blockquote", "body", "br", "button", 
          "canvas", "caption", "center", "cite", "code", "col", "colgroup", "command", "content", 
          "data", "datalist", "dd", "del", "details", "dfn", "dialog", "dir", "div", "dl", "dt", 
          "em", "embed", "fieldset", "figcaption", "figure", "font", "footer", "form", "frame", 
          "frameset", "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hgroup", "hr", "html", 
          "i", "iframe", "img", "input", "ins", "isindex", "kbd", "keygen", "label", "legend", 
          "li", "link", "main", "map", "mark", "marquee", "menu", "menuitem", "meta", "meter", 
          "nav", "nobr", "noframes", "noscript", "object", "ol", "optgroup", "option", "output", 
          "p", "param", "picture", "plaintext", "pre", "progress", "q", "rb", "rp", "rt", "rtc", 
          "ruby", "s", "samp", "script", "section", "select", "shadow", "small", "source", "spacer", 
          "span", "strike", "strong", "style", "sub", "summary", "sup", "svg", "table", "tbody", 
          "td", "template", "textarea", "tfoot", "th", "thead", "time", "title", "tr", "track", 
          "tt", "u", "ul", "var", "video", "wbr", "xmp"
        ]

        css_properties = [
          "align-content", "align-items", "align-self", "all", "animation", "animation-delay", 
          "animation-direction", "animation-duration", "animation-fill-mode", "animation-iteration-count", 
          "animation-name", "animation-play-state", "animation-timing-function", "appearance", "aspect-ratio", 
          "backdrop-filter", "backface-visibility", "background", "background-attachment", "background-blend-mode", 
          "background-clip", "background-color", "background-image", "background-origin", "background-position", 
          "background-repeat", "background-size", "block-size", "border", "border-block", "border-block-color", 
          "border-block-end", "border-block-end-color", "border-block-end-style", "border-block-end-width", 
          "border-block-start", "border-block-start-color", "border-block-start-style", "border-block-start-width", 
          "border-block-style", "border-block-width", "border-bottom", "border-bottom-color", "border-bottom-left-radius", 
          "border-bottom-right-radius", "border-bottom-style", "border-bottom-width", "border-collapse", "border-color", 
          "border-end-end-radius", "border-end-start-radius", "border-image", "border-image-outset", "border-image-repeat", 
          "border-image-slice", "border-image-source", "border-image-width", "border-inline", "border-inline-color", 
          "border-inline-end", "border-inline-end-color", "border-inline-end-style", "border-inline-end-width", 
          "border-inline-start", "border-inline-start-color", "border-inline-start-style", "border-inline-start-width", 
          "border-inline-style", "border-inline-width", "border-left", "border-left-color", "border-left-style", 
          "border-left-width", "border-radius", "border-right", "border-right-color", "border-right-style", "border-right-width", 
          "border-spacing", "border-start-end-radius", "border-start-start-radius", "border-style", "border-top", 
          "border-top-color", "border-top-left-radius", "border-top-right-radius", "border-top-style", "border-top-width", 
          "border-width", "bottom", "box-decoration-break", "box-shadow", "box-sizing", "break-after", "break-before", 
          "break-inside", "caption-side", "caret-color", "clear", "clip", "clip-path", "color", "column-count", "column-fill", 
          "column-gap", "column-rule", "column-rule-color", "column-rule-style", "column-rule-width", "column-span", 
          "column-width", "columns", "contain", "content", "content-visibility", "counter-increment", "counter-reset", 
          "counter-set", "cursor", "direction", "display", "empty-cells", "filter", "flex", "flex-basis", "flex-direction", 
          "flex-flow", "flex-grow", "flex-shrink", "flex-wrap", "float", "font", "font-display", "font-family", "font-feature-settings", 
          "font-kerning", "font-optical-sizing", "font-size", "font-size-adjust", "font-stretch", "font-style", "font-synthesis", 
          "font-variant", "font-variant-alternates", "font-variant-caps", "font-variant-east-asian", "font-variant-ligatures", 
          "font-variant-numeric", "font-variant-position", "font-variation-settings", "font-weight", "gap", "grid", 
          "grid-area", "grid-auto-columns", "grid-auto-flow", "grid-auto-rows", "grid-column", "grid-column-end", 
          "grid-column-gap", "grid-column-start", "grid-gap", "grid-row", "grid-row-end", "grid-row-gap", "grid-row-start", 
          "grid-template", "grid-template-areas", "grid-template-columns", "grid-template-rows", "hanging-punctuation", 
          "height", "hyphens", "image-orientation", "image-rendering", "inline-size", "inset", "inset-block", "inset-block-end", 
          "inset-block-start", "inset-inline", "inset-inline-end", "inset-inline-start", "isolation", "justify-content", 
          "justify-items", "justify-self", "left", "letter-spacing", "line-break", "line-height", "list-style", "list-style-image", 
          "list-style-position", "list-style-type", "margin", "margin-block", "margin-block-end", "margin-block-start", 
          "margin-bottom", "margin-inline", "margin-inline-end", "margin-inline-start", "margin-left", "margin-right", 
          "margin-top", "mask", "mask-border", "mask-border-mode", "mask-border-outset", "mask-border-repeat", 
          "mask-border-slice", "mask-border-source", "mask-border-width", "mask-clip", "mask-composite", "mask-image", 
          "mask-mode", "mask-origin", "mask-position", "mask-repeat", "mask-size", "mask-type", "max-block-size", 
          "max-height", "max-inline-size", "max-width", "min-block-size", "min-height", "min-inline-size", "min-width", 
          "mix-blend-mode", "object-fit", "object-position", "offset", "offset-anchor", "offset-distance", "offset-path", 
          "offset-position", "offset-rotate", "opacity", "order", "orphans", "outline", "outline-color", "outline-offset", 
          "outline-style", "outline-width", "overflow", "overflow-anchor", "overflow-block", "overflow-clip-box", 
          "overflow-inline", "overflow-wrap", "overflow-x", "overflow-y", "overscroll-behavior", "overscroll-behavior-block", 
          "overscroll-behavior-inline", "overscroll-behavior-x", "overscroll-behavior-y", "padding", "padding-block", 
          "padding-block-end", "padding-block-start", "padding-bottom", "padding-inline", "padding-inline-end", 
          "padding-inline-start", "padding-left", "padding-right", "padding-top", "page-break-after", "page-break-before", 
          "page-break-inside", "paint-order", "perspective", "perspective-origin", "place-content", "place-items", 
          "place-self", "pointer-events", "position", "quotes", "resize", "right", "rotate", "row-gap", "scale", 
          "scroll-behavior", "scroll-margin", "scroll-margin-block", "scroll-margin-block-end", "scroll-margin-block-start", 
          "scroll-margin-bottom", "scroll-margin-inline", "scroll-margin-inline-end", "scroll-margin-inline-start", 
          "scroll-margin-left", "scroll-margin-right", "scroll-margin-top", "scroll-padding", "scroll-padding-block", 
          "scroll-padding-block-end", "scroll-padding-block-start", "scroll-padding-bottom", "scroll-padding-inline", 
          "scroll-padding-inline-end", "scroll-padding-inline-start", "scroll-padding-left", "scroll-padding-right", 
          "scroll-padding-top", "scroll-snap-align", "scroll-snap-stop", "scroll-snap-type", "scrollbar-color", 
          "scrollbar-gutter", "scrollbar-width", "shape-image-threshold", "shape-margin", "shape-outside", "tab-size", 
          "table-layout", "text-align", "text-align-last", "text-combine-upright", "text-decoration", "text-decoration-color", 
          "text-decoration-line", "text-decoration-style", "text-decoration-thickness", "text-emphasis", "text-emphasis-color", 
          "text-emphasis-position", "text-emphasis-style", "text-indent", "text-justify", "text-orientation", 
          "text-overflow", "text-rendering", "text-shadow", "text-transform", "text-underline-offset", "text-underline-position", 
          "top", "touch-action", "transform", "transform-box", "transform-origin", "transform-style", "transition", 
          "transition-delay", "transition-duration", "transition-property", "transition-timing-function", "unicode-bidi", 
          "user-select", "vertical-align", "visibility", "white-space", "width", "will-change", "word-break", 
          "word-spacing", "word-wrap", "writing-mode", "z-index", "zoom"
        ]

        js_functions = [
          # Keywords
          "break", "case", "catch", "class", "const", "continue", "debugger", "default", "delete", "do",
          "else", "enum", "export", "extends", "false", "finally", "for", "function", "if", "import", "in",
          "instanceof", "let", "new", "null", "return", "super", "switch", "this", "throw", "true", "try",
          "typeof", "var", "void", "while", "with", "yield",
    
          # Console functions
          "console.log", "console.error", "console.warn", "console.info", "console.debug", "console.clear",
          "console.table", "console.time", "console.timeEnd", "console.count", "console.group",
          "console.groupEnd", "console.trace",

          # Document functions
          "document.getElementById", "document.getElementsByClassName", "document.getElementsByTagName",
          "document.querySelector", "document.querySelectorAll", "document.createElement",
          "document.createTextNode", "document.appendChild", "document.removeChild",
          "document.replaceChild", "document.write", "document.execCommand",

          # Event functions
          "addEventListener", "removeEventListener", "dispatchEvent",

          # Window functions
          "alert", "confirm", "prompt", "setTimeout", "setInterval", "clearTimeout", "clearInterval",
          "requestAnimationFrame", "cancelAnimationFrame", "scrollTo", "scrollBy",

          # Math functions
          "Math.abs", "Math.ceil", "Math.floor", "Math.round", "Math.max", "Math.min",
          "Math.pow", "Math.sqrt", "Math.random", "Math.sin", "Math.cos", "Math.tan",
          "Math.log", "Math.exp",

          # String functions
          "String.fromCharCode", "String.fromCodePoint", "String.prototype.charAt",
          "String.prototype.charCodeAt", "String.prototype.codePointAt",
          "String.prototype.concat", "String.prototype.includes", "String.prototype.indexOf",
          "String.prototype.lastIndexOf", "String.prototype.match", "String.prototype.replace",
          "String.prototype.search", "String.prototype.slice", "String.prototype.split",
          "String.prototype.startsWith", "String.prototype.endsWith", "String.prototype.substring",
          "String.prototype.toLowerCase", "String.prototype.toUpperCase", "String.prototype.trim",

          # Array functions
          "Array.isArray", "Array.from", "Array.of", "Array.prototype.concat",
          "Array.prototype.every", "Array.prototype.filter", "Array.prototype.find",
          "Array.prototype.findIndex", "Array.prototype.forEach", "Array.prototype.includes",
          "Array.prototype.indexOf", "Array.prototype.join", "Array.prototype.map",
          "Array.prototype.pop", "Array.prototype.push", "Array.prototype.reduce",
          "Array.prototype.reduceRight", "Array.prototype.reverse", "Array.prototype.shift",
          "Array.prototype.slice", "Array.prototype.some", "Array.prototype.sort",
          "Array.prototype.splice", "Array.prototype.unshift",

          # Object functions
          "Object.assign", "Object.create", "Object.defineProperty", "Object.defineProperties",
          "Object.entries", "Object.freeze", "Object.fromEntries", "Object.getOwnPropertyDescriptor",
          "Object.getOwnPropertyDescriptors", "Object.getOwnPropertyNames", "Object.getOwnPropertySymbols",
          "Object.getPrototypeOf", "Object.is", "Object.isExtensible", "Object.isFrozen",
          "Object.isSealed", "Object.keys", "Object.preventExtensions", "Object.seal", "Object.setPrototypeOf",
          "Object.values",

          # JSON functions
          "JSON.parse", "JSON.stringify",

          # Date functions
          "Date.now", "Date.parse", "Date.prototype.getDate", "Date.prototype.getDay",
          "Date.prototype.getFullYear", "Date.prototype.getHours", "Date.prototype.getMilliseconds",
          "Date.prototype.getMinutes", "Date.prototype.getMonth", "Date.prototype.getSeconds",
          "Date.prototype.getTime", "Date.prototype.getTimezoneOffset", "Date.prototype.getUTCDate",
          "Date.prototype.getUTCDay", "Date.prototype.getUTCFullYear", "Date.prototype.getUTCHours",
          "Date.prototype.getUTCMilliseconds", "Date.prototype.getUTCMinutes", "Date.prototype.getUTCMonth",
          "Date.prototype.getUTCSeconds", "Date.prototype.setDate", "Date.prototype.setFullYear",
          "Date.prototype.setHours", "Date.prototype.setMilliseconds", "Date.prototype.setMinutes",
          "Date.prototype.setMonth", "Date.prototype.setSeconds", "Date.prototype.setTime",
          "Date.prototype.setUTCDate", "Date.prototype.setUTCFullYear", "Date.prototype.setUTCHours",
          "Date.prototype.setUTCMilliseconds", "Date.prototype.setUTCMinutes", "Date.prototype.setUTCMonth",
          "Date.prototype.setUTCSeconds", "Date.prototype.toDateString", "Date.prototype.toISOString",
          "Date.prototype.toJSON", "Date.prototype.toLocaleDateString", "Date.prototype.toLocaleString",
          "Date.prototype.toLocaleTimeString", "Date.prototype.toString", "Date.prototype.toTimeString",
          "Date.prototype.toUTCString",

          # Fetch & Ajax functions
          "fetch", "XMLHttpRequest", "XMLHttpRequest.prototype.open", "XMLHttpRequest.prototype.send",
          "XMLHttpRequest.prototype.setRequestHeader", "XMLHttpRequest.prototype.getResponseHeader",
          "XMLHttpRequest.prototype.abort",

          # Storage functions
          "localStorage.setItem", "localStorage.getItem", "localStorage.removeItem",
          "localStorage.clear", "sessionStorage.setItem", "sessionStorage.getItem",
          "sessionStorage.removeItem", "sessionStorage.clear",

          # Web APIs
          "navigator.geolocation.getCurrentPosition", "navigator.geolocation.watchPosition",
          "navigator.geolocation.clearWatch", "navigator.clipboard.writeText",
          "navigator.clipboard.readText",

          # Web Workers
          "Worker", "Worker.prototype.postMessage", "Worker.prototype.terminate",

          # Promises & Async functions
          "Promise", "Promise.resolve", "Promise.reject", "Promise.all", "Promise.race",
          "Promise.allSettled", "Promise.any", "async", "await",

          # WebSockets
          "WebSocket", "WebSocket.prototype.send", "WebSocket.prototype.close",

          # Error handling
          "try", "catch", "finally", "throw", "Error", "TypeError", "SyntaxError",
          "ReferenceError", "RangeError",

          # Miscellaneous
          "setImmediate", "clearImmediate", "queueMicrotask", "structuredClone"
        ]


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
