from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'manager', 'employee')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    department TEXT NOT NULL,
    job_title TEXT NOT NULL,
    employment_type TEXT NOT NULL DEFAULT 'employee'
        CHECK (employment_type IN ('employee', 'intern')),
    start_date TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intern_applications (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    school TEXT NOT NULL,
    department TEXT NOT NULL,
    start_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Submitted'
        CHECK (status IN ('Submitted', 'Under Review', 'Accepted', 'Rejected')),
    submitted_by INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance_shifts (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    clock_in TEXT NOT NULL,
    clock_out TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance_breaks (
    id INTEGER PRIMARY KEY,
    shift_id INTEGER NOT NULL REFERENCES attendance_shifts(id) ON DELETE CASCADE,
    break_start TEXT NOT NULL,
    break_end TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    assigned_to INTEGER NOT NULL REFERENCES employees(id),
    assigned_by INTEGER NOT NULL REFERENCES users(id),
    due_date TEXT,
    priority TEXT NOT NULL DEFAULT 'Medium'
        CHECK (priority IN ('Low', 'Medium', 'High')),
    status TEXT NOT NULL DEFAULT 'To Do'
        CHECK (status IN ('To Do', 'In Progress', 'Blocked', 'Done')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_history (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    changed_by INTEGER NOT NULL REFERENCES users(id),
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    owner_id INTEGER NOT NULL REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'Active'
        CHECK (status IN ('Active', 'On Hold', 'Completed')),
    start_date TEXT NOT NULL,
    due_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leave_requests (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    leave_type TEXT NOT NULL
        CHECK (leave_type IN ('Annual', 'Sick', 'Personal', 'Unpaid')),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending'
        CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    audience TEXT NOT NULL DEFAULT 'Everyone'
        CHECK (audience IN ('Everyone', 'Employees', 'Interns')),
    posted_by INTEGER NOT NULL REFERENCES users(id),
    publish_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_shifts_employee_clockin
    ON attendance_shifts(employee_id, clock_in);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee_status
    ON tasks(assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_leave_employee_status
    ON leave_requests(employee_id, status);
CREATE INDEX IF NOT EXISTS idx_announcements_publish
    ON announcements(publish_at);
"""


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path, timeout=10, factory=ClosingConnection
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            task_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(tasks)")
            }
            if "project_id" not in task_columns:
                connection.execute(
                    "ALTER TABLE tasks ADD COLUMN project_id INTEGER "
                    "REFERENCES projects(id) ON DELETE SET NULL"
                )

    def has_users(self) -> bool:
        with self.connect() as connection:
            row = connection.execute("SELECT EXISTS(SELECT 1 FROM users)").fetchone()
            return bool(row[0])
