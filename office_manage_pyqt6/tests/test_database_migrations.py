from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from office_manager.database import Database


class DatabaseMigrationTests(unittest.TestCase):
    def test_old_task_rows_survive_optional_project_link_migration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.sqlite3"
            with closing(sqlite3.connect(path)) as connection:
                with connection:
                    connection.execute(
                        """CREATE TABLE tasks (
                        id INTEGER PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL DEFAULT '',
                        assigned_to INTEGER NOT NULL,
                        assigned_by INTEGER NOT NULL,
                        due_date TEXT,
                        priority TEXT NOT NULL DEFAULT 'Medium',
                        status TEXT NOT NULL DEFAULT 'To Do',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                        )"""
                    )
                    connection.execute(
                        """INSERT INTO tasks
                       (id, title, description, assigned_to, assigned_by,
                        due_date, priority, status, created_at, updated_at)
                       VALUES (17, 'Keep this task', 'Existing record', 4, 2,
                               NULL, 'High', 'In Progress', '2026-01-01',
                               '2026-01-02')"""
                    )

            Database(path)

            with closing(sqlite3.connect(path)) as connection:
                columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(tasks)")
                }
                row = connection.execute(
                    "SELECT id, title, status, project_id FROM tasks WHERE id = 17"
                ).fetchone()
            self.assertIn("project_id", columns)
            self.assertEqual(row, (17, "Keep this task", "In Progress", None))


if __name__ == "__main__":
    unittest.main()
