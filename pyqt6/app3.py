import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout
)

class UserFormApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("User Registration Form")
        self.resize(450, 250)

        # 1. Input Fields
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your full name")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")

        # 2. Buttons
        self.submit_btn = QPushButton("Submit")
        self.clear_btn = QPushButton("Clear")

        # Connect signals
        self.submit_btn.clicked.connect(self.handle_submit)
        self.clear_btn.clicked.connect(self.handle_clear)

        # 3. Status Label
        self.status_label = QLabel("")

        # --- LAYOUT MANAGEMENT ---
        # A. Grid Layout for the form fields (Row, Column)
        grid = QGridLayout()
        grid.addWidget(QLabel("Full Name:"), 0, 0)
        grid.addWidget(self.name_input, 0, 1)

        grid.addWidget(QLabel("Email:"), 1, 0)
        grid.addWidget(self.email_input, 1, 1)

        # B. Horizontal Layout for buttons (Side-by-side)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.clear_btn)

        # C. Main Vertical Layout to stack Grid -> Buttons -> Status
        main_layout = QVBoxLayout()
        main_layout.addLayout(grid)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.status_label)

        # Set central widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def handle_submit(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()

        if name and email:
            self.status_label.setText(f"Registered: {name} ({email})")
        else:
            self.status_label.setText("Please fill out both fields!")

    def handle_clear(self):
        self.name_input.clear()
        self.email_input.clear()
        self.status_label.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserFormApp()
    window.show()
    sys.exit(app.exec())