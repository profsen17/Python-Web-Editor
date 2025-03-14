import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QTreeWidget, 
                            QTreeWidgetItem, QSplitter, QWidget, QVBoxLayout, 
                            QAction, QMenu, QHBoxLayout, QFileDialog, QMessageBox,
                            QToolBar, QPushButton, QLabel, QInputDialog, QLineEdit)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QTextDocument, QColor
from fuzzywuzzy import fuzz  # Import fuzzywuzzy for fuzzy matching

class HTMLEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project_path = None
        self.current_file = None
        self.file_histories = {}
        self.expanded_state = {}
        self.is_dark_mode = False
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
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Cerca file...")
        self.search_bar.textChanged.connect(self.filter_files)
        self.search_bar.setVisible(False)
        sidebar_layout.addWidget(self.search_bar)
        
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
        
        sidebar_layout.addWidget(self.file_tree)
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setMinimumWidth(200)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        content_splitter = QSplitter(Qt.Vertical)
        
        self.design_view = QTextEdit()
        self.design_view.setPlaceholderText("Design View (da implementare)")
        self.design_view.setMinimumHeight(300)
        
        self.code_view = QTextEdit()
        self.code_view.setPlaceholderText("Code View")
        self.code_view.textChanged.connect(self.save_current_file)
        
        content_splitter.addWidget(self.design_view)
        content_splitter.addWidget(self.code_view)
        
        right_layout.addWidget(content_splitter)
        right_widget.setLayout(right_layout)

        main_splitter.addWidget(sidebar_widget)
        main_splitter.addWidget(right_widget)
        
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
                QTextEdit { 
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
                    padding: 5px;        /* Added padding for better spacing */
                }
                QMenu::item { 
                    padding: 5px 25px 5px 25px;  /* Adjusted padding for icons */
                }
                QMenu::item:selected { 
                    background-color: #5a5a5a; 
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
                QTextEdit { 
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
                    border-radius: 10px;  /* Changed from 5px to 10px */
                    padding: 5px;        /* Added padding for better spacing */
                }
                QMenu::item { 
                    padding: 5px 25px 5px 25px;  /* Adjusted padding for icons */
                }
                QMenu::item:selected { 
                    background-color: #d0d0d0; 
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
        
        if not search_text:
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

            script_folder_path = os.path.join(self.project_path, "Script")
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
            self.update_breadcrumbs(self.file_tree.topLevelItem(0))
            self.statusBar().showMessage(f'Nuovo progetto creato in {self.project_path}', 2000)

        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Errore durante la creazione del progetto: {str(e)}")
            self.project_path = None
            self.search_bar.setVisible(False)

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
            self.update_breadcrumbs(self.file_tree.topLevelItem(0))
            self.statusBar().showMessage(f'Progetto aperto: {self.project_path}', 2000)
        else:
            self.search_bar.setVisible(False)

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
            self.statusBar().showMessage(f"Eliminato: {item_path}", 2000)
        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Impossibile eliminare: {str(e)}")

    def handle_item_clicked(self, item, column):
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            self.current_file = file_path
            if file_path not in self.file_histories:
                self.file_histories[file_path] = QTextDocument()
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.file_histories[file_path].setPlainText(f.read())
                except Exception as e:
                    QMessageBox.warning(self, "Errore", f"Impossibile aprire il file: {str(e)}")
                    return
            self.code_view.setDocument(self.file_histories[file_path])
            self.statusBar().showMessage(f'Aperto: {file_path}', 2000)
        self.update_breadcrumbs(item)

    def save_current_file(self):
        if self.current_file and os.path.isfile(self.current_file):
            content = self.file_histories[self.current_file].toPlainText()
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
                    self.code_view.setDocument(self.file_histories[new_path])
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

def main():
    app = QApplication(sys.argv)
    editor = HTMLEditor()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
