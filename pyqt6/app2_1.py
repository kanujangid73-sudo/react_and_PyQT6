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

def display_greeting():
    user_name = name_input.text().strip()
    if user_name:
        result_label.setText(f"Hello, {user_name}! Welcome to PyQt6 🚀")
    else:
        result_label.setText("Please enter your name first!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Interactive Greeting App")
    window.resize(400, 200)

    # 1. Create Widgets
    instruction_label = QLabel("Enter your name:")
    name_input = QLineEdit()
    name_input.setPlaceholderText("e.g. Preeti")

    greet_button = QPushButton("Say Hello!")
    result_label = QLabel("")

    # 2. Connect Button Click to Slot Function
    greet_button.clicked.connect(display_greeting)

    # 3. Create Layout and Add Widgets
    layout = QVBoxLayout()
    layout.addWidget(instruction_label)
    layout.addWidget(name_input)
    layout.addWidget(greet_button)
    layout.addWidget(result_label)

    # 4. Set Central Widget
    container = QWidget()
    container.setLayout(layout)
    window.setCentralWidget(container)

    # Show window & run application
    window.show()
    sys.exit(app.exec())