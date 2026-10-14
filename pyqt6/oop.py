import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My PyQt6 App")
        self.setGeometry(200, 100, 400, 300) # (x, y, width, height)

        # 1. Create widgets
        self.label = QLabel("Welcome to PyQt6!", self)
        self.button = QPushButton("Click Me", self)

        # 2. Connect signal to slot
        self.button.clicked.connect(self.handle_click)

        # 3. Create layout and set central widget
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def handle_click(self):
        self.label.setText("Button clicked!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())