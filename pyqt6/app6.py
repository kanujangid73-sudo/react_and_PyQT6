import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QMessageBox,
    QFileDialog,
    QDialog,
    QLabel,
    QVBoxLayout,
    QPushButton
)
from PyQt6.QtGui import QAction, QKeySequence

# --- SECONDARY WINDOW (Custom About Dialog) ---
class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("About Mini Notepad")
        self.resize(300, 150)

        layout = QVBoxLayout()

        info_label = QLabel("📝 PyQt6 Mini Notepad v1.0\n\nBuilt during PyQt6 learning path.\nPowered by Python & Qt6.")
        ok_button = QPushButton("Close")
        ok_button.clicked.connect(self.accept)  # Closes the dialog

        layout.addWidget(info_label)
        layout.addWidget(ok_button)
        self.setLayout(layout)


# --- MAIN APPLICATION WINDOW ---
class AdvancedNotepadApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt6 Mini Notepad Pro")
        self.resize(650, 450)

        # 1. Main Text Area
        self.text_edit = QTextEdit()
        self.setCentralWidget(self.text_edit)

        # Listen for text typing to update live counter
        self.text_edit.textChanged.connect(self.update_status_bar)

        # 2. Status Bar
        self.statusBar().showMessage("Ready | Words: 0 | Chars: 0")

        # 3. Build Menus
        self.create_menu()

    def create_menu(self):
        menu_bar = self.menuBar()

        # --- FILE MENU ---
        file_menu = menu_bar.addMenu("&File")

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

        # --- HELP MENU ---
        help_menu = menu_bar.addMenu("&Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.open_about_dialog)
        help_menu.addAction(about_action)

    # Slot: Update Status Bar Live
    def update_status_bar(self):
        text = self.text_edit.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        self.statusBar().showMessage(f"Ready | Words: {word_count} | Chars: {char_count}")

    # Slot: Open Custom Dialog
    def open_about_dialog(self):
        dialog = AboutDialog()
        dialog.exec()  # .exec() opens window modally (blocks main window until closed)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.text_edit.setText(f.read())

    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedNotepadApp()
    window.show()
    sys.exit(app.exec())