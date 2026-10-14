import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QMessageBox,
    QFileDialog
)
from PyQt6.QtGui import QAction, QKeySequence

class NotepadApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt6 Mini Notepad")
        self.resize(600, 400)

        # 1. Main Text Area
        self.text_edit = QTextEdit()
        self.setCentralWidget(self.text_edit)

        # 2. Status Bar at the bottom
        self.statusBar().showMessage("Ready")

        # 3. Build Menu Bar
        self.create_menu()

    def create_menu(self):
        menu_bar = self.menuBar()

        # --- FILE MENU ---
        file_menu = menu_bar.addMenu("&File")

        # Open File Action
        open_action = QAction("Open...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Save File Action
        save_action = QAction("Save...", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Exit Action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def open_file(self):
        # Native OS File Dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.text_edit.setText(f.read())
            self.statusBar().showMessage(f"Opened: {file_path}")

    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            self.statusBar().showMessage(f"Saved: {file_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NotepadApp()
    window.show()
    sys.exit(app.exec())