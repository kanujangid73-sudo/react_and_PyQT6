from __future__ import annotations

import sys
import sqlite3
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

from office_manager.database import Database
from office_manager.services import OfficeService
from office_manager.ui import LoginDialog, MainWindow, SetupDialog


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Office Manager")
    app.setOrganizationName("Office Manager Portfolio")
    app.setStyle("Fusion")
    app.setStyleSheet(
        """
        * { font-family: "Segoe UI"; font-size: 10pt; }
        QWidget { color: #e5edf7; background-color: #111a25; }
        QMainWindow, QDialog, QTabWidget::pane { background: #111a25; }
        QFrame#appHeader { background: #0b121b; }
        QLabel#brandMark {
            background: #3d8bfd; color: #ffffff; border-radius: 10px;
            font-size: 15pt; font-weight: 700; min-width: 42px; max-width: 42px;
            min-height: 42px; max-height: 42px; qproperty-alignment: AlignCenter;
        }
        QLabel#brandTitle { color: #ffffff; font-size: 14pt; font-weight: 700; }
        QLabel#brandSubtitle { color: #8fa5bf; font-size: 8pt; letter-spacing: 1px; }
        QLabel#userBadge {
            color: #e5edf7; background: #1b2a3b; border: 1px solid #30445b;
            border-radius: 15px; padding: 7px 13px; font-weight: 600;
        }
        QTabWidget::pane {
            background: #111a25; border: 0; top: -1px;
        }
        QTabBar { background: #151f2c; }
        QTabBar::tab {
            background: #151f2c; color: #9baabd; border: 0;
            border-bottom: 3px solid transparent; padding: 14px 19px;
            min-width: 88px; font-weight: 600;
        }
        QTabBar::tab:hover { color: #8bc0ff; background: #1b2939; }
        QTabBar::tab:selected {
            color: #8bc0ff; border-bottom: 3px solid #3d8bfd;
            background: #111a25;
        }
        QLabel#pageTitle { color: #f0f5fb; font-size: 21pt; font-weight: 700; }
        QLabel#pageDescription { color: #91a1b5; font-size: 10pt; }
        QLabel#welcomeTitle { color: #dbe7f5; font-size: 14pt; font-weight: 600; }
        QFrame#metricCard {
            background: #1a2634; border: 1px solid #2b3a4c;
            border-radius: 10px;
        }
        QLabel#metricValue { color: #72b2ff; font-size: 25pt; font-weight: 700; }
        QLabel#metricTitle { color: #e0e9f4; font-size: 11pt; font-weight: 700; }
        QLabel#metricHint { color: #91a1b5; font-size: 9pt; }
        QLabel#statusBanner {
            color: #b3c0d0; background: #1b2735; border: 1px solid #2c3c4f;
            border-radius: 8px; padding: 13px 16px; font-weight: 600;
        }
        QLabel#statusBanner[state="clockedIn"] {
            color: #9be2b2; background: #173326; border: 1px solid #28573c;
        }
        QLabel#statusBanner[state="onBreak"] {
            color: #f3ce7a; background: #352b18; border: 1px solid #665126;
        }
        QPushButton {
            background: #263548; color: #dce7f4; border: 1px solid #364a61;
            border-radius: 6px; padding: 9px 15px; font-weight: 600;
        }
        QPushButton:hover { background: #30445c; border-color: #4b6686; }
        QPushButton:pressed { background: #203044; }
        QPushButton#primaryButton {
            background: #347fe0; color: #ffffff; border: 1px solid #347fe0;
        }
        QPushButton#primaryButton:hover {
            background: #438ff0; border-color: #438ff0;
        }
        QPushButton#secondaryButton {
            background: #1a2634; color: #d5e2f1; border: 1px solid #35485e;
        }
        QPushButton#secondaryButton:hover { background: #243448; }
        QPushButton:disabled { background: #202a36; color: #718095; }
        QLineEdit, QComboBox, QDateEdit, QTextEdit {
            background: #182330; color: #e5edf7; border: 1px solid #35475c;
            border-radius: 6px; padding: 8px 10px; selection-background-color: #347fe0;
        }
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
            border: 1px solid #58a0fa;
        }
        QComboBox::drop-down, QDateEdit::drop-down {
            border: 0; width: 25px; background: transparent;
        }
        QComboBox QAbstractItemView {
            background: #1a2634; color: #e5edf7; border: 1px solid #35475c;
            selection-background-color: #2d5f9c; selection-color: #ffffff;
        }
        QTableWidget {
            background: #17222e; alternate-background-color: #1a2735;
            color: #dce6f2; gridline-color: #263546; border: 1px solid #2b3b4e;
            border-radius: 8px; selection-background-color: #254a73;
            selection-color: #ffffff; outline: 0;
        }
        QTableWidget::item { padding: 7px; border: 0; }
        QHeaderView::section {
            background: #202d3c; color: #b6c5d7; padding: 10px 8px;
            border: 0; border-bottom: 1px solid #334459; font-weight: 700;
        }
        QScrollBar:vertical {
            background: #111a25; width: 10px; margin: 2px;
        }
        QScrollBar::handle:vertical {
            background: #3b4c61; border-radius: 4px; min-height: 25px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        QToolTip {
            color: #f3f7fc; background: #26384c; border: 1px solid #425a76; padding: 5px;
        }
        QMessageBox { background: #182330; }
        QCalendarWidget QWidget { background: #182330; color: #e5edf7; }
        QCalendarWidget QAbstractItemView {
            background: #182330; color: #e5edf7;
            selection-background-color: #347fe0; selection-color: #ffffff;
        }
        """
    )

    try:
        data_directory = Path.home() / ".office_manager"
        database = Database(data_directory / "office_manager.sqlite3")
        service = OfficeService(database)
    except (OSError, RuntimeError, sqlite3.Error) as error:
        QMessageBox.critical(None, "Startup error", str(error))
        return 1

    if not database.has_users():
        setup = SetupDialog(service)
        if setup.exec() != QDialog.DialogCode.Accepted:
            return 0

    login = LoginDialog(service)
    if login.exec() != QDialog.DialogCode.Accepted or login.user is None:
        return 0

    window = MainWindow(service, login.user)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
