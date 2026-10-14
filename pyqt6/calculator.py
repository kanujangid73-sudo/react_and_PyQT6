import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLineEdit,
    QVBoxLayout,
    QMainWindow,
    QGridLayout,
    QPushButton
)

class CalcualtorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window properties
        self.setWindowTitle("Simple Calculator")
        self.resize(400, 200)

        # Main Layout & Display Screen
        main_layout = QVBoxLayout()
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        main_layout.addWidget(self.display)

        # Keypad Grid Layout
        buttons = [
            ['7', '8', '9', '/'],
            ['4', '5', '6', '*'],
            ['1', '2', '3', '-'],
            ['0', 'C', '=', '+']
        ]

        grid_layout = QGridLayout()
        for row_idx, row in enumerate(buttons):
            for col_idx, text in enumerate(row):
                btn = QPushButton(text)
                # Connected to on_button_click
                btn.clicked.connect(lambda checked, ch=text: self.on_button_click(ch))
                if text == '=':
                    btn.setStyleSheet("background-color: #89b4fa; color: #11111b;")
                elif text == 'C':
                    btn.setStyleSheet("background-color: #f38ba8; color: #11111b;")
                elif text in ['/', '*', '-', '+']:
                    btn.setStyleSheet("background-color: #fab387; color: #11111b;")

                grid_layout.addWidget(btn, row_idx, col_idx)

        main_layout.addLayout(grid_layout)

        # Central Container
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.apply_styles()

    # Separate method under class (not inside __init__)
    

    def apply_styles(self):
         self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e2e;
                }
                QLineEdit {
                    background-color: #181825;
                    color: #cdd6f4;
                    font-size: 28px;
                    font-weight: bold;
                    border: 2px solid #313244;
                    border-radius: 8px; 
                    padding: 10px;
                    margin-bottom: 10px;
                }
                QPushButton {
                    background-color: #313244;
                    color: #cdd6f4;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 15px;
                }
                QPushButton:hover {
                    background-color: #45475a;
                }
                QPushButton:pressed {
                    background-color: #585b70;
                }
            """)
    def on_button_click(self, ch):
            if ch == 'C':
                self.display.setText('')
            elif ch == '=':
                try:
                    result = eval(self.display.text())
                    self.display.setText(str(result))
                except Exception:
                    self.display.setText('Error')
            else:
                self.display.setText(self.display.text() + ch)


    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()

        # Keyboard shortcuts
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.on_button_click('=')
        elif key == Qt.Key.Key_Escape:
            self.on_button_click('C')
        elif key == Qt.Key.Key_Backspace:
            current = self.display.text()
            self.display.setText(current[:-1])
        elif text in '0123456789+-*/':
            self.on_button_click(text)
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalcualtorApp()
    window.show()
    sys.exit(app.exec())