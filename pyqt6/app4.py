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
    QVBoxLayout,
    QMessageBox
)

class StyledRegistrationForm(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("User Registration Form")
        self.resize(450, 280)

        # 1. Inputs
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your full name")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")

        # 2. Buttons
        self.submit_btn = QPushButton("Submit")
        self.clear_btn = QPushButton("Clear")

        # Set Object Names for specific CSS targeting
        self.submit_btn.setObjectName("submitBtn")
        self.clear_btn.setObjectName("clearBtn")

        # Connect button signals
        self.submit_btn.clicked.connect(self.handle_submit)
        self.clear_btn.clicked.connect(self.handle_clear)

        # --- LAYOUT MANAGEMENT ---
        grid = QGridLayout()
        grid.addWidget(QLabel("Full Name:"), 0, 0)
        grid.addWidget(self.name_input, 0, 1)

        grid.addWidget(QLabel("Email:"), 1, 0)
        grid.addWidget(self.email_input, 1, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.clear_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(grid)
        main_layout.addLayout(btn_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 3. Apply Custom Stylesheet (QSS)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f9;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
                color: #333333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
            }
            QPushButton#submitBtn {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
                border: none;
            }
            QPushButton#submitBtn:hover {
                background-color: #0056b3;
            }
            QPushButton#clearBtn {
                background-color: #6c757d;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
                border: none;
            }
            QPushButton#clearBtn:hover {
                background-color: #5a6268;
            }
        """)

    def handle_submit(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()

        if name and email:
            QMessageBox.information(
                self,
                "Success",
                f"Registration Successful!\n\nName: {name}\nEmail: {email}"
            )
        else:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please fill in both Full Name and Email before submitting!"
            )

    def handle_clear(self):
        self.name_input.clear()
        self.email_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StyledRegistrationForm()
    window.show()
    sys.exit(app.exec())