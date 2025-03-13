import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QTreeWidget, 
                            QTreeWidgetItem, QSplitter, QWidget, QVBoxLayout, 
                            QAction, QMenu, QHBoxLayout, QFileDialog, QMessageBox,
                            QToolBar, QPushButton, QLabel, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class HTMLEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project_path = None
        self.current_file = None
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
        
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel("Project Files")
        self.file_tree.itemDoubleClicked.connect(self.open_file)
        self.file_tree.itemClicked.connect(self.update_breadcrumbs)
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.file_tree.setExpandsOnDoubleClick(False)
        self.file_tree.itemChanged.connect(self.rename_item)
        
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
        self.show()

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
        
        if not path_parts:
            path_parts = [self.file_tree.topLevelItem(0)]
        
        for i, part in enumerate(path_parts):
            btn = QPushButton(part.text(0))
            btn.setFlat(True)
            btn.clicked.connect(lambda checked, item=part: self.file_tree.setCurrentItem(item))
            self.breadcrumb_bar.addWidget(btn)
            if i < len(path_parts) - 1:
                self.breadcrumb_bar.addWidget(QLabel(">"))

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

            css_folder_path = os.path.join(script_folder_path, "Css")
            os.makedirs(css_folder_path, exist_ok=True)
            style_file_path = os.path.join(css_folder_path, "style.css")
            with open(style_file_path, "w") as f:
                f.write("/* CSS File */\n")

            js_folder_path = os.path.join(script_folder_path, "Js")
            os.makedirs(js_folder_path, exist_ok=True)
            script_file_path = os.path.join(js_folder_path, "script.js")
            with open(script_file_path, "w") as f:
                f.write("// JavaScript File\n")

            html_folder_path = os.path.join(script_folder_path, "Html")
            os.makedirs(html_folder_path, exist_ok=True)
            index_file_path = os.path.join(html_folder_path, "index.html")
            with open(index_file_path, "w") as f:
                f.write("<html>\n<head>\n</head>\n<body>\n</body>\n</html>")

            assets_folder_path = os.path.join(self.project_path, "Assets")
            os.makedirs(assets_folder_path, exist_ok=True)

            self.file_tree.clear()
            self.load_project_structure(self.project_path)
            self.update_breadcrumbs(self.file_tree.topLevelItem(0))
            self.statusBar().showMessage(f'Nuovo progetto creato in {self.project_path}', 2000)

        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Errore durante la creazione del progetto: {str(e)}")
            self.project_path = None

    def openProject(self):
        default_path = os.getcwd()
        folder = QFileDialog.getExistingDirectory(self, "Seleziona cartella progetto", default_path)
        if folder:
            self.project_path = folder
            self.file_tree.clear()
            self.load_project_structure(self.project_path)
            self.update_breadcrumbs(self.file_tree.topLevelItem(0))
            self.statusBar().showMessage(f'Progetto aperto: {self.project_path}', 2000)

    def load_project_structure(self, path, parent=None):
        if parent is None:
            root = QTreeWidgetItem(self.file_tree, [os.path.basename(path)])
            root.setIcon(0, QIcon("icons/folder.png"))
            root.setFlags(root.flags() | Qt.ItemIsEditable)
            root.setData(0, Qt.UserRole, path)
            parent = root
        
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                folder_item = QTreeWidgetItem(parent, [item])
                folder_item.setIcon(0, QIcon("icons/folder.png"))
                folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
                folder_item.setData(0, Qt.UserRole, item_path)
                self.load_project_structure(item_path, folder_item)
            elif not item.startswith('.'):
                file_item = QTreeWidgetItem(parent, [item])
                file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
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
        if not item:
            return
            
        menu = QMenu()
        if self.is_folder(item):
            add_file = menu.addAction("Aggiungi File")
            add_folder = menu.addAction("Aggiungi Cartella")
            rename_act = menu.addAction("Rinomina")
            delete_act = menu.addAction("Elimina")
        else:
            rename_act = menu.addAction("Rinomina")
            delete_act = menu.addAction("Elimina")
        
        action = menu.exec_(self.file_tree.viewport().mapToGlobal(position))
        
        if action:
            if action.text() == "Aggiungi File":
                self.addFile(item)
            elif action.text() == "Aggiungi Cartella":
                self.addFolder(item)
            elif action.text() == "Rinomina":
                self.file_tree.editItem(item, 0)
            elif action.text() == "Elimina":
                self.delete_item(item)

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
        
        # Step 1: Create the sample file in the filesystem
        default_name = "new_file.html"
        file_path = os.path.join(parent_path, default_name)
        with open(file_path, "w") as f:
            f.write("")
        
        # Step 2: Add it to the tree
        new_file = QTreeWidgetItem(parent_item, [default_name])
        new_file.setFlags(new_file.flags() | Qt.ItemIsEditable)
        new_file.setData(0, Qt.UserRole, file_path)
        self.update_file_icon(new_file)
        
        # Step 3: Expand parent and allow renaming
        self.update_breadcrumbs(new_file)
        parent_item.setExpanded(True)
        self.file_tree.setCurrentItem(new_file)
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
        new_folder.setFlags(new_folder.flags() | Qt.ItemIsEditable)
        folder_path = os.path.join(parent_path, "New Folder")
        new_folder.setData(0, Qt.UserRole, folder_path)
        self.update_file_icon(new_folder)
        
        os.makedirs(folder_path, exist_ok=True)
        self.update_breadcrumbs(new_folder)
        parent_item.setExpanded(True)
        
        self.file_tree.setCurrentItem(new_folder)
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
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                self.file_tree.takeTopLevelItem(self.file_tree.indexOfTopLevelItem(item))
                self.project_path = None
            self.statusBar().showMessage(f"Eliminato: {item_path}", 2000)
        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Impossibile eliminare: {str(e)}")

    def open_file(self, item, column):
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            self.current_file = file_path
            with open(file_path, "r") as f:
                self.code_view.setText(f.read())
            self.update_breadcrumbs(item)
            self.statusBar().showMessage(f'Aperto: {file_path}', 2000)

    def save_current_file(self):
        if self.current_file and os.path.isfile(self.current_file):
            with open(self.current_file, "w") as f:
                f.write(self.code_view.toPlainText())
            self.statusBar().showMessage(f'Salvato: {self.current_file}', 1000)

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
            if self.current_file == old_path:
                self.current_file = new_path
            self.update_breadcrumbs(item)
            self.statusBar().showMessage(f"Rinominato: {old_path} -> {new_path}", 2000)
        except PermissionError:
            QMessageBox.warning(self, "Errore", f"Accesso negato: non è possibile rinominare '{old_path}'. Assicurati che il file o la cartella non sia in uso.")
            item.setText(column, os.path.basename(old_path))
        except OSError as e:
            QMessageBox.warning(self, "Errore", f"Errore durante la rinomina: {str(e)}")
            item.setText(column, os.path.basename(old_path))

def main():
    app = QApplication(sys.argv)
    editor = HTMLEditor()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
