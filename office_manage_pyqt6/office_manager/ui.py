from __future__ import annotations

import traceback
from datetime import datetime

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from office_manager.services import OfficeService


def notify_error(parent: QWidget, error: Exception) -> None:
    if isinstance(error, (ValueError, PermissionError)):
        QMessageBox.warning(parent, "Unable to complete action", str(error))
        return
    traceback.print_exc()
    QMessageBox.critical(parent, "Unexpected error", str(error))


def text_field(password: bool = False) -> QLineEdit:
    field = QLineEdit()
    if password:
        field.setEchoMode(QLineEdit.EchoMode.Password)
    return field


def date_field(default_today: bool = False) -> QDateEdit:
    field = QDateEdit()
    field.setCalendarPopup(True)
    field.setDisplayFormat("yyyy-MM-dd")
    field.setDate(QDate.currentDate() if default_today else QDate(2000, 1, 1))
    return field


def date_text(field: QDateEdit) -> str:
    return field.date().toString("yyyy-MM-dd")


class FormDialog(QDialog):
    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        accept_label: str = "Save",
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.form = QFormLayout()
        self.content = QVBoxLayout(self)
        self.content.addLayout(self.form)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText(accept_label)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.content.addWidget(self.buttons)


class SetupDialog(FormDialog):
    def __init__(self, service: OfficeService):
        super().__init__("Create administrator account", accept_label="Create account")
        self.service = service
        self.name = text_field()
        self.username = text_field()
        self.password = text_field(password=True)
        self.confirm = text_field(password=True)
        self.form.addRow("Administrator name", self.name)
        self.form.addRow("Username", self.username)
        self.form.addRow("Password (10+ characters)", self.password)
        self.form.addRow("Confirm password", self.confirm)
        self.buttons.accepted.disconnect(self.accept)
        self.buttons.accepted.connect(self.save)

    def save(self) -> None:
        try:
            if self.password.text() != self.confirm.text():
                raise ValueError("Passwords do not match.")
            self.service.create_initial_admin(
                self.username.text(), self.password.text(), self.name.text()
            )
        except Exception as error:
            notify_error(self, error)
            return
        QMessageBox.information(
            self,
            "Setup complete",
            "Administrator account created. Sign in with your new credentials.",
        )
        self.accept()


class LoginDialog(FormDialog):
    def __init__(self, service: OfficeService):
        super().__init__("Office Manager — Sign in", accept_label="Sign in")
        self.service = service
        self.user: dict | None = None
        self.username = text_field()
        self.password = text_field(password=True)
        self.account_type = QComboBox()
        self.account_type.addItem("Employee", "employee")
        self.account_type.addItem("Intern", "intern")
        self.account_type.addItem("Manager", "manager")
        self.account_type.addItem("Administrator", "admin")
        self.form.addRow("Sign in as", self.account_type)
        self.form.addRow("Username", self.username)
        self.form.addRow("Password", self.password)
        self.password.returnPressed.connect(self.login)
        self.buttons.accepted.disconnect(self.accept)
        self.buttons.accepted.connect(self.login)
        self.register_button = QPushButton("New here? Register as an employee or intern")
        self.register_button.setObjectName("secondaryButton")
        self.register_button.clicked.connect(self.open_registration)
        self.content.addWidget(self.register_button)

    def login(self) -> None:
        try:
            self.user = self.service.login(
                self.username.text(),
                self.password.text(),
                self.account_type.currentData(),
            )
        except Exception as error:
            notify_error(self, error)
            return
        self.accept()

    def open_registration(self) -> None:
        dialog = RegistrationDialog(self.service, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.username.setText(dialog.username.text().strip())
        account_index = self.account_type.findData(dialog.employment_type.currentData())
        if account_index >= 0:
            self.account_type.setCurrentIndex(account_index)
        self.password.clear()
        QMessageBox.information(
            self,
            "Registration complete",
            "Your account has been created. Sign in with your new username and password.",
        )
        self.password.setFocus()


class RegistrationDialog(FormDialog):
    def __init__(self, service: OfficeService, parent: QWidget):
        super().__init__(
            "Employee / Intern Registration",
            parent,
            accept_label="Create account",
        )
        self.service = service
        self.name = text_field()
        self.email = text_field()
        self.department = text_field()
        self.title = text_field()
        self.username = text_field()
        self.password = text_field(password=True)
        self.confirm_password = text_field(password=True)
        self.employment_type = QComboBox()
        self.employment_type.addItem("Employee", "employee")
        self.employment_type.addItem("Intern", "intern")
        self.start_date = date_field(default_today=True)
        self.form.addRow("Register as", self.employment_type)
        self.form.addRow("Full name", self.name)
        self.form.addRow("Email", self.email)
        self.form.addRow("Department", self.department)
        self.form.addRow("Job title", self.title)
        self.form.addRow("Username (3–32 characters)", self.username)
        self.form.addRow("Password (at least 10 characters)", self.password)
        self.form.addRow("Confirm password", self.confirm_password)
        self.form.addRow("Start date", self.start_date)
        self.buttons.accepted.disconnect(self.accept)
        self.buttons.accepted.connect(self.register)

    def register(self) -> None:
        try:
            if self.password.text() != self.confirm_password.text():
                raise ValueError("Passwords do not match.")
            self.service.register_account(
                username=self.username.text(),
                password=self.password.text(),
                full_name=self.name.text(),
                email=self.email.text(),
                department=self.department.text(),
                job_title=self.title.text(),
                start_date=date_text(self.start_date),
                employment_type=self.employment_type.currentData(),
            )
        except Exception as error:
            notify_error(self, error)
            return
        self.accept()


class EmployeeDialog(FormDialog):
    def __init__(self, parent: QWidget):
        super().__init__(
            "Add employee or intern", parent, accept_label="Register staff member"
        )
        self.name = text_field()
        self.email = text_field()
        self.department = text_field()
        self.title = text_field()
        self.username = text_field()
        self.password = text_field(password=True)
        self.role = QComboBox()
        self.role.addItems(["employee", "manager"])
        self.employment_type = QComboBox()
        self.employment_type.addItems(["employee", "intern"])
        self.start_date = date_field(default_today=True)
        self.form.addRow("Full name", self.name)
        self.form.addRow("Email", self.email)
        self.form.addRow("Department", self.department)
        self.form.addRow("Job title", self.title)
        self.form.addRow("Username", self.username)
        self.form.addRow("Temporary password (10+ characters)", self.password)
        self.form.addRow("Access role", self.role)
        self.form.addRow("Employment type", self.employment_type)
        self.form.addRow("Start date", self.start_date)


class ApplicationDialog(FormDialog):
    def __init__(self, parent: QWidget):
        super().__init__("New intern application", parent, accept_label="Submit application")
        self.name = text_field()
        self.email = text_field()
        self.school = text_field()
        self.department = text_field()
        self.start_date = date_field(default_today=True)
        self.form.addRow("Full name", self.name)
        self.form.addRow("Email", self.email)
        self.form.addRow("School / institution", self.school)
        self.form.addRow("Department", self.department)
        self.form.addRow("Proposed start date", self.start_date)


class TaskDialog(FormDialog):
    def __init__(
        self, parent: QWidget, employees: list[dict], projects: list[dict]
    ):
        super().__init__("Assign a task", parent, accept_label="Assign task")
        self.title = text_field()
        self.description = QTextEdit()
        self.description.setFixedHeight(90)
        self.assignee = QComboBox()
        for employee in employees:
            label = f"{employee['full_name']} — {employee['department']}"
            self.assignee.addItem(label, employee["id"])
        self.project = QComboBox()
        self.project.addItem("No project", None)
        for project in projects:
            if project["status"] == "Active":
                self.project.addItem(project["name"], project["id"])
        self.due_date = text_field()
        self.due_date.setPlaceholderText("YYYY-MM-DD (leave empty if none)")
        self.priority = QComboBox()
        self.priority.addItems(["Low", "Medium", "High"])
        self.form.addRow("Task title", self.title)
        self.form.addRow("Description", self.description)
        self.form.addRow("Assign to", self.assignee)
        self.form.addRow("Project (optional)", self.project)
        self.form.addRow("Due date (optional)", self.due_date)
        self.form.addRow("Priority", self.priority)


class PasswordDialog(FormDialog):
    def __init__(self, parent: QWidget):
        super().__init__("Change password", parent, accept_label="Change password")
        self.current_password = text_field(password=True)
        self.new_password = text_field(password=True)
        self.confirm_password = text_field(password=True)
        self.form.addRow("Current password", self.current_password)
        self.form.addRow("New password (10+ characters)", self.new_password)
        self.form.addRow("Confirm new password", self.confirm_password)


class ProjectDialog(FormDialog):
    def __init__(self, parent: QWidget):
        super().__init__("Create project", parent, accept_label="Create project")
        self.name = text_field()
        self.description = QTextEdit()
        self.description.setFixedHeight(90)
        self.start_date = date_field(default_today=True)
        self.due_date = text_field()
        self.due_date.setPlaceholderText("YYYY-MM-DD (optional)")
        self.form.addRow("Project name", self.name)
        self.form.addRow("Description", self.description)
        self.form.addRow("Start date", self.start_date)
        self.form.addRow("Due date (optional)", self.due_date)


class LeaveRequestDialog(FormDialog):
    def __init__(self, parent: QWidget):
        super().__init__("Request leave", parent, accept_label="Submit request")
        self.leave_type = QComboBox()
        self.leave_type.addItems(["Annual", "Sick", "Personal", "Unpaid"])
        self.start_date = date_field(default_today=True)
        self.end_date = date_field(default_today=True)
        self.reason = QTextEdit()
        self.reason.setFixedHeight(85)
        self.form.addRow("Leave type", self.leave_type)
        self.form.addRow("Start date", self.start_date)
        self.form.addRow("End date", self.end_date)
        self.form.addRow("Reason", self.reason)


class AnnouncementDialog(FormDialog):
    def __init__(self, parent: QWidget):
        super().__init__("Post announcement", parent, accept_label="Post announcement")
        self.title = text_field()
        self.body = QTextEdit()
        self.body.setFixedHeight(120)
        self.audience = QComboBox()
        self.audience.addItems(["Everyone", "Employees", "Interns"])
        self.form.addRow("Title", self.title)
        self.form.addRow("Message", self.body)
        self.form.addRow("Audience", self.audience)


def make_table(headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setAlternatingRowColors(True)
    table.horizontalHeader().setStretchLastSection(True)
    return table


def fill_table(table: QTableWidget, rows: list[dict], columns: list[tuple[str, str]]) -> None:
    table.setRowCount(len(rows))
    for row_index, row in enumerate(rows):
        for column_index, (key, label) in enumerate(columns):
            value = row.get(key, "")
            if value is None:
                value = ""
            item = QTableWidgetItem(str(value))
            if column_index == 0 and "id" in row:
                item.setData(Qt.ItemDataRole.UserRole, row["id"])
            table.setItem(row_index, column_index, item)
    table.resizeColumnsToContents()


def selected_id(table: QTableWidget) -> int:
    row = table.currentRow()
    if row < 0 or table.item(row, 0) is None:
        raise ValueError("Select a row first.")
    value = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
    if value is None:
        raise ValueError("The selected row has no identifier.")
    return int(value)


class MainWindow(QMainWindow):
    def __init__(self, service: OfficeService, user: dict):
        super().__init__()
        self.service = service
        self.user = user
        self.setWindowTitle(f"Office Manager — {user['username']} ({user['role']})")
        self.resize(1180, 760)
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self._build_app_header(root_layout)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        root_layout.addWidget(self.tabs)
        self.setCentralWidget(root)
        self._build_dashboard()
        self._build_people()
        self._build_applications()
        self._build_attendance()
        self._build_tasks()
        self._build_reports()
        self._build_projects()
        self._build_leave()
        self._build_announcements()
        self.refresh_all()

    def _build_app_header(self, parent_layout: QVBoxLayout) -> None:
        header = QFrame()
        header.setObjectName("appHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 18, 28, 18)
        brand = QLabel("OM")
        brand.setObjectName("brandMark")
        title = QLabel("Office Manager")
        title.setObjectName("brandTitle")
        subtitle = QLabel("WORKSPACE")
        subtitle.setObjectName("brandSubtitle")
        identity = QVBoxLayout()
        identity.setSpacing(1)
        identity.addWidget(title)
        identity.addWidget(subtitle)
        header_layout.addWidget(brand)
        header_layout.addLayout(identity)
        header_layout.addStretch()
        self.header_user = QLabel(
            f"{self.user['username']}  ·  {self.user['role'].title()}"
        )
        self.header_user.setObjectName("userBadge")
        header_layout.addWidget(self.header_user)
        parent_layout.addWidget(header)

    def _page(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 24, 30, 26)
        layout.setSpacing(16)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)
        descriptions = {
            "Dashboard": "A clear view of your office activity and priorities.",
            "Employees": "Manage people, departments, roles, and employment details.",
            "Intern Applications": "Review candidates and keep the internship pipeline moving.",
            "Attendance": "Record shifts and breaks, then review time worked.",
            "Tasks": "Keep assignments visible, prioritized, and up to date.",
            "Reports": "Review attendance totals and export a shareable CSV report.",
            "Projects": "Track company initiatives, timelines, and project status.",
            "Leave": "Submit time-off requests and review approval decisions.",
            "Announcements": "Read company updates and important team notices.",
        }
        description = QLabel(descriptions.get(title, "Office workspace"))
        description.setObjectName("pageDescription")
        layout.addWidget(description)
        self.tabs.addTab(page, title)
        return page, layout

    def _build_dashboard(self) -> None:
        _, layout = self._page("Dashboard")
        welcome = QLabel(f"Good to see you, {self.user['username']}")
        welcome.setObjectName("welcomeTitle")
        layout.addWidget(welcome)
        self.dashboard_grid = QGridLayout()
        self.dashboard_grid.setContentsMargins(0, 4, 0, 0)
        self.dashboard_grid.setHorizontalSpacing(16)
        self.dashboard_grid.setVerticalSpacing(16)
        layout.addLayout(self.dashboard_grid)
        change_password = QPushButton("Change password")
        change_password.setObjectName("secondaryButton")
        change_password.clicked.connect(self.change_password)
        layout.addWidget(change_password, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()

    def _build_people(self) -> None:
        _, layout = self._page("Employees")
        actions = QHBoxLayout()
        refresh = QPushButton("Refresh")
        refresh.setObjectName("secondaryButton")
        refresh.clicked.connect(self.refresh_employees)
        actions.addWidget(refresh)
        if self.user["role"] == "admin":
            add = QPushButton("Add employee / intern account")
            add.setObjectName("primaryButton")
            add.clicked.connect(self.add_employee)
            actions.addWidget(add)
        actions.addStretch()
        layout.addLayout(actions)
        self.employees_table = make_table(
            ["ID", "Name", "Email", "Department", "Title", "Type", "Start date", "Username", "Role"]
        )
        layout.addWidget(self.employees_table)

    def _build_applications(self) -> None:
        _, layout = self._page("Intern Applications")
        actions = QHBoxLayout()
        if self.user["role"] in {"admin", "manager"}:
            add = QPushButton("New application")
            add.setObjectName("primaryButton")
            add.clicked.connect(self.add_application)
            actions.addWidget(add)
            self.application_status = QComboBox()
            self.application_status.addItems(
                ["Submitted", "Under Review", "Accepted", "Rejected"]
            )
            actions.addWidget(self.application_status)
            update = QPushButton("Update selected status")
            update.setObjectName("secondaryButton")
            update.clicked.connect(self.update_application)
            actions.addWidget(update)
        refresh = QPushButton("Refresh")
        refresh.setObjectName("secondaryButton")
        refresh.clicked.connect(self.refresh_applications)
        actions.addWidget(refresh)
        actions.addStretch()
        layout.addLayout(actions)
        self.applications_table = make_table(
            ["ID", "Name", "Email", "School", "Department", "Start date", "Status", "Submitted"]
        )
        layout.addWidget(self.applications_table)

    def _build_attendance(self) -> None:
        _, layout = self._page("Attendance")
        self.attendance_state = QLabel()
        self.attendance_state.setObjectName("statusBanner")
        layout.addWidget(self.attendance_state)
        actions = QHBoxLayout()
        for label, action in (
            ("Clock in", "clock_in"),
            ("Start break", "break_start"),
            ("End break", "break_end"),
            ("Clock out", "clock_out"),
        ):
            button = QPushButton(label)
            button.setObjectName(
                "primaryButton" if action == "clock_in" else "secondaryButton"
            )
            button.clicked.connect(lambda checked=False, value=action: self.attendance_action(value))
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.attendance_table: QTableWidget | None = None
        layout.addWidget(QLabel("Attendance and work-hours report"))
        self.attendance_table = make_table(
            ["ID", "Employee", "Department", "Clock in", "Clock out", "Break min", "Work hours"]
        )
        layout.addWidget(self.attendance_table)

    def _build_tasks(self) -> None:
        _, layout = self._page("Tasks")
        actions = QHBoxLayout()
        if self.user["role"] in {"admin", "manager"}:
            add = QPushButton("Assign task")
            add.setObjectName("primaryButton")
            add.clicked.connect(self.add_task)
            actions.addWidget(add)
        self.task_status = QComboBox()
        self.task_status.addItems(["To Do", "In Progress", "Blocked", "Done"])
        actions.addWidget(self.task_status)
        update = QPushButton("Update selected task")
        update.setObjectName("secondaryButton")
        update.clicked.connect(self.update_task)
        actions.addWidget(update)
        refresh = QPushButton("Refresh")
        refresh.setObjectName("secondaryButton")
        refresh.clicked.connect(self.refresh_tasks)
        actions.addWidget(refresh)
        actions.addStretch()
        layout.addLayout(actions)
        self.tasks_table = make_table(
            ["ID", "Task", "Assignee", "Project", "Due date", "Priority", "Status", "Description"]
        )
        layout.addWidget(self.tasks_table)

    def _build_reports(self) -> None:
        _, layout = self._page("Reports")
        actions = QHBoxLayout()
        refresh = QPushButton("Refresh attendance")
        refresh.setObjectName("secondaryButton")
        refresh.clicked.connect(self.refresh_reports)
        export = QPushButton("Export attendance CSV")
        export.setObjectName("primaryButton")
        export.clicked.connect(self.export_attendance)
        actions.addWidget(refresh)
        actions.addWidget(export)
        actions.addStretch()
        layout.addLayout(actions)
        self.report_table = make_table(
            ["ID", "Employee", "Department", "Clock in", "Clock out", "Break min", "Work hours"]
        )
        layout.addWidget(self.report_table)

    def _build_projects(self) -> None:
        _, layout = self._page("Projects")
        actions = QHBoxLayout()
        if self.user["role"] in {"admin", "manager"}:
            create = QPushButton("Create project")
            create.setObjectName("primaryButton")
            create.clicked.connect(self.add_project)
            actions.addWidget(create)
            self.project_status = QComboBox()
            self.project_status.addItems(["Active", "On Hold", "Completed"])
            actions.addWidget(self.project_status)
            update = QPushButton("Update selected project")
            update.setObjectName("secondaryButton")
            update.clicked.connect(self.update_project)
            actions.addWidget(update)
        refresh = QPushButton("Refresh")
        refresh.setObjectName("secondaryButton")
        refresh.clicked.connect(self.refresh_projects)
        actions.addWidget(refresh)
        actions.addStretch()
        layout.addLayout(actions)
        self.projects_table = make_table(
            ["ID", "Project", "Owner", "Status", "Start date", "Due date", "Description"]
        )
        layout.addWidget(self.projects_table)

    def _build_leave(self) -> None:
        _, layout = self._page("Leave Requests")
        actions = QHBoxLayout()
        request = QPushButton("Request leave")
        request.setObjectName("primaryButton")
        request.clicked.connect(self.add_leave_request)
        actions.addWidget(request)
        if self.user["role"] in {"admin", "manager"}:
            self.leave_status = QComboBox()
            self.leave_status.addItems(["Approved", "Rejected"])
            actions.addWidget(self.leave_status)
            review = QPushButton("Review selected request")
            review.setObjectName("secondaryButton")
            review.clicked.connect(self.review_leave_request)
            actions.addWidget(review)
        refresh = QPushButton("Refresh")
        refresh.setObjectName("secondaryButton")
        refresh.clicked.connect(self.refresh_leave_requests)
        actions.addWidget(refresh)
        actions.addStretch()
        layout.addLayout(actions)
        self.leave_table = make_table(
            ["ID", "Employee", "Department", "Type", "Start", "End", "Reason", "Status", "Reviewer"]
        )
        layout.addWidget(self.leave_table)

    def _build_announcements(self) -> None:
        _, layout = self._page("Announcements")
        actions = QHBoxLayout()
        if self.user["role"] in {"admin", "manager"}:
            post = QPushButton("Post announcement")
            post.setObjectName("primaryButton")
            post.clicked.connect(self.add_announcement)
            actions.addWidget(post)
        refresh = QPushButton("Refresh")
        refresh.setObjectName("secondaryButton")
        refresh.clicked.connect(self.refresh_announcements)
        actions.addWidget(refresh)
        actions.addStretch()
        layout.addLayout(actions)
        self.announcements_table = make_table(
            ["ID", "Title", "Audience", "Posted by", "Published", "Message"]
        )
        layout.addWidget(self.announcements_table)

    def refresh_all(self) -> None:
        self.refresh_dashboard()
        self.refresh_attendance_state()
        self.refresh_tasks()
        self.refresh_employees()
        self.refresh_applications()
        self.refresh_reports()
        self.refresh_projects()
        self.refresh_leave_requests()
        self.refresh_announcements()

    def _refresh(self, callback) -> None:
        try:
            callback()
        except Exception as error:
            notify_error(self, error)

    def refresh_dashboard(self) -> None:
        metrics = self.service.dashboard(self.user)
        while self.dashboard_grid.count():
            item = self.dashboard_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        labels = {
            "active_staff": ("Active staff", "People currently in the staff directory"),
            "open_tasks": ("Open tasks", "Assignments not yet completed"),
            "overdue_tasks": ("Overdue tasks", "Open assignments past their due date"),
            "applications_to_review": (
                "Applications to review",
                "Candidates awaiting a decision",
            ),
            "my_open_tasks": ("My open tasks", "Assignments still in progress"),
            "hours_today": ("Hours today", "Time worked, excluding recorded breaks"),
            "active_projects": ("Active projects", "Projects currently in progress"),
            "pending_leave_requests": (
                "Leave requests",
                "Requests waiting for a manager decision",
            ),
            "my_pending_leave": ("My leave requests", "Requests waiting for review"),
        }
        for index, (key, value) in enumerate(metrics.items()):
            title_text, hint_text = labels.get(
                key, (key.replace("_", " ").title(), "")
            )
            card = QFrame()
            card.setObjectName("metricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 18, 20, 18)
            card_layout.setSpacing(6)
            value_label = QLabel(str(value))
            value_label.setObjectName("metricValue")
            title_label = QLabel(title_text)
            title_label.setObjectName("metricTitle")
            hint_label = QLabel(hint_text)
            hint_label.setObjectName("metricHint")
            hint_label.setWordWrap(True)
            card_layout.addWidget(value_label)
            card_layout.addWidget(title_label)
            card_layout.addWidget(hint_label)
            self.dashboard_grid.addWidget(card, index // 2, index % 2)

    def change_password(self) -> None:
        dialog = PasswordDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            if dialog.new_password.text() != dialog.confirm_password.text():
                raise ValueError("New passwords do not match.")
            self.service.change_password(
                self.user,
                dialog.current_password.text(),
                dialog.new_password.text(),
            )
        except Exception as error:
            notify_error(self, error)
            return
        QMessageBox.information(self, "Password updated", "Your password was changed.")

    def refresh_employees(self) -> None:
        if not hasattr(self, "employees_table"):
            return
        rows = self.service.list_employees(self.user)
        fill_table(
            self.employees_table,
            rows,
            [
                ("id", "ID"),
                ("full_name", "Name"),
                ("email", "Email"),
                ("department", "Department"),
                ("job_title", "Title"),
                ("employment_type", "Type"),
                ("start_date", "Start date"),
                ("username", "Username"),
                ("role", "Role"),
            ],
        )

    def refresh_applications(self) -> None:
        rows = self.service.list_intern_applications(self.user)
        fill_table(
            self.applications_table,
            rows,
            [
                ("id", "ID"),
                ("full_name", "Name"),
                ("email", "Email"),
                ("school", "School"),
                ("department", "Department"),
                ("start_date", "Start date"),
                ("status", "Status"),
                ("created_at", "Submitted"),
            ],
        )

    def refresh_attendance_state(self) -> None:
        state = self.service.current_attendance_state(self.user)
        if state["clocked_in"]:
            clock_in = datetime.fromisoformat(state["clock_in"]).astimezone().strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )
            status = "On a break" if state["on_break"] else "Clocked in"
            visual_state = "onBreak" if state["on_break"] else "clockedIn"
            self.attendance_state.setText(f"Status: {status} — since {clock_in}")
        else:
            visual_state = "clockedOut"
            self.attendance_state.setText("Status: Not clocked in")
        self.attendance_state.setProperty("state", visual_state)
        self.attendance_state.style().unpolish(self.attendance_state)
        self.attendance_state.style().polish(self.attendance_state)

    def refresh_tasks(self) -> None:
        rows = self.service.list_tasks(self.user)
        fill_table(
            self.tasks_table,
            rows,
            [
                ("id", "ID"),
                ("title", "Task"),
                ("assignee", "Assignee"),
                ("project", "Project"),
                ("due_date", "Due date"),
                ("priority", "Priority"),
                ("status", "Status"),
                ("description", "Description"),
            ],
        )

    def refresh_reports(self) -> None:
        rows = self.service.attendance_report(self.user)
        columns = [
            ("id", "ID"),
            ("employee", "Employee"),
            ("department", "Department"),
            ("clock_in", "Clock in"),
            ("clock_out", "Clock out"),
            ("break_minutes", "Break min"),
            ("work_hours", "Work hours"),
        ]
        fill_table(self.report_table, rows, columns)
        if self.attendance_table is not None:
            fill_table(self.attendance_table, rows, columns)

    def refresh_projects(self) -> None:
        fill_table(
            self.projects_table,
            self.service.list_projects(self.user),
            [
                ("id", "ID"),
                ("name", "Project"),
                ("owner", "Owner"),
                ("status", "Status"),
                ("start_date", "Start date"),
                ("due_date", "Due date"),
                ("description", "Description"),
            ],
        )

    def refresh_leave_requests(self) -> None:
        fill_table(
            self.leave_table,
            self.service.list_leave_requests(self.user),
            [
                ("id", "ID"),
                ("employee", "Employee"),
                ("department", "Department"),
                ("leave_type", "Type"),
                ("start_date", "Start"),
                ("end_date", "End"),
                ("reason", "Reason"),
                ("status", "Status"),
                ("reviewer", "Reviewer"),
            ],
        )

    def refresh_announcements(self) -> None:
        fill_table(
            self.announcements_table,
            self.service.list_announcements(self.user),
            [
                ("id", "ID"),
                ("title", "Title"),
                ("audience", "Audience"),
                ("author", "Posted by"),
                ("publish_at", "Published"),
                ("body", "Message"),
            ],
        )

    def add_project(self) -> None:
        dialog = ProjectDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.create_project(
                self.user,
                name=dialog.name.text(),
                description=dialog.description.toPlainText(),
                start_date=date_text(dialog.start_date),
                due_date=dialog.due_date.text(),
            )
            self.refresh_projects()
            self.refresh_dashboard()
        except Exception as error:
            notify_error(self, error)

    def update_project(self) -> None:
        try:
            self.service.update_project_status(
                self.user,
                selected_id(self.projects_table),
                self.project_status.currentText(),
            )
            self.refresh_projects()
            self.refresh_dashboard()
        except Exception as error:
            notify_error(self, error)

    def add_leave_request(self) -> None:
        dialog = LeaveRequestDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.submit_leave_request(
                self.user,
                leave_type=dialog.leave_type.currentText(),
                start_date=date_text(dialog.start_date),
                end_date=date_text(dialog.end_date),
                reason=dialog.reason.toPlainText(),
            )
            self.refresh_leave_requests()
            self.refresh_dashboard()
        except Exception as error:
            notify_error(self, error)

    def review_leave_request(self) -> None:
        try:
            self.service.review_leave_request(
                self.user,
                selected_id(self.leave_table),
                self.leave_status.currentText(),
            )
            self.refresh_leave_requests()
            self.refresh_dashboard()
        except Exception as error:
            notify_error(self, error)

    def add_announcement(self) -> None:
        dialog = AnnouncementDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.create_announcement(
                self.user,
                title=dialog.title.text(),
                body=dialog.body.toPlainText(),
                audience=dialog.audience.currentText(),
            )
            self.refresh_announcements()
            self.refresh_dashboard()
        except Exception as error:
            notify_error(self, error)

    def add_employee(self) -> None:
        dialog = EmployeeDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.add_employee(
                self.user,
                username=dialog.username.text(),
                password=dialog.password.text(),
                full_name=dialog.name.text(),
                email=dialog.email.text(),
                department=dialog.department.text(),
                job_title=dialog.title.text(),
                start_date=date_text(dialog.start_date),
                role=dialog.role.currentText(),
                employment_type=dialog.employment_type.currentText(),
            )
        except Exception as error:
            notify_error(self, error)
            return
        self.refresh_all()

    def add_application(self) -> None:
        dialog = ApplicationDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.add_intern_application(
                self.user,
                full_name=dialog.name.text(),
                email=dialog.email.text(),
                school=dialog.school.text(),
                department=dialog.department.text(),
                start_date=date_text(dialog.start_date),
            )
        except Exception as error:
            notify_error(self, error)
            return
        self.refresh_applications()
        self.refresh_dashboard()

    def update_application(self) -> None:
        try:
            self.service.update_application_status(
                self.user,
                selected_id(self.applications_table),
                self.application_status.currentText(),
            )
            self.refresh_applications()
            self.refresh_dashboard()
        except Exception as error:
            notify_error(self, error)

    def attendance_action(self, action: str) -> None:
        try:
            self.service.attendance_action(self.user, action)
            self.refresh_attendance_state()
            self.refresh_dashboard()
            self.refresh_reports()
        except Exception as error:
            notify_error(self, error)

    def add_task(self) -> None:
        try:
            employees = [
                employee
                for employee in self.service.list_employees(self.user)
                if employee["is_active"]
            ]
            if not employees:
                raise ValueError("Add an active employee before assigning a task.")
            dialog = TaskDialog(
                self, employees, self.service.list_projects(self.user)
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            self.service.create_task(
                self.user,
                title=dialog.title.text(),
                description=dialog.description.toPlainText(),
                assigned_to=int(dialog.assignee.currentData()),
                due_date=dialog.due_date.text(),
                priority=dialog.priority.currentText(),
                project_id=dialog.project.currentData(),
            )
            self.refresh_all()
        except Exception as error:
            notify_error(self, error)

    def update_task(self) -> None:
        try:
            self.service.update_task_status(
                self.user, selected_id(self.tasks_table), self.task_status.currentText()
            )
            self.refresh_all()
        except Exception as error:
            notify_error(self, error)

    def export_attendance(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export attendance", "attendance.csv", "CSV files (*.csv)"
        )
        if not path:
            return
        try:
            count = self.service.export_attendance_csv(self.user, path)
        except Exception as error:
            notify_error(self, error)
            return
        QMessageBox.information(self, "Export complete", f"Exported {count} attendance rows.")
