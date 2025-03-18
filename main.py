import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPlainTextEdit, QTreeWidget, 
                            QTreeWidgetItem, QSplitter, QWidget, QVBoxLayout, 
                            QAction, QMenu, QHBoxLayout, QFileDialog, QMessageBox,
                            QToolBar, QPushButton, QLabel, QInputDialog, QLineEdit,
                            QTabWidget, QGridLayout, QScrollArea, QDialog, QComboBox, 
                            QFormLayout, QStackedWidget, QTextEdit)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QMimeData, QPoint, QSize, QRect
from PyQt5.QtGui import QIcon, QColor, QDrag, QPainter, QPen, QBrush, QFont, QTextFormat, QTextCharFormat
from fuzzywuzzy import fuzz

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Courier", 10))  # Use a monospaced font for better alignment
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)

    def line_number_area_width(self):
        digits = 1
        max_lines = max(1, self.blockCount())
        while max_lines >= 10:
            max_lines /= 10
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

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            # Create an extra selection for the current line
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        height = self.fontMetrics().height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                # Use QRect to specify the bounding box for the text
                rect = QRect(0, top, self.line_number_area.width() - 3, height)
                painter.drawText(rect, Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

class GridWidget(QWidget):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor  # Reference to HTMLEditor instance
        self.grid_size = 20
        self.items = []
        self.drag_preview = None
        self.setAcceptDrops(True)
        self.setMinimumHeight(300)

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(QColor(200, 200, 200, 50) if self.editor.is_dark_mode else QColor(0, 0, 0, 50), 1, Qt.DotLine)
        painter.setPen(pen)

        for x in range(0, self.width(), self.grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), self.grid_size):
            painter.drawLine(0, y, self.width(), y)

        if self.drag_preview:
            painter.setBrush(QBrush(QColor(100, 100, 255, 100)))
            painter.setPen(Qt.NoPen)
            pos, size = self.drag_preview
            painter.drawRect(pos.x(), pos.y(), size.width(), size.height())

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-button"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-button"):
            pos = event.pos()
            snapped_pos = self.snap_to_grid(pos)
            self.drag_preview = (snapped_pos, QSize(100, 40))
            self.update()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.drag_preview = None
        self.update()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-button"):
            pos = event.pos()
            snapped_pos = self.snap_to_grid(pos)
            button = QPushButton("Button", self)
            button.setFixedSize(100, 40)
            button.move(snapped_pos)
            button.show()
            self.items.append((button, snapped_pos))
            self.drag_preview = None
            self.update()
            event.acceptProposedAction()

    def snap_to_grid(self, pos):
        x = round(pos.x() / self.grid_size) * self.grid_size
        y = round(pos.y() / self.grid_size) * self.grid_size

        mid_x = self.width() // 2
        if abs(x + 50 - mid_x) < self.grid_size * 2:
            x = mid_x - 50

        mid_y = self.height() // 2
        if abs(y + 20 - mid_y) < self.grid_size * 2:
            y = mid_y - 20

        x = max(0, min(x, self.width() - 100))
        y = max(0, min(y, self.height() - 40))
        
        return QPoint(x, y)

class DraggableButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(100, 40)
        self.setMaximumWidth(120)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setData("application/x-button", b"button")
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)

class FileSelectionDialog(QDialog):
    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Main Files")
        self.project_path = project_path
        self.layout = QFormLayout()

        self.html_files = self.find_files(".html")
        self.css_files = self.find_files(".css")
        self.js_files = self.find_files(".js")

        self.html_combo = QComboBox()
        self.html_combo.addItems(self.html_files if self.html_files else ["None"])
        self.layout.addRow("Main HTML File:", self.html_combo)

        self.css_combo = QComboBox()
        self.css_combo.addItems(self.css_files if self.css_files else ["None"])
        self.layout.addRow("Main CSS File:", self.css_combo)

        self.js_combo = QComboBox()
        self.js_combo.addItems(self.js_files if self.js_files else ["None"])
        self.layout.addRow("Main JS File:", self.js_combo)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)

    def find_files(self, extension):
        files = []
        for root, _, filenames in os.walk(self.project_path):
            for filename in filenames:
                if filename.endswith(extension) and not filename.startswith('.'):
                    files.append(os.path.relpath(os.path.join(root, filename), self.project_path))
        return files

    def get_selected_files(self):
        html_file = self.html_combo.currentText() if self.html_combo.currentText() != "None" else None
        css_file = self.css_combo.currentText() if self.css_combo.currentText() != "None" else None
        js_file = self.js_combo.currentText() if self.js_combo.currentText() != "None" else None
        return html_file, css_file, js_file

class HTMLEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project_path = None
        self.current_file = None
        self.file_histories = {}  # Now stores plain strings instead of QTextDocument
        self.expanded_state = {}
        self.is_dark_mode = False
        self.main_html_file = None
        self.main_css_file = None
        self.main_js_file = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('HTML & CSS Editor')
        self.setGeometry(100, 100, 1000, 700)

        self.breadcrumb_bar = QToolBar("Breadcrumbs")
        self.breadcrumb_bar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.breadcrumb_bar)
        self.update_breadcrumbs(None)

        main_splitter = QSplitter(Qt.Horizontal)

        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setVisible(False)
        
        project_files_widget = QWidget()
        project_files_layout = QVBoxLayout()
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Cerca file...")
        self.search_bar.textChanged.connect(self.filter_files)
        project_files_layout.addWidget(self.search_bar)
        
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel("Project Files")
        self.file_tree.itemClicked.connect(self.handle_item_clicked)
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.file_tree.setExpandsOnDoubleClick(False)
        self.file_tree.itemChanged.connect(self.rename_item)
        self.file_tree.itemExpanded.connect(self.store_expanded_state)
        self.file_tree.itemCollapsed.connect(self.store_expanded_state)
        self.file_tree.viewport().installEventFilter(self)
        project_files_layout.addWidget(self.file_tree)
        
        # Add New Page button below the file tree
        new_page_button = QPushButton("New Page")
        new_page_button.clicked.connect(self.newPage)
        project_files_layout.addWidget(new_page_button)
        
        project_files_widget.setLayout(project_files_layout)
        self.tab_widget.addTab(project_files_widget, "Project Files")
        
        components_widget = QWidget()
        components_layout = QVBoxLayout()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        
        components_grid = QGridLayout()
        components_grid.setSpacing(10)
        components_grid.setAlignment(Qt.AlignHCenter)
        
        btn1 = DraggableButton("Button")
        components_grid.addWidget(btn1, 0, 0)
        
        btn2 = DraggableButton("Div")
        components_grid.addWidget(btn2, 0, 1)
        
        btn3 = DraggableButton("Image")
        components_grid.addWidget(btn3, 1, 0)
        
        btn4 = DraggableButton("Text")
        components_grid.addWidget(btn4, 1, 1)
        
        scroll_content.setLayout(components_grid)
        scroll_area.setWidget(scroll_content)
        components_layout.addWidget(scroll_area)
        
        components_widget.setLayout(components_layout)
        self.tab_widget.addTab(components_widget, "Components")
        
        sidebar_layout.addWidget(self.tab_widget)
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setMinimumWidth(200)

        # Assign right_widget as an instance variable
        self.right_widget = QWidget()
        right_layout = QVBoxLayout()

        # Toolbar for switching views
        view_toolbar = QToolBar()
        self.design_button = QPushButton("Design View")
        self.design_button.setCheckable(True)
        self.design_button.setChecked(True)
        self.design_button.clicked.connect(self.switch_to_design)
        view_toolbar.addWidget(self.design_button)

        self.code_button = QPushButton("Code View")
        self.code_button.setCheckable(True)
        self.code_button.clicked.connect(self.switch_to_code)
        view_toolbar.addWidget(self.code_button)

        right_layout.addWidget(view_toolbar)

        # Stacked widget for views
        self.view_stack = QStackedWidget()
        self.design_view = GridWidget(self)
        self.code_view = CodeEditor()
        self.code_view.setPlaceholderText("Code View")
        self.code_view.textChanged.connect(self.save_current_file)

        self.view_stack.addWidget(self.design_view)
        self.view_stack.addWidget(self.code_view)
        right_layout.addWidget(self.view_stack)

        self.right_widget.setLayout(right_layout)
        # Initially hide the right widget if no project is loaded
        self.right_widget.setVisible(False)

        main_splitter.addWidget(sidebar_widget)
        main_splitter.addWidget(self.right_widget)
        
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.addWidget(main_splitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.createMenu()
        self.apply_theme()
        self.show()

    def apply_theme(self):
        if self.is_dark_mode:
            self.setStyleSheet("""
            QMainWindow { 
                background-color: #2b2b2b; 
                color: #ffffff; 
            }
            QMenuBar {
                background-color: #3c3f41;
                border-radius: 5px; 
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;               
            }
            QToolBar { 
                background-color: #2b2b2b; 
                border: none; 
                padding: 5px; 
                color: #ffffff;
            }
            QPushButton { 
                background-color: #4a4a4a; 
                color: #ffffff; 
                border: none; 
                border-radius: 8px; 
                padding: 5px; 
            }
            QPushButton:hover { 
                background-color: #5a5a5a; 
            }
            QPlainTextEdit { 
                background-color: #1e1e1e; 
                color: #ffffff; 
                border: 1px solid #555555; 
                border-radius: 10px; 
                padding: 5px; 
            }
            QTreeWidget { 
                background-color: #333333; 
                color: #ffffff; 
                border: 1px solid #555555; 
                border-radius: 10px; 
            }
            QTreeWidget::item:hover { 
                background-color: #444444; 
            }
            QTreeWidget::item:selected { 
                background-color: #5a5a5a; 
                color: #ffffff; 
            }
            QTreeWidget::item:selected:hover { 
                background-color: #666666; 
                color: #ffffff; 
            }
            QHeaderView {
                background-color: #000000;
                border-radius: 10px;
            }
            QHeaderView::section { 
                background-color: #3c3f41; 
                color: #ffffff; 
                border: none; 
                padding: 5px; 
                border-top-left-radius: 10px; 
                border-top-right-radius: 10px; 
            }
            QLineEdit { 
                background-color: #3c3f41; 
                color: #ffffff; 
                border: 1px solid #555555; 
                border-radius: 8px; 
                padding: 5px; 
                min-height: 30px;
            }
            QTreeWidget QLineEdit { 
                min-height: 30px; 
                padding: 5px; 
                font-size: 14px; 
            }
            QSplitter::handle { 
                background-color: #555555; 
                border-radius: 5px; 
            }
            QMenu { 
                background-color: #3c3f41; 
                color: #ffffff; 
                border: 1px solid #555555; 
                padding: 5px;
            }
            QMenu::item { 
                padding: 5px 25px 5px 25px; 
            }
            QMenu::item:selected { 
                background-color: #5a5a5a; 
            }
            QMessageBox { 
                background-color: #000000; 
                color: #ffffff; 
                border: 1px solid #555555; 
                border-radius: 5px; 
                background-color: #3a3a3a;   
            }
            QMessageBox QLabel { 
                color: #ffffff;  
            }
            QMessageBox QPushButton { 
                background-color: #4a4a4a; 
                color: #ffffff; 
                border: none; 
                border-radius: 8px; 
                padding: 5px; 
            }
            QMessageBox QPushButton:hover { 
                background-color: #5a5a5a; 
            }
            QTabWidget::pane { 
                background-color: #2b2b2b; 
                border: 1px solid #555555; 
                border-radius: 5px; 
            }
            QTabBar::tab { 
                background-color: #3c3f41; 
                color: #ffffff; 
                padding: 5px; 
                border-top-left-radius: 5px; 
                border-top-right-radius: 5px; 
            }
            QTabBar::tab:selected { 
                background-color: #5a5a5a; 
            }
            QScrollArea { 
                background-color: #2b2b2b; 
                border: none; 
            }
            GridWidget { 
                background-color: #1e1e1e; 
            }
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QComboBox {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QWidget#LineNumberArea {
                background-color: #2b2b2b;
                color: #ffffff;
                border-right: 1px solid #555555;
            }
            """)
        else:
            self.setStyleSheet("""
            QMainWindow { 
                background-color: #f0f0f0; 
                color: #000000; 
            }
            QMenuBar {
                background-color: #e0e0e0;
                border-radius: 5px; 
            }
            QLabel {
                color: #000000;               
            }
            QToolBar { 
                background-color: #f0f0f0; 
                border: none; 
                padding: 5px; 
            }
            QPushButton { 
                background-color: #d0d0d0; 
                color: #000000; 
                border: none; 
                border-radius: 8px; 
                padding: 5px; 
            }
            QPushButton:hover { 
                background-color: #c0c0c0; 
            }
            QPlainTextEdit { 
                background-color: #ffffff; 
                color: #000000; 
                border: 1px solid #cccccc; 
                border-radius: 10px; 
                padding: 5px; 
            }
            QTreeWidget { 
                background-color: #ffffff; 
                color: #000000; 
                border: 1px solid #cccccc; 
                border-radius: 10px; 
            }
            QTreeWidget::item:hover { 
                background-color: #f5f5f5; 
            }
            QTreeWidget::item:selected { 
                background-color: #d0d0d0; 
                color: #000000; 
            }
            QTreeWidget::item:selected:hover { 
                background-color: #c0c0c0; 
                color: #000000; 
            }
            QHeaderView {
                background-color: #e0e0e0;
                border-radius: 10px;
            }
            QHeaderView::section { 
                background-color: #e0e0e0; 
                color: #000000; 
                border: none; 
                padding: 5px; 
                border-top-left-radius: 10px; 
                border-top-right-radius: 10px; 
            }
            QLineEdit { 
                background-color: #e0e0e0; 
                color: #000000; 
                border: 1px solid #cccccc; 
                border-radius: 5px; 
                padding: 5px; 
                min-height: 11px; 
            }
            QTreeWidget QLineEdit { 
                min-height: 11px; 
                padding: 5px; 
                font-size: 11px; 
            }
            QSplitter::handle { 
                background-color: #cccccc; 
                border-radius: 5px; 
            }
            QMenu { 
                background-color: #e0e0e0; 
                color: #000000; 
                border: 1px solid #cccccc; 
                border-radius: 10px; 
                padding: 5px; 
            }
            QMenu::item { 
                padding: 5px 25px 5px 25px; 
            }
            QMenu::item:selected { 
                background-color: #d0d0d0; 
            }
            QTabWidget::pane { 
                background-color: #f0f0f0; 
                border: 1px solid #cccccc; 
                border-radius: 5px; 
            }
            QTabBar::tab { 
                background-color: #e0e0e0; 
                color: #000000; 
                padding: 5px; 
                border-top-left-radius: 5px; 
                border-top-right-radius: 5px; 
            }
            QTabBar::tab:selected { 
                background-color: #d0d0d0; 
            }
            QScrollArea { 
                background-color: #f0f0f0; 
                border: none; 
            }
            GridWidget { 
                background-color: #ffffff; 
            }
            QDialog {
                background-color: #f0f0f0;
                color: #000000;
            }
            QComboBox {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #cccccc;
            }
            QWidget#LineNumberArea {
                background-color: #f0f0f0;
                color: #000000;
                border-right: 1px solid #cccccc;
            }
            """)

    def animate_button(self, button):
        anim = QPropertyAnimation(button, b"geometry")
        anim.setDuration(100)
        anim.setStartValue(button.geometry())
        anim.setEndValue(button.geometry().adjusted(-2, -2, 2, 2))
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def eventFilter(self, obj, event):
        if obj == self.file_tree.viewport() and event.type() == event.MouseButtonPress:
            if not self.file_tree.itemAt(event.pos()):
                self.file_tree.clearSelection()
                self.update_breadcrumbs(None)
        return super().eventFilter(obj, event)

    def createMenu(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')
        
        newAct = QAction('Nuovo Progetto', self)
        newAct.setShortcut('Ctrl+N')
        newAct.triggered.connect(self.newProject)
        fileMenu.addAction(newAct)
        
        openAct = QAction('Apri Progetto', self)
        openAct.setShortcut('Ctrl+O')
        openAct.triggered.connect(self.openProject)
        fileMenu.addAction(openAct)
        
        saveAct = QAction('Salva', self)
        saveAct.setShortcut('Ctrl+S')
        saveAct.triggered.connect(self.save_current_file)
        fileMenu.addAction(saveAct)

        # Add New Page action
        newPageAct = QAction('Nuova Pagina', self)
        newPageAct.setShortcut('Ctrl+Shift+N')
        newPageAct.triggered.connect(self.newPage)
        fileMenu.addAction(newPageAct)

        themeMenu = menubar.addMenu('Theme')
        lightAct = QAction('Light Mode', self)
        lightAct.triggered.connect(lambda: self.set_theme(False))
        themeMenu.addAction(lightAct)
        
        darkAct = QAction('Dark Mode', self)
        darkAct.triggered.connect(lambda: self.set_theme(True))
        themeMenu.addAction(darkAct)

    def set_theme(self, dark_mode):
        self.is_dark_mode = dark_mode
        self.apply_theme()

    def update_breadcrumbs(self, item):
        self.breadcrumb_bar.clear()
        if not self.project_path:
            self.breadcrumb_bar.addWidget(QLabel("Nessun progetto aperto"))
            return
            
        path_parts = []
        current_item = item
        
        while current_item:
            path_parts.insert(0, current_item)
            current_item = current_item.parent()
        
        if not path_parts and self.project_path:
            path_parts = [self.file_tree.topLevelItem(0)]
        
        for i, part in enumerate(path_parts):
            btn = QPushButton(part.text(0))
            btn.setFlat(True)
            btn.clicked.connect(lambda checked, item=part: self.file_tree.setCurrentItem(item))
            btn.clicked.connect(lambda: self.animate_button(btn))
            self.breadcrumb_bar.addWidget(btn)
            if i < len(path_parts) - 1:
                self.breadcrumb_bar.addWidget(QLabel(">"))

    def store_expanded_state(self, item):
        item_path = item.data(0, Qt.UserRole)
        if item_path:
            self.expanded_state[item_path] = item.isExpanded()

    def restore_expanded_state(self, item):
        item_path = item.data(0, Qt.UserRole)
        if item_path in self.expanded_state:
            item.setExpanded(self.expanded_state[item_path])
        for i in range(item.childCount()):
            self.restore_expanded_state(item.child(i))

    def filter_files(self, text):
        if not self.project_path:
            return

        search_text = text.replace(" ", "").lower()
        
        if not self.search_bar.text():
            self.file_tree.clear()
            self.load_project_structure(self.project_path)
            self.restore_expanded_state(self.file_tree.topLevelItem(0))
            return

        if self.file_tree.topLevelItem(0):
            self.store_expanded_state_recursive(self.file_tree.topLevelItem(0))

        self.file_tree.clear()
        root_item = QTreeWidgetItem(self.file_tree, [os.path.basename(self.project_path)])
        root_item.setIcon(0, QIcon("icons/folder.png"))
        root_item.setFlags(root_item.flags() & ~Qt.ItemIsEditable)
        root_item.setData(0, Qt.UserRole, self.project_path)

        for dirpath, _, filenames in os.walk(self.project_path):
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                file_no_spaces = filename.replace(" ", "").lower()
                match_score = fuzz.partial_ratio(search_text, file_no_spaces)
                if match_score >= 70:
                    rel_path = os.path.relpath(os.path.join(dirpath, filename), self.project_path)
                    path_parts = rel_path.split(os.sep)
                    
                    current_item = root_item
                    for i, part in enumerate(path_parts):
                        if i == len(path_parts) - 1:
                            file_item = QTreeWidgetItem(current_item, [part])
                            file_item.setFlags(file_item.flags() & ~Qt.ItemIsEditable)
                            file_item.setData(0, Qt.UserRole, os.path.join(self.project_path, rel_path))
                            self.update_file_icon(file_item)
                        else:
                            found = False
                            for j in range(current_item.childCount()):
                                if current_item.child(j).text(0) == part:
                                    current_item = current_item.child(j)
                                    found = True
                                    break
                            if not found:
                                folder_item = QTreeWidgetItem(current_item, [part])
                                folder_item.setIcon(0, QIcon("icons/folder.png"))
                                folder_item.setFlags(folder_item.flags() & ~Qt.ItemIsEditable)
                                folder_item.setData(0, Qt.UserRole, os.path.join(self.project_path, os.sep.join(path_parts[:i+1])))
                                current_item = folder_item
        
        self.expand_all_items(root_item)

    def store_expanded_state_recursive(self, item):
        self.store_expanded_state(item)
        for i in range(item.childCount()):
            self.store_expanded_state_recursive(item.child(i))

    def expand_all_items(self, item):
        item.setExpanded(True)
        for i in range(item.childCount()):
            self.expand_all_items(item.child(i))

    def newProject(self):
        parent_folder = QFileDialog.getExistingDirectory(self, "Seleziona cartella progetto")
        if not parent_folder:
            return

        project_name, ok = QInputDialog.getText(self, "Nuovo Progetto", "Inserisci il nome del progetto:", text="MyProject")
        if not ok or not project_name:
            QMessageBox.warning(self, "Errore", "Devi inserire un nome per il progetto.")
            return

        self.project_path = os.path.join(parent_folder, project_name)
        try:
            os.makedirs(self.project_path, exist_ok=True)

            script_folder_path = os.path.join(self.project_path, "Scripts")
            os.makedirs(script_folder_path, exist_ok=True)

            css_folder_path = os.path.join(script_folder_path, "css")
            os.makedirs(css_folder_path, exist_ok=True)
            style_file_path = os.path.join(css_folder_path, "style.css")
            with open(style_file_path, "w") as f:
                f.write("/* CSS File */\n")

            js_folder_path = os.path.join(script_folder_path, "js")
            os.makedirs(js_folder_path, exist_ok=True)
            script_file_path = os.path.join(js_folder_path, "script.js")
            with open(script_file_path, "w") as f:
                f.write("// JavaScript File\n")

            html_folder_path = os.path.join(script_folder_path, "html")
            os.makedirs(html_folder_path, exist_ok=True)
            index_file_path = os.path.join(html_folder_path, "index.html")
            with open(index_file_path, "w") as f:
                f.write("<html>\n<head>\n</head>\n<body>\n</body>\n</html>")

            assets_folder_path = os.path.join(self.project_path, "Assets")
            os.makedirs(assets_folder_path, exist_ok=True)

            self.file_histories.clear()
            self.expanded_state.clear()
            self.file_tree.clear()
            self.load_project_structure(self.project_path)
            self.search_bar.setVisible(True)
            self.tab_widget.setVisible(True)
            self.update_breadcrumbs(self.file_tree.topLevelItem(0))
            self.select_main_files()
            # Show the right widget when a project is created
            self.right_widget.setVisible(True)
            self.statusBar().showMessage(f'Nuovo progetto creato in {self.project_path}', 2000)

        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Errore durante la creazione del progetto: {str(e)}")
            self.project_path = None
            self.search_bar.setVisible(False)
            self.tab_widget.setVisible(False)
            self.right_widget.setVisible(False)

    def openProject(self):
        default_path = os.getcwd()
        folder = QFileDialog.getExistingDirectory(self, "Seleziona cartella progetto", default_path)
        if folder:
            self.project_path = folder
            self.file_histories.clear()
            self.expanded_state.clear()
            self.file_tree.clear()
            self.load_project_structure(self.project_path)
            self.search_bar.setVisible(True)
            self.tab_widget.setVisible(True)
            self.update_breadcrumbs(self.file_tree.topLevelItem(0))
            self.select_main_files()
            # Show the right widget when a project is opened
            self.right_widget.setVisible(True)
            self.statusBar().showMessage(f'Progetto aperto: {self.project_path}', 2000)
        else:
            self.search_bar.setVisible(False)
            self.tab_widget.setVisible(False)
            self.right_widget.setVisible(False)

    def select_main_files(self):
        dialog = FileSelectionDialog(self.project_path, self)
        if dialog.exec_():
            html_file, css_file, js_file = dialog.get_selected_files()
            self.main_html_file = os.path.join(self.project_path, html_file) if html_file else None
            self.main_css_file = os.path.join(self.project_path, css_file) if css_file else None
            self.main_js_file = os.path.join(self.project_path, js_file) if js_file else None
            if self.main_html_file:
                self.load_html_to_design_view()
            self.statusBar().showMessage(f"Main files selected: HTML={html_file}, CSS={css_file}, JS={js_file}", 2000)

    def load_html_to_design_view(self):
        if self.main_html_file and os.path.exists(self.main_html_file):
            with open(self.main_html_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.design_view.items.clear()
                for widget, _ in self.design_view.items:
                    widget.deleteLater()
                self.design_view.update()

    def load_project_structure(self, path, parent=None):
        if parent is None:
            root = QTreeWidgetItem(self.file_tree, [os.path.basename(path)])
            root.setIcon(0, QIcon("icons/folder.png"))
            root.setFlags(root.flags() & ~Qt.ItemIsEditable)
            root.setData(0, Qt.UserRole, path)
            parent = root
        
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                folder_item = QTreeWidgetItem(parent, [item])
                folder_item.setIcon(0, QIcon("icons/folder.png"))
                folder_item.setFlags(folder_item.flags() & ~Qt.ItemIsEditable)
                folder_item.setData(0, Qt.UserRole, item_path)
                self.load_project_structure(item_path, folder_item)
            elif not item.startswith('.'):
                file_item = QTreeWidgetItem(parent, [item])
                file_item.setFlags(file_item.flags() & ~Qt.ItemIsEditable)
                file_item.setData(0, Qt.UserRole, item_path)
                self.update_file_icon(file_item)

    def update_file_icon(self, item):
        item_path = item.data(0, Qt.UserRole)
        if item_path and os.path.isdir(item_path):
            item.setIcon(0, QIcon("icons/folder.png"))
        elif item_path and os.path.isfile(item_path):
            if item_path.endswith('.html'):
                item.setIcon(0, QIcon("icons/html.png"))
            elif item_path.endswith('.css'):
                item.setIcon(0, QIcon("icons/css.png"))
            elif item_path.endswith('.js'):
                item.setIcon(0, QIcon("icons/js.png"))
            else:
                item.setIcon(0, QIcon("icons/file.png"))

    def show_context_menu(self, position):
        item = self.file_tree.itemAt(position)
        menu = QMenu()
        
        if item:
            if self.is_folder(item):
                add_file_action = QAction(QIcon("icons/add_file.png"), "Aggiungi File", self)
                add_file_action.triggered.connect(lambda: self.addFile(item))
                menu.addAction(add_file_action)
                
                add_folder_action = QAction(QIcon("icons/folder.png"), "Aggiungi Cartella", self)
                add_folder_action.triggered.connect(lambda: self.addFolder(item))
                menu.addAction(add_folder_action)
                
                rename_action = QAction(QIcon("icons/rename.png"), "Rinomina", self)
                rename_action.triggered.connect(lambda: self.start_rename(item))
                menu.addAction(rename_action)
                
                delete_action = QAction(QIcon("icons/delete_foler.png"), "Elimina", self)
                delete_action.triggered.connect(lambda: self.delete_item(item))
                menu.addAction(delete_action)
            else:
                rename_action = QAction(QIcon("icons/rename.png"), "Rinomina", self)
                rename_action.triggered.connect(lambda: self.start_rename(item))
                menu.addAction(rename_action)
                
                delete_action = QAction(QIcon("icons/delete_file.png"), "Elimina", self)
                delete_action.triggered.connect(lambda: self.delete_item(item))
                menu.addAction(delete_action)
            
            explorer_action = QAction(QIcon("icons/explorer.png"), "Apri in Explorer", self)
            explorer_action.triggered.connect(lambda: self.open_in_explorer(item))
            menu.addAction(explorer_action)
        else:
            self.file_tree.clearSelection()
            self.update_breadcrumbs(None)
        
        if not menu.isEmpty():
            menu.exec_(self.file_tree.viewport().mapToGlobal(position))

    def start_rename(self, item):
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.file_tree.editItem(item, 0)

    def open_in_explorer(self, item):
        item_path = item.data(0, Qt.UserRole)
        if item_path:
            if os.path.isfile(item_path):
                dir_path = os.path.dirname(item_path)
            else:
                dir_path = item_path
            try:
                os.startfile(dir_path)
            except Exception as e:
                QMessageBox.warning(self, "Errore", f"Impossibile aprire Explorer: {str(e)}")

    def is_folder(self, item):
        item_path = item.data(0, Qt.UserRole)
        return item_path and os.path.isdir(item_path)

    def folder_has_contents(self, folder_path):
        if not os.path.isdir(folder_path):
            return False
        return any(os.scandir(folder_path))

    def addFile(self, parent_item=None):
        if not self.project_path:
            QMessageBox.warning(self, "Errore", "Crea o apri un progetto prima")
            return
        
        if parent_item is None:
            parent_item = self.file_tree.currentItem()
        if parent_item is None or not self.is_folder(parent_item):
            parent_item = self.file_tree.topLevelItem(0)
            
        parent_path = parent_item.data(0, Qt.UserRole)
        
        default_name = "new_file.html"
        file_path = os.path.join(parent_path, default_name)
        with open(file_path, "w") as f:
            f.write("")
        
        new_file = QTreeWidgetItem(parent_item, [default_name])
        new_file.setFlags(new_file.flags() & ~Qt.ItemIsEditable)
        new_file.setData(0, Qt.UserRole, file_path)
        self.update_file_icon(new_file)
        
        self.update_breadcrumbs(new_file)
        parent_item.setExpanded(True)
        self.store_expanded_state(parent_item)
        self.file_tree.setCurrentItem(new_file)
        new_file.setFlags(new_file.flags() | Qt.ItemIsEditable)
        self.file_tree.editItem(new_file, 0)

    def addFolder(self, parent_item=None):
        if not self.project_path:
            QMessageBox.warning(self, "Errore", "Crea o apri un progetto prima")
            return
            
        if parent_item is None:
            parent_item = self.file_tree.currentItem()
        if parent_item is None or not self.is_folder(parent_item):
            parent_item = self.file_tree.topLevelItem(0)
            
        parent_path = parent_item.data(0, Qt.UserRole)
        
        new_folder = QTreeWidgetItem(parent_item, ["New Folder"])
        new_folder.setFlags(new_folder.flags() & ~Qt.ItemIsEditable)
        folder_path = os.path.join(parent_path, "New Folder")
        new_folder.setData(0, Qt.UserRole, folder_path)
        self.update_file_icon(new_folder)
        
        os.makedirs(folder_path, exist_ok=True)
        self.update_breadcrumbs(new_folder)
        parent_item.setExpanded(True)
        self.store_expanded_state(parent_item)
        
        self.file_tree.setCurrentItem(new_folder)
        new_folder.setFlags(new_folder.flags() | Qt.ItemIsEditable)
        self.file_tree.editItem(new_folder, 0)
        self.file_tree.itemChanged.connect(lambda item, column: self.update_file_icon(item) if item == new_folder else None)

    def delete_item(self, item):
        item_path = item.data(0, Qt.UserRole)
        if not item_path or not os.path.exists(item_path):
            return
        
        reply = QMessageBox.question(self, "Conferma", f"Vuoi eliminare '{item.text(0)}'?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        if os.path.isdir(item_path) and self.folder_has_contents(item_path):
            second_reply = QMessageBox.question(self, "Conferma Eliminazione",
                                               f"La cartella '{item.text(0)}' contiene file o sottocartelle. Sei sicuro di volerla eliminare?",
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if second_reply != QMessageBox.Yes:
                return

        try:
            if os.path.isfile(item_path):
                os.remove(item_path)
                if item_path in self.file_histories:
                    del self.file_histories[item_path]
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                self.file_tree.takeTopLevelItem(self.file_tree.indexOfTopLevelItem(item))
                self.project_path = None
                self.search_bar.setVisible(False)
                self.tab_widget.setVisible(False)
                self.right_widget.setVisible(False)
            self.statusBar().showMessage(f"Eliminato: {item_path}", 2000)
        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Impossibile eliminare: {str(e)}")

    def handle_item_clicked(self, item, column):
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            self.current_file = file_path
            if file_path not in self.file_histories:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        self.file_histories[file_path] = content
                        self.code_view.setPlainText(content)
                except Exception as e:
                    QMessageBox.warning(self, "Errore", f"Impossibile aprire il file: {str(e)}")
                    return
            else:
                self.code_view.setPlainText(self.file_histories[file_path])
            
            # Show/hide design view based on file type
            if file_path.endswith('.html'):
                self.design_button.setVisible(True)
                self.code_button.setVisible(True)
                # If design view was last selected, switch to it; otherwise, stay in code view
                if self.design_button.isChecked():
                    self.switch_to_design()
                else:
                    self.switch_to_code()
            else:
                # For non-HTML files (e.g., CSS, JS), show only code view
                self.design_button.setVisible(False)
                self.code_button.setVisible(True)
                self.switch_to_code()

            self.statusBar().showMessage(f'Aperto: {file_path}', 2000)
        self.update_breadcrumbs(item)

    def save_current_file(self):
        if self.current_file and os.path.isfile(self.current_file):
            content = self.code_view.toPlainText()
            self.file_histories[self.current_file] = content  # Update the history with the current content
            try:
                with open(self.current_file, "w", encoding="utf-8") as f:
                    f.write(content)
                self.statusBar().showMessage(f'Salvato: {self.current_file}', 1000)
            except Exception as e:
                QMessageBox.warning(self, "Errore", f"Impossibile salvare il file: {str(e)}")

    def rename_item(self, item, column):
        if not self.project_path:
            return
            
        old_path = item.data(0, Qt.UserRole)
        new_name = item.text(column)
        if not old_path or not os.path.exists(old_path) or os.path.basename(old_path) == new_name:
            return

        new_path = os.path.join(os.path.dirname(old_path), new_name)
        
        try:
            os.rename(old_path, new_path)
            item.setData(0, Qt.UserRole, new_path)
            self.update_file_icon(item)
            if old_path == self.project_path:
                self.project_path = new_path
            if old_path in self.file_histories:
                self.file_histories[new_path] = self.file_histories.pop(old_path)
                if self.current_file == old_path:
                    self.current_file = new_path
                    self.code_view.setPlainText(self.file_histories[new_path])
            self.update_breadcrumbs(item)
            self.statusBar().showMessage(f"Rinominato: {old_path} -> {new_path}", 2000)
        except PermissionError:
            QMessageBox.warning(self, "Errore", f"Accesso negato: non è possibile rinominare '{old_path}'. Assicurati che il file o la cartella non sia in uso.")
            item.setText(column, os.path.basename(old_path))
        except OSError as e:
            QMessageBox.warning(self, "Errore", f"Errore durante la rinomina: {str(e)}")
            item.setText(column, os.path.basename(old_path))
        finally:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)

    def closeEvent(self, event):
        super().closeEvent(event)

    def switch_to_design(self):
        if self.current_file and self.current_file.endswith('.html'):
            self.view_stack.setCurrentWidget(self.design_view)
            self.design_button.setChecked(True)
            self.code_button.setChecked(False)

    def switch_to_code(self):
        self.view_stack.setCurrentWidget(self.code_view)
        self.code_button.setChecked(True)
        self.design_button.setChecked(False)

    def newPage(self):
        if not self.project_path:
            QMessageBox.warning(self, "Errore", "Crea o apri un progetto prima")
            return

        page_name, ok = QInputDialog.getText(self, "Nuova Pagina", "Inserisci il nome della pagina:", text="NewPage")
        if not ok or not page_name:
            QMessageBox.warning(self, "Errore", "Devi inserire un nome per la pagina.")
            return

        try:
            # Define folder paths
            script_folder_path = os.path.join(self.project_path, "Scripts")
            css_folder_path = os.path.join(script_folder_path, "css")
            js_folder_path = os.path.join(script_folder_path, "js")
            html_folder_path = os.path.join(script_folder_path, "html")

            # Ensure folders exist
            os.makedirs(css_folder_path, exist_ok=True)
            os.makedirs(js_folder_path, exist_ok=True)
            os.makedirs(html_folder_path, exist_ok=True)

            # Create files with the page name
            html_file_path = os.path.join(html_folder_path, f"{page_name}.html")
            css_file_path = os.path.join(css_folder_path, f"{page_name}.css")
            js_file_path = os.path.join(js_folder_path, f"{page_name}.js")

            # Write initial content to files
            with open(html_file_path, "w") as f:
                f.write(f"<html>\n<head>\n<link rel=\"stylesheet\" href=\"../css/{page_name}.css\">\n<script src=\"../js/{page_name}.js\"></script>\n</head>\n<body>\n</body>\n</html>")
            with open(css_file_path, "w") as f:
                f.write(f"/* CSS for {page_name} */\n")
            with open(js_file_path, "w") as f:
                f.write(f"// JavaScript for {page_name}\n")

            # Update file tree
            self.file_tree.clear()
            self.load_project_structure(self.project_path)
            self.restore_expanded_state(self.file_tree.topLevelItem(0))
            
            # Find and select the new HTML file in the tree
            html_item = self.find_item_by_path(html_file_path)
            if html_item:
                self.file_tree.setCurrentItem(html_item)
                self.update_breadcrumbs(html_item)
                self.handle_item_clicked(html_item, 0)

            self.statusBar().showMessage(f'Nuova pagina "{page_name}" creata in {html_folder_path}', 2000)

        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Errore durante la creazione della pagina: {str(e)}")

    def find_item_by_path(self, path):
        def search_tree(item):
            if item.data(0, Qt.UserRole) == path:
                return item
            for i in range(item.childCount()):
                result = search_tree(item.child(i))
                if result:
                    return result
            return None

        root = self.file_tree.topLevelItem(0)
        if root:
            return search_tree(root)
        return None

def main():
    app = QApplication(sys.argv)
    editor = HTMLEditor()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
