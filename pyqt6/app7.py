import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QFileDialog,
    QTabWidget,
    QMessageBox,
    QWidget,
    QVBoxLayout
)
from PyQt6.QtGui import QAction, QKeySequence

class TabbedNotepadApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt6 Tabbed Notepad Pro")
        self.resize(750, 500)

        # 1. Main Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        # Track Dark Mode State
        self.is_dark_mode = False

        # 2. Status Bar
        self.statusBar().showMessage("Ready")

        # 3. Create First Tab & Menus
        self.add_new_tab("Untitled 1")
        self.create_menu()

    def add_new_tab(self, title="Untitled"):
        # Each tab contains a QTextEdit widget
        text_edit = QTextEdit()
        
        # Connect text change signal to update live status
        text_edit.textChanged.connect(self.update_status_bar)

        index = self.tabs.addTab(text_edit, title)
        self.tabs.setCurrentIndex(index)

    def close_tab(self, index):
        # Keep at least one tab open
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            QMessageBox.information(self, "Notepad", "Cannot close the last tab!")

    def current_text_edit(self) -> QTextEdit:
        # Helper to get the active tab's QTextEdit
        return self.tabs.currentWidget()

    def create_menu(self):
        menu_bar = self.menuBar()

        # --- FILE MENU ---
        file_menu = menu_bar.addMenu("&File")

        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut(QKeySequence("Ctrl+N"))
        new_tab_action.triggered.connect(lambda: self.add_new_tab())
        file_menu.addAction(new_tab_action)

        open_action = QAction("Open...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save...", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # --- VIEW MENU ---
        view_menu = menu_bar.addMenu("&View")

        toggle_theme_action = QAction("Toggle Dark/Light Mode", self)
        toggle_theme_action.setShortcut(QKeySequence("Ctrl+T"))
        toggle_theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(toggle_theme_action)

    def update_status_bar(self):
        active_editor = self.current_text_edit()
        if active_editor:
            text = active_editor.toPlainText()
            char_count = len(text)
            word_count = len(text.split()) if text.strip() else 0
            self.statusBar().showMessage(f"Words: {word_count} | Chars: {char_count}")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract filename from path
            file_name = file_path.split("/")[-1]
            
            # Add tab with content
            self.add_new_tab(file_name)
            self.current_text_edit().setText(content)

    def save_file(self):
        active_editor = self.current_text_edit()
        if not active_editor:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(active_editor.toPlainText())

            # Update tab title to match saved filename
            file_name = file_path.split("/")[-1]
            current_index = self.tabs.currentIndex()
            self.tabs.setTabText(current_index, file_name)

    def toggle_theme(self):
        if not self.is_dark_mode:
            # Apply Dark Theme
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
                QTabWidget::pane {
                    border: 1px solid #333333;
                }
                QTabBar::tab {
                    background-color: #2d2d2d;
                    color: #cccccc;
                    padding: 8px 16px;
                    border: 1px solid #333333;
                }
                QTabBar::tab:selected {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border-bottom: 2px solid #007acc;
                }
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: none;
                    font-family: 'Consolas', monospace;
                    font-size: 14px;
                }
                QMenuBar, QMenu {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QMenu::item:selected {
                    background-color: #007acc;
                }
            """)
            self.is_dark_mode = True
        else:
            # Reset to Light/Default Theme
            self.setStyleSheet("")
            self.is_dark_mode = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TabbedNotepadApp()
    window.show()
    sys.exit(app.exec())