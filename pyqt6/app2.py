import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout
)

class GreetingApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set main window properties
        self.setWindowTitle("Interactive Greeting App")
        self.resize(400, 200)

        # 1. Create Widgets
        self.instruction_label = QLabel("Enter your name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Preeti")
        
        self.greet_button = QPushButton("Say Hello!")
        self.result_label = QLabel("")

        # 2. Connect Button Click to Slot Function
        self.greet_button.clicked.connect(self.display_greeting)

        # 3. Create Layout and Add Widgets
        layout = QVBoxLayout()
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.greet_button)
        layout.addWidget(self.result_label)

        # 4. Set Central Widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # 5. Define Slot Function
    def display_greeting(self):
        user_name = self.name_input.text().strip()
        if user_name:
            self.result_label.setText(f"Hello, {user_name}! Welcome to PyQt6 🚀")
        else:
            self.result_label.setText("Please enter your name first!")

# Application Entry Point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GreetingApp()
    window.show()
    sys.exit(app.exec())