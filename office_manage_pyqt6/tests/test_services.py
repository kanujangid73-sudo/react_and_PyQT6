from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from office_manager.database import Database
from office_manager.services import OfficeService


class OfficeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "test.sqlite3")
        self.service = OfficeService(self.database)
        self.service.create_initial_admin("admin", "A-strong-password", "Admin User")
        self.admin = self.service.login("admin", "A-strong-password")
        self.employee_id = self.service.add_employee(
            self.admin,
            username="jules",
            password="Another-strong-password",
            full_name="Jules Employee",
            email="jules@example.test",
            department="Operations",
            job_title="Coordinator",
            start_date="2026-01-12",
        )
        self.employee = self.service.login("jules", "Another-strong-password")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_login_uses_password_hash_and_rejects_wrong_password(self) -> None:
        self.assertEqual(self.employee["role"], "employee")
        with self.assertRaisesRegex(ValueError, "Invalid username, password"):
            self.service.login("jules", "wrong")

    def test_register_employee_and_intern_then_require_matching_login_type(self) -> None:
        intern_id = self.service.register_account(
            username="sam.intern",
            password="Intern-password-123",
            full_name="Sam Intern",
            email="sam.intern@example.test",
            department="Engineering",
            job_title="Intern",
            start_date="2026-07-01",
            employment_type="intern",
        )
        self.assertGreater(intern_id, 0)
        intern = self.service.login(
            "sam.intern", "Intern-password-123", account_type="intern"
        )
        self.assertEqual(intern["role"], "employee")
        self.assertEqual(intern["employment_type"], "intern")
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.service.login(
                "sam.intern", "Intern-password-123", account_type="employee"
            )
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.service.login(
                "jules", "Another-strong-password", account_type="intern"
            )

    def test_registration_validates_required_fields_and_account_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "Passwords|Password"):
            self.service.register_account(
                username="new.person",
                password="short",
                full_name="New Person",
                email="new@example.test",
                department="Operations",
                job_title="Assistant",
                start_date="2026-07-01",
                employment_type="employee",
            )
        with self.assertRaisesRegex(ValueError, "Choose Employee or Intern"):
            self.service.register_account(
                username="new.person",
                password="Strong-password-123",
                full_name="New Person",
                email="new@example.test",
                department="Operations",
                job_title="Assistant",
                start_date="2026-07-01",
                employment_type="admin",
            )

    def test_user_can_change_own_password(self) -> None:
        with self.assertRaisesRegex(ValueError, "Current password is incorrect"):
            self.service.change_password(self.employee, "wrong", "Updated-password")
        self.service.change_password(
            self.employee, "Another-strong-password", "Updated-password"
        )
        self.assertEqual(
            self.service.login("jules", "Updated-password")["id"],
            self.employee["id"],
        )

    def test_staff_creation_rejects_non_admin(self) -> None:
        with self.assertRaises(PermissionError):
            self.service.add_employee(
                self.employee,
                username="unauthorized",
                password="Another-strong-password",
                full_name="Unauthorized User",
                email="unauthorized@example.test",
                department="Operations",
                job_title="Coordinator",
                start_date="2026-01-12",
            )

    def test_employee_can_view_staff_and_intern_application_records(self) -> None:
        second_employee_id = self.service.add_employee(
            self.admin,
            username="morgan",
            password="Different-strong-password",
            full_name="Morgan Employee",
            email="morgan@example.test",
            department="Finance",
            job_title="Analyst",
            start_date="2026-01-15",
        )
        self.assertNotEqual(second_employee_id, self.employee_id)
        employees = self.service.list_employees(self.employee)
        self.assertEqual(
            {employee["full_name"] for employee in employees},
            {"Admin User", "Jules Employee", "Morgan Employee"},
        )

        application_id = self.service.add_intern_application(
            self.admin,
            full_name="Taylor Candidate",
            email="taylor@example.test",
            school="Example College",
            department="Engineering",
            start_date="2026-08-01",
        )
        applications = self.service.list_intern_applications(self.employee)
        self.assertIn(application_id, {application["id"] for application in applications})
        with self.assertRaises(PermissionError):
            self.service.update_application_status(
                self.employee, application_id, "Accepted"
            )

    def test_employee_attendance_report_is_scoped_to_their_own_records(self) -> None:
        other_employee_id = self.service.add_employee(
            self.admin,
            username="morgan",
            password="Different-strong-password",
            full_name="Morgan Employee",
            email="morgan@example.test",
            department="Finance",
            job_title="Analyst",
            start_date="2026-01-15",
        )
        other_employee = self.service.login("morgan", "Different-strong-password")
        self.service.attendance_action(self.employee, "clock_in")
        self.service.attendance_action(other_employee, "clock_in")

        own_rows = self.service.attendance_report(self.employee)
        admin_rows = self.service.attendance_report(self.admin)
        self.assertEqual([row["employee"] for row in own_rows], ["Jules Employee"])
        self.assertEqual(len(admin_rows), 2)

    def test_projects_can_be_created_and_attached_to_tasks(self) -> None:
        project_id = self.service.create_project(
            self.admin,
            name="Office move",
            description="Coordinate the office move.",
            start_date="2026-05-01",
            due_date="2026-06-01",
        )
        project = next(
            item
            for item in self.service.list_projects(self.employee)
            if item["id"] == project_id
        )
        self.assertEqual(project["status"], "Active")
        task_id = self.service.create_task(
            self.admin,
            title="Book movers",
            description="Get vendor quotes.",
            assigned_to=self.employee_id,
            due_date="2026-05-15",
            priority="High",
            project_id=project_id,
        )
        task = next(
            item
            for item in self.service.list_tasks(self.employee)
            if item["id"] == task_id
        )
        self.assertEqual(task["project"], "Office move")
        self.service.update_project_status(self.admin, project_id, "On Hold")
        self.assertEqual(
            next(
                item
                for item in self.service.list_projects(self.employee)
                if item["id"] == project_id
            )["status"],
            "On Hold",
        )

    def test_leave_request_workflow_and_employee_scope(self) -> None:
        request_id = self.service.submit_leave_request(
            self.employee,
            leave_type="Annual",
            start_date="2026-08-10",
            end_date="2026-08-12",
            reason="Family travel",
        )
        requests = self.service.list_leave_requests(self.employee)
        self.assertEqual(requests[0]["status"], "Pending")
        with self.assertRaises(PermissionError):
            self.service.review_leave_request(self.employee, request_id, "Approved")
        self.service.review_leave_request(self.admin, request_id, "Approved")
        self.assertEqual(
            self.service.list_leave_requests(self.admin)[0]["status"], "Approved"
        )
        with self.assertRaisesRegex(ValueError, "overlaps an existing"):
            self.service.submit_leave_request(
                self.employee,
                leave_type="Personal",
                start_date="2026-08-11",
                end_date="2026-08-13",
                reason="Overlapping dates",
            )
        with self.assertRaisesRegex(ValueError, "cannot be before"):
            self.service.submit_leave_request(
                self.employee,
                leave_type="Sick",
                start_date="2026-08-13",
                end_date="2026-08-12",
                reason="Invalid range",
            )

    def test_announcements_are_filtered_for_intern_and_employee_audiences(self) -> None:
        intern_id = self.service.register_account(
            username="casey.intern",
            password="Intern-password-456",
            full_name="Casey Intern",
            email="casey.intern@example.test",
            department="Engineering",
            job_title="Intern",
            start_date="2026-07-01",
            employment_type="intern",
        )
        intern = self.service.login(
            "casey.intern", "Intern-password-456", account_type="intern"
        )
        self.service.create_announcement(
            self.admin,
            title="Intern orientation",
            body="Orientation begins Monday.",
            audience="Interns",
        )
        self.service.create_announcement(
            self.admin,
            title="Employee benefits",
            body="Annual enrollment is open.",
            audience="Employees",
        )
        self.assertEqual(
            [item["title"] for item in self.service.list_announcements(intern)],
            ["Intern orientation"],
        )
        self.assertEqual(
            [item["title"] for item in self.service.list_announcements(self.employee)],
            ["Employee benefits"],
        )
        self.assertGreater(intern["id"], 0)

    def test_attendance_blocks_duplicate_clock_in_and_open_break_clock_out(self) -> None:
        self.service.attendance_action(self.employee, "clock_in")
        with self.assertRaisesRegex(ValueError, "already have an active shift"):
            self.service.attendance_action(self.employee, "clock_in")
        self.service.attendance_action(self.employee, "break_start")
        with self.assertRaisesRegex(ValueError, "End your active break"):
            self.service.attendance_action(self.employee, "clock_out")
        self.service.attendance_action(self.employee, "break_end")
        self.service.attendance_action(self.employee, "clock_out")
        self.assertFalse(self.service.current_attendance_state(self.employee)["clocked_in"])

    def test_work_hours_subtract_completed_break_time(self) -> None:
        timestamps = iter(
            [
                "2026-06-02T08:00:00+00:00",
                "2026-06-02T12:00:00+00:00",
                "2026-06-02T12:30:00+00:00",
                "2026-06-02T17:00:00+00:00",
                "2026-06-02T18:00:00+00:00",
            ]
        )
        with patch("office_manager.services.now_iso", side_effect=lambda: next(timestamps)):
            self.service.attendance_action(self.employee, "clock_in")
            self.service.attendance_action(self.employee, "break_start")
            self.service.attendance_action(self.employee, "break_end")
            self.service.attendance_action(self.employee, "clock_out")

        report = self.service.attendance_report(self.admin)
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["break_minutes"], 30.0)
        self.assertEqual(report[0]["work_hours"], 8.5)

    def test_employee_only_sees_and_updates_assigned_tasks(self) -> None:
        task_id = self.service.create_task(
            self.admin,
            title="Prepare weekly report",
            description="Summarize office operations.",
            assigned_to=self.employee_id,
            due_date="2026-06-05",
            priority="High",
        )
        self.assertEqual([task["id"] for task in self.service.list_tasks(self.employee)], [task_id])
        self.service.update_task_status(self.employee, task_id, "In Progress")
        self.assertEqual(self.service.list_tasks(self.employee)[0]["status"], "In Progress")

        other_id = self.service.add_employee(
            self.admin,
            username="lee",
            password="One-more-strong-password",
            full_name="Lee Employee",
            email="lee@example.test",
            department="Finance",
            job_title="Analyst",
            start_date="2026-01-12",
        )
        other_task = self.service.create_task(
            self.admin,
            title="Private assignment",
            description="",
            assigned_to=other_id,
            due_date="",
            priority="Low",
        )
        self.assertNotIn(other_task, [task["id"] for task in self.service.list_tasks(self.employee)])
        with self.assertRaises(PermissionError):
            self.service.update_task_status(self.employee, other_task, "Done")

    def test_intern_application_workflow_and_csv_export(self) -> None:
        application_id = self.service.add_intern_application(
            self.admin,
            full_name="Pat Candidate",
            email="pat@example.test",
            school="Example University",
            department="Engineering",
            start_date="2026-07-01",
        )
        self.service.update_application_status(self.admin, application_id, "Under Review")
        self.assertEqual(
            self.service.list_intern_applications(self.admin)[0]["status"],
            "Under Review",
        )
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "attendance.csv"
            self.assertEqual(
                self.service.export_attendance_csv(self.admin, destination),
                0,
            )
            self.assertTrue(destination.read_text(encoding="utf-8-sig").startswith("id,employee"))


if __name__ == "__main__":
    unittest.main()
