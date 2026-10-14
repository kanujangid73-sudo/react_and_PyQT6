from __future__ import annotations

import csv
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path

from office_manager.database import Database
from office_manager.security import hash_password, verify_password

ROLES = {"admin", "manager", "employee"}
TASK_STATUSES = {"To Do", "In Progress", "Blocked", "Done"}
PRIORITIES = {"Low", "Medium", "High"}
APPLICATION_STATUSES = {"Submitted", "Under Review", "Accepted", "Rejected"}
PROJECT_STATUSES = {"Active", "On Hold", "Completed"}
LEAVE_TYPES = {"Annual", "Sick", "Personal", "Unpaid"}
LEAVE_STATUSES = {"Pending", "Approved", "Rejected"}
ANNOUNCEMENT_AUDIENCES = {"Everyone", "Employees", "Interns"}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _required(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required.")
    return normalized


def _validate_username(username: str) -> str:
    value = _required(username, "Username")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", value):
        raise ValueError(
            "Username must be 3–32 characters using letters, numbers, dots, "
            "underscores, or hyphens."
        )
    return value


def _validate_email(email: str) -> str:
    value = _required(email, "Email")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        raise ValueError("Enter a valid email address.")
    return value


def _validate_date(value: str, label: str, optional: bool = False) -> str | None:
    normalized = value.strip()
    if optional and not normalized:
        return None
    try:
        date.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"{label} must use YYYY-MM-DD format.") from error
    return normalized


class OfficeService:
    def __init__(self, database: Database):
        self.database = database

    def create_initial_admin(
        self, username: str, password: str, full_name: str
    ) -> int:
        username = _validate_username(username)
        full_name = _required(full_name, "Full name")
        if len(password) < 10:
            raise ValueError("Password must be at least 10 characters.")
        timestamp = now_iso()
        try:
            with self.database.connect() as connection:
                if connection.execute("SELECT 1 FROM users LIMIT 1").fetchone():
                    raise ValueError("Initial setup has already been completed.")
                cursor = connection.execute(
                    "INSERT INTO users(username, password_hash, role, created_at) "
                    "VALUES (?, ?, 'admin', ?)",
                    (username, hash_password(password), timestamp),
                )
                connection.execute(
                    """INSERT INTO employees
                       (user_id, full_name, email, department, job_title,
                        employment_type, start_date, created_at)
                       VALUES (?, ?, ?, 'Administration', 'Administrator',
                               'employee', ?, ?)""",
                    (
                        cursor.lastrowid,
                        full_name,
                        f"{username}@local.invalid",
                        date.today().isoformat(),
                        timestamp,
                    ),
                )
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            raise ValueError("That username is already in use.") from error

    def login(
        self, username: str, password: str, account_type: str | None = None
    ) -> dict:
        with self.database.connect() as connection:
            user = connection.execute(
                """SELECT u.id, u.username, u.password_hash, u.role, u.is_active,
                          e.employment_type
                   FROM users u LEFT JOIN employees e ON e.user_id = u.id
                   WHERE u.username = ? COLLATE NOCASE""",
                (username.strip(),),
            ).fetchone()
        if (
            user is None
            or not user["is_active"]
            or not verify_password(password, user["password_hash"])
        ):
            raise ValueError("Invalid username, password, or selected account type.")
        if account_type is not None:
            if account_type in {"employee", "intern"}:
                matches_type = (
                    user["role"] == "employee"
                    and user["employment_type"] == account_type
                )
            elif account_type in {"admin", "manager"}:
                matches_type = user["role"] == account_type
            else:
                raise ValueError("Select a valid account type.")
            if not matches_type:
                raise ValueError(
                    "This account does not match the selected sign-in type."
                )
        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "employment_type": user["employment_type"],
        }

    def register_account(
        self,
        *,
        username: str,
        password: str,
        full_name: str,
        email: str,
        department: str,
        job_title: str,
        start_date: str,
        employment_type: str,
    ) -> int:
        username = _validate_username(username)
        full_name = _required(full_name, "Full name")
        email = _validate_email(email)
        department = _required(department, "Department")
        job_title = _required(job_title, "Job title")
        start_date = _validate_date(start_date, "Start date") or ""
        if len(password) < 10:
            raise ValueError("Password must be at least 10 characters.")
        if employment_type not in {"employee", "intern"}:
            raise ValueError("Choose Employee or Intern as the account type.")
        timestamp = now_iso()
        try:
            with self.database.connect() as connection:
                cursor = connection.execute(
                    """INSERT INTO users(username, password_hash, role, created_at)
                       VALUES (?, ?, 'employee', ?)""",
                    (username, hash_password(password), timestamp),
                )
                employee_cursor = connection.execute(
                    """INSERT INTO employees
                       (user_id, full_name, email, department, job_title,
                        employment_type, start_date, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        cursor.lastrowid,
                        full_name,
                        email,
                        department,
                        job_title,
                        employment_type,
                        start_date,
                        timestamp,
                    ),
                )
                return int(employee_cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            raise ValueError(
                "That username or email is already registered. Try signing in "
                "or use different details."
            ) from error

    def change_password(
        self, actor: dict, current_password: str, new_password: str
    ) -> None:
        if actor.get("role") not in ROLES:
            raise PermissionError("Sign in before changing your password.")
        if len(new_password) < 10:
            raise ValueError("New password must be at least 10 characters.")
        with self.database.connect() as connection:
            user = connection.execute(
                "SELECT password_hash FROM users WHERE id = ? AND is_active = 1",
                (actor["id"],),
            ).fetchone()
            if user is None or not verify_password(
                current_password, user["password_hash"]
            ):
                raise ValueError("Current password is incorrect.")
            connection.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(new_password), actor["id"]),
            )

    @staticmethod
    def _require_role(user: dict, *roles: str) -> None:
        if user.get("role") not in roles:
            raise PermissionError("Your account is not allowed to do that.")

    def create_project(
        self,
        actor: dict,
        *,
        name: str,
        description: str,
        start_date: str,
        due_date: str,
    ) -> int:
        self._require_role(actor, "admin", "manager")
        name = _required(name, "Project name")
        start_date = _validate_date(start_date, "Start date") or ""
        due_date = _validate_date(due_date, "Due date", optional=True)
        if due_date and due_date < start_date:
            raise ValueError("Due date cannot be earlier than the project start date.")
        timestamp = now_iso()
        with self.database.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO projects
                   (name, description, owner_id, start_date, due_date,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    name,
                    description.strip(),
                    actor["id"],
                    start_date,
                    due_date,
                    timestamp,
                    timestamp,
                ),
            )
            return int(cursor.lastrowid)

    def list_projects(self, actor: dict) -> list[dict]:
        if actor.get("role") not in ROLES:
            raise PermissionError("Sign in before viewing projects.")
        with self.database.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    """SELECT p.id, p.name, p.description, p.status, p.start_date,
                              p.due_date, u.username AS owner
                       FROM projects p JOIN users u ON u.id = p.owner_id
                       ORDER BY CASE p.status WHEN 'Active' THEN 0
                                             WHEN 'On Hold' THEN 1 ELSE 2 END,
                                p.due_date IS NULL, p.due_date, p.name"""
                )
            ]

    def update_project_status(
        self, actor: dict, project_id: int, status: str
    ) -> None:
        self._require_role(actor, "admin", "manager")
        if status not in PROJECT_STATUSES:
            raise ValueError("Select a valid project status.")
        with self.database.connect() as connection:
            result = connection.execute(
                "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
                (status, now_iso(), project_id),
            )
            if result.rowcount != 1:
                raise ValueError("Project was not found.")

    def submit_leave_request(
        self,
        actor: dict,
        *,
        leave_type: str,
        start_date: str,
        end_date: str,
        reason: str,
    ) -> int:
        if actor.get("role") not in ROLES:
            raise PermissionError("Sign in before requesting leave.")
        if leave_type not in LEAVE_TYPES:
            raise ValueError("Select a valid leave type.")
        start_date = _validate_date(start_date, "Leave start date") or ""
        end_date = _validate_date(end_date, "Leave end date") or ""
        if end_date < start_date:
            raise ValueError("Leave end date cannot be before the start date.")
        reason = _required(reason, "Reason")
        timestamp = now_iso()
        with self.database.connect() as connection:
            employee_id = self._employee_id(connection, actor["id"])
            overlap = connection.execute(
                """SELECT 1 FROM leave_requests
                   WHERE employee_id = ?
                     AND status IN ('Pending', 'Approved')
                     AND start_date <= ? AND end_date >= ?
                   LIMIT 1""",
                (employee_id, end_date, start_date),
            ).fetchone()
            if overlap:
                raise ValueError(
                    "This request overlaps an existing pending or approved leave request."
                )
            cursor = connection.execute(
                """INSERT INTO leave_requests
                   (employee_id, leave_type, start_date, end_date, reason,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    employee_id,
                    leave_type,
                    start_date,
                    end_date,
                    reason,
                    timestamp,
                    timestamp,
                ),
            )
            return int(cursor.lastrowid)

    def list_leave_requests(self, actor: dict) -> list[dict]:
        if actor.get("role") not in ROLES:
            raise PermissionError("Sign in before viewing leave requests.")
        with self.database.connect() as connection:
            query = """SELECT l.id, e.full_name AS employee, e.department,
                              l.leave_type, l.start_date, l.end_date, l.reason,
                              l.status, l.created_at, u.username AS reviewer
                       FROM leave_requests l
                       JOIN employees e ON e.id = l.employee_id
                       LEFT JOIN users u ON u.id = l.reviewed_by"""
            parameters: tuple = ()
            if actor["role"] == "employee":
                employee_id = self._employee_id(connection, actor["id"])
                query += " WHERE l.employee_id = ?"
                parameters = (employee_id,)
            query += " ORDER BY CASE l.status WHEN 'Pending' THEN 0 ELSE 1 END, " \
                     "l.start_date DESC"
            return [dict(row) for row in connection.execute(query, parameters)]

    def review_leave_request(
        self, actor: dict, request_id: int, status: str
    ) -> None:
        self._require_role(actor, "admin", "manager")
        if status not in {"Approved", "Rejected"}:
            raise ValueError("A leave request can only be approved or rejected.")
        with self.database.connect() as connection:
            result = connection.execute(
                """UPDATE leave_requests
                   SET status = ?, reviewed_by = ?, reviewed_at = ?, updated_at = ?
                   WHERE id = ? AND status = 'Pending'""",
                (status, actor["id"], now_iso(), now_iso(), request_id),
            )
            if result.rowcount != 1:
                raise ValueError("Pending leave request was not found.")

    def create_announcement(
        self,
        actor: dict,
        *,
        title: str,
        body: str,
        audience: str,
    ) -> int:
        self._require_role(actor, "admin", "manager")
        title = _required(title, "Announcement title")
        body = _required(body, "Announcement message")
        if audience not in ANNOUNCEMENT_AUDIENCES:
            raise ValueError("Select a valid announcement audience.")
        timestamp = now_iso()
        with self.database.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO announcements
                   (title, body, audience, posted_by, publish_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (title, body, audience, actor["id"], timestamp, timestamp),
            )
            return int(cursor.lastrowid)

    def list_announcements(self, actor: dict) -> list[dict]:
        if actor.get("role") not in ROLES:
            raise PermissionError("Sign in before viewing announcements.")
        with self.database.connect() as connection:
            row = connection.execute(
                """SELECT e.employment_type FROM employees e
                   WHERE e.user_id = ?""",
                (actor["id"],),
            ).fetchone()
            employment_type = row["employment_type"] if row else "employee"
            audience = "Interns" if employment_type == "intern" else "Employees"
            audience_filter = (
                "a.audience IN ('Everyone', 'Employees', 'Interns')"
                if actor["role"] in {"admin", "manager"}
                else "a.audience IN ('Everyone', ?)"
            )
            parameters = (
                (now_iso(),)
                if actor["role"] in {"admin", "manager"}
                else (now_iso(), audience)
            )
            return [
                dict(item)
                for item in connection.execute(
                    f"""SELECT a.id, a.title, a.body, a.audience, a.publish_at,
                              u.username AS author
                       FROM announcements a JOIN users u ON u.id = a.posted_by
                       WHERE a.publish_at <= ?
                         AND {audience_filter}
                       ORDER BY a.publish_at DESC""",
                    parameters,
                )
            ]

    def add_employee(
        self,
        actor: dict,
        *,
        username: str,
        password: str,
        full_name: str,
        email: str,
        department: str,
        job_title: str,
        start_date: str,
        role: str = "employee",
        employment_type: str = "employee",
    ) -> int:
        self._require_role(actor, "admin")
        username = _validate_username(username)
        full_name = _required(full_name, "Full name")
        email = _validate_email(email)
        department = _required(department, "Department")
        job_title = _required(job_title, "Job title")
        start_date = _validate_date(start_date, "Start date") or ""
        if len(password) < 10:
            raise ValueError("Temporary password must be at least 10 characters.")
        if role not in {"manager", "employee"}:
            raise ValueError("New staff accounts must be a manager or employee.")
        if employment_type not in {"employee", "intern"}:
            raise ValueError("Employment type must be employee or intern.")
        timestamp = now_iso()
        try:
            with self.database.connect() as connection:
                cursor = connection.execute(
                    """INSERT INTO users(username, password_hash, role, created_at)
                       VALUES (?, ?, ?, ?)""",
                    (username, hash_password(password), role, timestamp),
                )
                employee_cursor = connection.execute(
                    """INSERT INTO employees
                       (user_id, full_name, email, department, job_title,
                        employment_type, start_date, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        cursor.lastrowid,
                        full_name,
                        email,
                        department,
                        job_title,
                        employment_type,
                        start_date,
                        timestamp,
                    ),
                )
                return int(employee_cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            raise ValueError("Username or email is already in use.") from error

    def list_employees(self, actor: dict) -> list[dict]:
        self._require_role(actor, "admin", "manager", "employee")
        with self.database.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    """SELECT e.id, e.full_name, e.email, e.department,
                              e.job_title, e.employment_type, e.start_date,
                              e.is_active, u.username, u.role
                       FROM employees e LEFT JOIN users u ON u.id = e.user_id
                       ORDER BY e.full_name COLLATE NOCASE"""
                )
            ]

    def add_intern_application(
        self,
        actor: dict,
        *,
        full_name: str,
        email: str,
        school: str,
        department: str,
        start_date: str,
    ) -> int:
        self._require_role(actor, "admin", "manager")
        values = (
            _required(full_name, "Full name"),
            _validate_email(email),
            _required(school, "School"),
            _required(department, "Department"),
            _validate_date(start_date, "Proposed start date") or "",
        )
        timestamp = now_iso()
        with self.database.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO intern_applications
                   (full_name, email, school, department, start_date,
                    submitted_by, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (*values, actor["id"], timestamp, timestamp),
            )
            return int(cursor.lastrowid)

    def list_intern_applications(self, actor: dict) -> list[dict]:
        self._require_role(actor, "admin", "manager", "employee")
        with self.database.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    """SELECT id, full_name, email, school, department,
                              start_date, status, created_at
                       FROM intern_applications ORDER BY created_at DESC"""
                )
            ]

    def update_application_status(
        self, actor: dict, application_id: int, status: str
    ) -> None:
        self._require_role(actor, "admin", "manager")
        if status not in APPLICATION_STATUSES:
            raise ValueError("Select a valid application status.")
        with self.database.connect() as connection:
            result = connection.execute(
                """UPDATE intern_applications SET status = ?, updated_at = ?
                   WHERE id = ?""",
                (status, now_iso(), application_id),
            )
            if result.rowcount != 1:
                raise ValueError("Intern application was not found.")

    def _employee_id(self, connection: sqlite3.Connection, user_id: int) -> int:
        row = connection.execute(
            "SELECT id FROM employees WHERE user_id = ? AND is_active = 1",
            (user_id,),
        ).fetchone()
        if row is None:
            raise ValueError("This account has no active staff profile.")
        return int(row["id"])

    def attendance_action(self, actor: dict, action: str) -> None:
        if actor.get("role") not in ROLES:
            raise PermissionError("Sign in before recording attendance.")
        timestamp = now_iso()
        with self.database.connect() as connection:
            employee_id = self._employee_id(connection, actor["id"])
            shift = connection.execute(
                """SELECT id, clock_in, clock_out FROM attendance_shifts
                   WHERE employee_id = ? AND clock_out IS NULL
                   ORDER BY id DESC LIMIT 1""",
                (employee_id,),
            ).fetchone()
            if action == "clock_in":
                if shift:
                    raise ValueError("You already have an active shift.")
                connection.execute(
                    """INSERT INTO attendance_shifts(employee_id, clock_in, created_at)
                       VALUES (?, ?, ?)""",
                    (employee_id, timestamp, timestamp),
                )
            elif action == "clock_out":
                if shift is None:
                    raise ValueError("Clock in before clocking out.")
                open_break = connection.execute(
                    "SELECT id FROM attendance_breaks WHERE shift_id = ? "
                    "AND break_end IS NULL",
                    (shift["id"],),
                ).fetchone()
                if open_break:
                    raise ValueError("End your active break before clocking out.")
                if datetime.fromisoformat(timestamp) < datetime.fromisoformat(
                    shift["clock_in"]
                ):
                    raise ValueError("Clock-out time cannot precede clock-in.")
                connection.execute(
                    "UPDATE attendance_shifts SET clock_out = ? WHERE id = ?",
                    (timestamp, shift["id"]),
                )
            elif action == "break_start":
                if shift is None:
                    raise ValueError("Clock in before starting a break.")
                active_break = connection.execute(
                    "SELECT id FROM attendance_breaks WHERE shift_id = ? "
                    "AND break_end IS NULL",
                    (shift["id"],),
                ).fetchone()
                if active_break:
                    raise ValueError("A break is already in progress.")
                connection.execute(
                    """INSERT INTO attendance_breaks(shift_id, break_start)
                       VALUES (?, ?)""",
                    (shift["id"], timestamp),
                )
            elif action == "break_end":
                if shift is None:
                    raise ValueError("There is no active shift.")
                active_break = connection.execute(
                    "SELECT id, break_start FROM attendance_breaks "
                    "WHERE shift_id = ? AND break_end IS NULL",
                    (shift["id"],),
                ).fetchone()
                if active_break is None:
                    raise ValueError("There is no active break to end.")
                if datetime.fromisoformat(timestamp) < datetime.fromisoformat(
                    active_break["break_start"]
                ):
                    raise ValueError("Break end cannot precede its start.")
                connection.execute(
                    "UPDATE attendance_breaks SET break_end = ? WHERE id = ?",
                    (timestamp, active_break["id"]),
                )
            else:
                raise ValueError("Unsupported attendance action.")

    def current_attendance_state(self, actor: dict) -> dict:
        with self.database.connect() as connection:
            employee_id = self._employee_id(connection, actor["id"])
            shift = connection.execute(
                """SELECT id, clock_in FROM attendance_shifts
                   WHERE employee_id = ? AND clock_out IS NULL
                   ORDER BY id DESC LIMIT 1""",
                (employee_id,),
            ).fetchone()
            if shift is None:
                return {"clocked_in": False, "on_break": False, "clock_in": None}
            open_break = connection.execute(
                "SELECT id FROM attendance_breaks WHERE shift_id = ? "
                "AND break_end IS NULL",
                (shift["id"],),
            ).fetchone()
            return {
                "clocked_in": True,
                "on_break": open_break is not None,
                "clock_in": shift["clock_in"],
            }

    def attendance_report(self, actor: dict) -> list[dict]:
        self._require_role(actor, "admin", "manager", "employee")
        with self.database.connect() as connection:
            employee_filter = ""
            parameters: tuple = (now_iso(),)
            if actor["role"] == "employee":
                employee_id = self._employee_id(connection, actor["id"])
                employee_filter = "WHERE s.employee_id = ?"
                parameters = (now_iso(), employee_id)
            rows = connection.execute(
                """SELECT s.id, e.full_name, e.department, s.clock_in, s.clock_out,
                          COALESCE(SUM(
                                  CASE
                                      WHEN b.break_end IS NOT NULL THEN
                                          (julianday(b.break_end) -
                                           julianday(b.break_start)) * 86400
                                      WHEN s.clock_out IS NULL AND b.break_start IS NOT NULL THEN
                                          (julianday(?) - julianday(b.break_start)) * 86400
                                      ELSE 0
                                  END
                              ), 0) AS break_seconds
                       FROM attendance_shifts s
                       JOIN employees e ON e.id = s.employee_id
                       LEFT JOIN attendance_breaks b ON b.shift_id = s.id
                       {employee_filter}
                       GROUP BY s.id
                       ORDER BY s.clock_in DESC""".format(
                    employee_filter=employee_filter
                ),
                parameters,
                ).fetchall()
        output = []
        for row in rows:
            elapsed = 0
            if row["clock_out"]:
                elapsed = (
                    datetime.fromisoformat(row["clock_out"])
                    - datetime.fromisoformat(row["clock_in"])
                ).total_seconds()
            elif row["clock_in"]:
                elapsed = (
                    datetime.fromisoformat(now_iso())
                    - datetime.fromisoformat(row["clock_in"])
                ).total_seconds()
            worked = max(0, elapsed - row["break_seconds"])
            output.append(
                {
                    "id": row["id"],
                    "employee": row["full_name"],
                    "department": row["department"],
                    "clock_in": row["clock_in"],
                    "clock_out": row["clock_out"] or "In progress",
                    "break_minutes": round(row["break_seconds"] / 60, 1),
                    "work_hours": round(worked / 3600, 2),
                }
            )
        return output

    def create_task(
        self,
        actor: dict,
        *,
        title: str,
        description: str,
        assigned_to: int,
        due_date: str,
        priority: str,
        project_id: int | None = None,
    ) -> int:
        self._require_role(actor, "admin", "manager")
        title = _required(title, "Task title")
        due_date = _validate_date(due_date, "Due date", optional=True)
        if priority not in PRIORITIES:
            raise ValueError("Select a valid priority.")
        timestamp = now_iso()
        with self.database.connect() as connection:
            employee = connection.execute(
                "SELECT id FROM employees WHERE id = ? AND is_active = 1",
                (assigned_to,),
            ).fetchone()
            if employee is None:
                raise ValueError("Select an active employee.")
            if project_id is not None and connection.execute(
                "SELECT 1 FROM projects WHERE id = ?", (project_id,)
            ).fetchone() is None:
                raise ValueError("Select an existing project or no project.")
            cursor = connection.execute(
                """INSERT INTO tasks
                   (title, description, assigned_to, assigned_by, due_date,
                    priority, created_at, updated_at, project_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    title,
                    description.strip(),
                    assigned_to,
                    actor["id"],
                    due_date,
                    priority,
                    timestamp,
                    timestamp,
                    project_id,
                ),
            )
            connection.execute(
                """INSERT INTO task_history
                   (task_id, changed_by, old_status, new_status, changed_at)
                   VALUES (?, ?, NULL, 'To Do', ?)""",
                (cursor.lastrowid, actor["id"], timestamp),
            )
            return int(cursor.lastrowid)

    def list_tasks(self, actor: dict) -> list[dict]:
        if actor.get("role") not in ROLES:
            raise PermissionError("Sign in before viewing tasks.")
        with self.database.connect() as connection:
            query = """SELECT t.id, t.title, t.description, e.full_name AS assignee,
                              p.name AS project, t.due_date, t.priority, t.status, t.created_at,
                              e.user_id AS assignee_user_id
                       FROM tasks t JOIN employees e ON e.id = t.assigned_to
                       LEFT JOIN projects p ON p.id = t.project_id"""
            parameters: tuple = ()
            if actor["role"] == "employee":
                query += " WHERE e.user_id = ?"
                parameters = (actor["id"],)
            query += " ORDER BY CASE t.status WHEN 'Done' THEN 1 ELSE 0 END, " \
                     "t.due_date IS NULL, t.due_date, t.created_at DESC"
            return [dict(row) for row in connection.execute(query, parameters)]

    def update_task_status(self, actor: dict, task_id: int, status: str) -> None:
        if actor.get("role") not in ROLES:
            raise PermissionError("Sign in before updating tasks.")
        if status not in TASK_STATUSES:
            raise ValueError("Select a valid task status.")
        timestamp = now_iso()
        with self.database.connect() as connection:
            task = connection.execute(
                """SELECT t.status, e.user_id FROM tasks t
                   JOIN employees e ON e.id = t.assigned_to WHERE t.id = ?""",
                (task_id,),
            ).fetchone()
            if task is None:
                raise ValueError("Task was not found.")
            if actor["role"] == "employee" and task["user_id"] != actor["id"]:
                raise PermissionError("You can only update tasks assigned to you.")
            if task["status"] == status:
                return
            connection.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status, timestamp, task_id),
            )
            connection.execute(
                """INSERT INTO task_history
                   (task_id, changed_by, old_status, new_status, changed_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (task_id, actor["id"], task["status"], status, timestamp),
            )

    def dashboard(self, actor: dict) -> dict:
        if actor.get("role") not in ROLES:
            raise PermissionError("Sign in before opening the dashboard.")
        with self.database.connect() as connection:
            staff_count = connection.execute(
                "SELECT COUNT(*) FROM employees WHERE is_active = 1"
            ).fetchone()[0]
            open_tasks = connection.execute(
                "SELECT COUNT(*) FROM tasks WHERE status != 'Done'"
            ).fetchone()[0]
            overdue_tasks = connection.execute(
                """SELECT COUNT(*) FROM tasks WHERE status != 'Done'
                   AND due_date IS NOT NULL AND due_date < ?""",
                (date.today().isoformat(),),
            ).fetchone()[0]
            applications = connection.execute(
                "SELECT COUNT(*) FROM intern_applications "
                "WHERE status IN ('Submitted', 'Under Review')"
            ).fetchone()[0]
            active_projects = connection.execute(
                "SELECT COUNT(*) FROM projects WHERE status = 'Active'"
            ).fetchone()[0]
            if actor["role"] == "employee":
                employee_id = self._employee_id(connection, actor["id"])
                assigned_tasks = connection.execute(
                    "SELECT COUNT(*) FROM tasks WHERE assigned_to = ? AND status != 'Done'",
                    (employee_id,),
                ).fetchone()[0]
                pending_leave = connection.execute(
                    """SELECT COUNT(*) FROM leave_requests
                       WHERE employee_id = ? AND status = 'Pending'""",
                    (employee_id,),
                ).fetchone()[0]
                today = date.today()
                shifts = connection.execute(
                    """SELECT id, clock_in, clock_out FROM attendance_shifts
                       WHERE employee_id = ?""",
                    (employee_id,),
                ).fetchall()
                own_hours = 0.0
                for shift in shifts:
                    start = datetime.fromisoformat(shift["clock_in"])
                    if start.astimezone().date() != today:
                        continue
                    end = (
                        datetime.fromisoformat(shift["clock_out"])
                        if shift["clock_out"]
                        else datetime.fromisoformat(now_iso())
                    )
                    breaks = connection.execute(
                        """SELECT break_start, break_end FROM attendance_breaks
                           WHERE shift_id = ?""",
                        (shift["id"],),
                    ).fetchall()
                    break_duration = 0.0
                    for item in breaks:
                        break_end = (
                            datetime.fromisoformat(item["break_end"])
                            if item["break_end"]
                            else datetime.fromisoformat(now_iso())
                        )
                        break_duration += max(
                            0,
                            (
                                break_end
                                - datetime.fromisoformat(item["break_start"])
                            ).total_seconds(),
                        )
                    own_hours += max(0, (end - start).total_seconds() - break_duration) / 3600
                return {
                    "my_open_tasks": assigned_tasks,
                    "hours_today": round(own_hours, 2),
                    "active_projects": active_projects,
                    "my_pending_leave": pending_leave,
                }
            pending_leave = connection.execute(
                "SELECT COUNT(*) FROM leave_requests WHERE status = 'Pending'"
            ).fetchone()[0]
            return {
                "active_staff": staff_count,
                "open_tasks": open_tasks,
                "overdue_tasks": overdue_tasks,
                "applications_to_review": applications,
                "active_projects": active_projects,
                "pending_leave_requests": pending_leave,
            }

    def export_attendance_csv(self, actor: dict, destination: str | Path) -> int:
        rows = self.attendance_report(actor)
        fields = [
            "id",
            "employee",
            "department",
            "clock_in",
            "clock_out",
            "break_minutes",
            "work_hours",
        ]
        path = Path(destination)
        with path.open("w", newline="", encoding="utf-8-sig") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)

    def has_open_shift(self, actor: dict) -> bool:
        return self.current_attendance_state(actor)["clocked_in"]
