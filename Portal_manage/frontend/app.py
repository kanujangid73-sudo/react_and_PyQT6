import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QMessageBox, QLabel, QStackedWidget
)

BASE_URL = "http://127.0.0.1:8000"

class AttendanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.access_token = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Employee Portal MVP")
        self.setGeometry(100, 100, 500, 300)

        self.stacked_widget = QStackedWidget(self)

        # Build Screen 1: Login / Register Page
        self.auth_screen = QWidget()
        auth_layout = QVBoxLayout()
        
        self.title_label = QLabel("Portal Login", self)
        auth_layout.addWidget(self.title_label)

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Username")
        auth_layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        auth_layout.addWidget(self.password_input)

        auth_btn_layout = QHBoxLayout()
        self.login_btn = QPushButton("Login", self)
        self.login_btn.clicked.connect(self.handle_login)
        auth_btn_layout.addWidget(self.login_btn)

        self.register_btn = QPushButton("Register", self)
        self.register_btn.clicked.connect(self.handle_register)
        auth_btn_layout.addWidget(self.register_btn)

        auth_layout.addLayout(auth_btn_layout)
        self.auth_screen.setLayout(auth_layout)

        # Build Screen 2: Attendance Clock-In Terminal Page
        self.terminal_screen = QWidget()
        term_layout = QVBoxLayout()

        self.term_label = QLabel("Employee Terminal", self)
        term_layout.addWidget(self.term_label)

        self.emp_id_input = QLineEdit(self)
        self.emp_id_input.setPlaceholderText("Enter Employee ID (e.g., 101)")
        term_layout.addWidget(self.emp_id_input)

        action_btn_layout = QHBoxLayout()
        self.clock_in_btn = QPushButton("Clock IN", self)
        self.clock_in_btn.clicked.connect(lambda: self.handle_clock_action("clock-in"))
        action_btn_layout.addWidget(self.clock_in_btn)

        self.clock_out_btn = QPushButton("Clock OUT", self)
        self.clock_out_btn.clicked.connect(lambda: self.handle_clock_action("clock-out"))
        action_btn_layout.addWidget(self.clock_out_btn)

        term_layout.addLayout(action_btn_layout)
        self.terminal_screen.setLayout(term_layout)

        # Add Screens to Stack
        self.stacked_widget.addWidget(self.auth_screen)
        self.stacked_widget.addWidget(self.terminal_screen)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

    def handle_register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return

        try:
            res = requests.post(
                f"{BASE_URL}/register",
                json={"username": username, "password": password, "role": "admin"}
            )
            if res.status_code == 201:
                QMessageBox.information(self, "Success", "Registered successfully! Click Login now.")
            else:
                QMessageBox.warning(self, "Failed", res.json().get("detail", "Registration failed"))
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Could not connect to backend server:\n{e}")

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return

        try:
            res = requests.post(
                f"{BASE_URL}/token",
                data={"username": username, "password": password}
            )
            if res.status_code == 200:
                self.access_token = res.json()["access_token"]
                QMessageBox.information(self, "Success", "Authenticated successfully!")
                self.stacked_widget.setCurrentIndex(1)  # Switch to Terminal screen
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid credentials")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Could not connect to backend server:\n{e}")

    def handle_clock_action(self, endpoint):
        emp_id = self.emp_id_input.text().strip()

        if not emp_id:
            QMessageBox.warning(self, "Error", "Please enter an Employee ID")
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            res = requests.post(
                f"{BASE_URL}/{endpoint}",
                json={"employee_id": emp_id},
                headers=headers
            )
            if res.status_code == 200:
                msg = res.json().get("message", "Success")
                QMessageBox.information(self, "Success", msg)
            else:
                detail = res.json().get("detail", "Request failed")
                QMessageBox.warning(self, "Error", detail)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Connection error:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AttendanceApp()
    window.show()
    sys.exit(app.exec())