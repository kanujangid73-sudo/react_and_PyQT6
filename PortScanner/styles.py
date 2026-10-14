DARK_THEME_QSS = """
QMainWindow {
    background-color: #1e1e2e;
}

QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

QGroupBox {
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
    color: #89b4fa;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QLineEdit, QSpinBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 6px;
    color: #cdd6f4;
}

QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #89b4fa;
}

QPushButton {
    background-color: #89b4fa;
    color: #11111b;
    font-weight: bold;
    border-radius: 5px;
    padding: 8px 16px;
}

QPushButton:hover {
    background-color: #b4befe;
}

QPushButton:disabled {
    background-color: #45475a;
    color: #6c7086;
}

QPushButton#stopBtn {
    background-color: #f38ba8;
    color: #11111b;
}

QPushButton#stopBtn:hover {
    background-color: #eba0ac;
}

QTableWidget {
    background-color: #181825;
    border: 1px solid #45475a;
    border-radius: 6px;
    gridline-color: #313244;
}

QHeaderView::section {
    background-color: #313244;
    color: #cdd6f4;
    padding: 6px;
    border: none;
    font-weight: bold;
}

QProgressBar {
    border: 1px solid #45475a;
    border-radius: 5px;
    text-align: center;
    background-color: #313244;
    color: #cdd6f4;
}

QProgressBar::chunk {
    background-color: #a6e3a1;
    border-radius: 4px;
}
"""