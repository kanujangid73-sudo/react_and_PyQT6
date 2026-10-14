import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QSpinBox, QPushButton, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from scanner_worker import ScanWorker
from styles import DARK_THEME_QSS


class PortScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.scan_results = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Multi-Threaded Port Scanner & Security Audit Tool")
        self.resize(900, 650)
        self.setStyleSheet(DARK_THEME_QSS)

        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # --- Controls Box ---
        config_box = QGroupBox("Scan Configurations")
        config_layout = QHBoxLayout()

        # Target IP / Host
        config_layout.addWidget(QLabel("Target Host:"))
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("e.g. 127.0.0.1 or scanme.nmap.org")
        self.host_input.setText("127.0.0.1")
        config_layout.addWidget(self.host_input)

        # Port Range
        config_layout.addWidget(QLabel("Ports:"))
        self.start_port = QSpinBox()
        self.start_port.setRange(1, 65535)
        self.start_port.setValue(1)
        config_layout.addWidget(self.start_port)

        config_layout.addWidget(QLabel("-"))
        self.end_port = QSpinBox()
        self.end_port.setRange(1, 65535)
        self.end_port.setValue(1024)
        config_layout.addWidget(self.end_port)

        # Threads
        config_layout.addWidget(QLabel("Threads:"))
        self.thread_count = QSpinBox()
        self.thread_count.setRange(1, 200)
        self.thread_count.setValue(50)
        config_layout.addWidget(self.thread_count)

        config_box.setLayout(config_layout)
        main_layout.addWidget(config_box)

        # --- Action Buttons & Status ---
        action_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Scan")
        self.start_btn.clicked.connect(self.start_scan)
        action_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        action_layout.addWidget(self.stop_btn)

        self.export_btn = QPushButton("Export JSON")
        self.export_btn.clicked.connect(self.export_results)
        action_layout.addWidget(self.export_btn)

        main_layout.addLayout(action_layout)

        # --- Progress Bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # --- Results Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Port", "Status", "Service", "Banner / Info"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.table)

        # Status Label
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def start_scan(self):
        target = self.host_input.text().strip()
        start = self.start_port.value()
        end = self.end_port.value()
        threads = self.thread_count.value()

        if not target:
            QMessageBox.warning(self, "Input Error", "Please enter a target host or IP.")
            return

        if start > end:
            QMessageBox.warning(self, "Port Error", "Start port must be less than or equal to end port.")
            return

        # Reset UI Table
        self.table.setRowCount(0)
        self.scan_results.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Scanning target: {target}...")

        # Update Controls State
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # Start QThread Worker
        self.worker = ScanWorker(target_host=target, start_port=start, end_port=end, max_threads=threads)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.result_signal.connect(self.add_table_row)
        self.worker.finished_signal.connect(self.scan_finished)
        self.worker.error_signal.connect(self.scan_error)
        self.worker.start()

    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.status_label.setText("Cancelling scan...")

    def update_progress(self, scanned: int, total: int):
        percentage = int((scanned / total) * 100)
        self.progress_bar.setValue(percentage)

    def add_table_row(self, data: dict):
        self.scan_results.append(data)
        row = self.table.rowCount()
        self.table.insertRow(row)

        port_item = QTableWidgetItem(str(data["port"]))
        status_item = QTableWidgetItem(data["status"])
        service_item = QTableWidgetItem(data["service"])
        banner_item = QTableWidgetItem(data["banner"])

        # Highlight open ports green
        status_item.setForeground(QColor("#a6e3a1"))
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.table.setItem(row, 0, port_item)
        self.table.setItem(row, 1, status_item)
        self.table.setItem(row, 2, service_item)
        self.table.setItem(row, 3, banner_item)

    def scan_finished(self, message: str):
        self.status_label.setText(message)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def scan_error(self, error_msg: str):
        QMessageBox.critical(self, "Scan Error", error_msg)
        self.status_label.setText("Scan failed.")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def export_results(self):
        if not self.scan_results:
            QMessageBox.information(self, "Export", "No results to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Scan Results", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, "w") as f:
                json.dump(self.scan_results, f, indent=4)
            QMessageBox.information(self, "Export", "Scan results exported successfully!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PortScannerApp()
    window.show()
    sys.exit(app.exec())