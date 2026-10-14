# Office Manager

A desktop office-management portfolio project built with **PyQt6** and **SQLite**. The application runs locally and stores its database in the current user's home directory; it does not require a browser, web framework, database server, or cloud account.

## Features

- **Role-based access:** administrator, manager, and employee screens. Important permissions are checked in the service layer as well as hidden in the interface.
- **Staff directory:** administrator-created employee and intern accounts with department, role, start date, and contact email.
- **Intern pipeline:** record a candidate application and move it through Submitted, Under Review, Accepted, and Rejected.
- **Attendance:** clock in/out and start/end breaks. Duplicate active shifts and clocking out during an open break are blocked. Worked time is calculated from timestamps less completed breaks.
- **Tasks:** managers and administrators assign prioritized work with optional due dates; employees see and update their own tasks. Status changes are retained in task history.
- **Projects:** create initiatives with owners, descriptions, timelines, and Active / On Hold / Completed status; tasks can be linked to a project.
- **Leave management:** employees and interns submit dated Annual, Sick, Personal, or Unpaid leave requests; managers/admins approve or reject them.
- **Announcements:** managers/admins publish notices for Everyone, Employees, or Interns; readers only see announcements intended for their account type.
- **Dashboard and reports:** role-specific summary, attendance hours, overdue tasks, pending leave requests, active projects, application counts, and attendance CSV export.
- **Credential handling:** first launch guides you through creating an administrator; passwords are stored as PBKDF2-SHA256 hashes, never as plain text.

## Requirements and setup

- Python 3.10 or newer
- Windows, macOS, or Linux with a graphical desktop

From the project directory:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

On macOS/Linux, activate with `source .venv/bin/activate` and then run `python -m pip install -r requirements.txt` and `python main.py`.

On first launch, create the initial administrator name, username, and password (minimum 10 characters). This one-time bootstrap protects the system's manager/admin controls. After setup, the sign-in window offers **Employee**, **Intern**, **Manager**, and **Administrator** account types, plus a registration button for employee and intern accounts. New employee/intern registrants can then sign in using the matching account type. Managers and administrators are provisioned by an administrator. A manager or admin can submit intern applications and assign tasks.

## Opening the registration forms

1. Start the app from the project folder with `python main.py`.
2. On a fresh database, the **Create administrator account** form opens first. Enter the administrator name and username, choose a password of at least 10 characters, confirm it, and select **Create account**. This one-time bootstrap creates the system administrator.
3. In the sign-in form, select **Employee** or **Intern** in **Sign in as**, then select **New here? Register as an employee or intern**.
4. In registration, choose **Employee** or **Intern** from **Register as** and fill in the name, email, department, job title, username, password, confirmation, and start date. Usernames must be 3–32 characters; passwords must contain at least 10 characters. Select **Create account**.
5. The sign-in form is pre-filled with the new username and selected account type. Enter the password used during registration and click **Sign in**. Employee accounts must sign in as Employee; intern accounts must sign in as Intern.
6. To register a staff member as an administrator instead, sign in as Administrator and open **Employees** → **Add employee / intern account**. This is also how manager accounts are created.
7. To record an intern candidate who is applying, without making them a system user yet, sign in as an administrator or manager and open **Intern Applications** → **New application**. Enter the candidate's details and submit; later update their review status.

The initial administrator setup form appears only while the database has no users. Employee/intern self-registration is available from the sign-in window after that setup is complete.

Database location:

- Windows: `%USERPROFILE%\.office_manager\office_manager.sqlite3`
- macOS/Linux: `~/.office_manager/office_manager.sqlite3`

Back up the database file while the application is closed. Do not use real employee data for public portfolio demos.

## Roles

| Capability | Admin | Manager | Employee |
|---|---:|---:|---:|
| Add employee / intern login | Yes | No | No |
| View staff directory | Yes | Yes | Yes |
| View intern applications | Yes | Yes | Yes |
| Submit/update intern applications | Yes | Yes | No |
| Assign tasks | Yes | Yes | No |
| See all attendance report and export CSV | Yes | Yes | No |
| See own attendance report and export CSV | Yes | Yes | Yes |
| Clock in/out and manage own breaks | Yes | Yes | Yes |
| See all tasks | Yes | Yes | No |
| See/update assigned tasks | Yes | Yes | Yes |

Employee accounts can view the complete employee directory and intern candidate register. Only managers and administrators can create or update intern applications; employee attendance views/exports are limited to their own shifts.

## Existing database upgrade

New project, leave-request, and announcement tables are created automatically when the app starts. Existing employees, intern applications, shifts, tasks, and task history are retained. The task table receives an optional project link; older tasks remain unassigned to a project. Back up the SQLite database before updating the app, and use made-up records in portfolio demos.

## Tests

The service and data-layer tests do not require a graphical session:

```powershell
python -m unittest discover -s tests -v
```

The test suite covers credential checks, authorization, shift state rules, break-adjusted hours, task visibility/project linking, leave approvals, audience-targeted announcements, application status, CSV export, and preservation of existing data during database upgrade.

## Architecture

```text
main.py                    Application startup and first-run setup
office_manager/
    database.py            SQLite schema, constraints, and connection setup
    security.py            Password hashing and verification
    services.py            Validation, permissions, and business workflows
    ui.py                  PyQt6 dialogs, pages, tables, and actions
tests/
    test_services.py       Service-level regression tests
```

The UI calls the service layer; the service layer enforces business rules and uses SQLite. Keep new business logic out of widget event handlers, and add service tests for workflow changes.

## Scope and next improvements

This is a local, single-database desktop app, suitable as a portfolio MVP—not a hosted HR/payroll system. Before handling real employee records, add a documented privacy/retention policy, protected backups, account deactivation and credential reset flows, audit review tools, and operational testing. For simultaneous use across multiple PCs, keep the PyQt6 client but move shared data behind an authenticated API and central database.

Useful portfolio follow-ups:

1. Add approved timesheet corrections and manager review.
2. Add employee profile editing/deactivation and account password reset.
3. Add department/date filters and task CSV export.
4. Add a packaged Windows installer and migration/backup utility.
5. Capture application screenshots and a short walkthrough after populating clearly fictional demo records.

## Demo checklist

1. Launch and create an administrator.
2. Add a manager and employee with fictional details.
3. Create and move an intern application through its statuses.
4. Create a project, assign a task to it, and post an announcement for a selected audience.
5. Sign in as the employee, clock in, record a break, clock out, update the task, and submit a leave request.
6. Return to manager, review the leave request, check work hours, and export the attendance CSV.
