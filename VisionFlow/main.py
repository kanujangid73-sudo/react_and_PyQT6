import sys
import time
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QComboBox, QSlider, QLabel, QPushButton, QSplitter, QGroupBox, QFileDialog
)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt

from camera_worker import CameraWorker
from metrics_widget import PerformanceMetricsWidget


class VisionFlowStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = CameraWorker()
        self.latest_frame = None
        self.last_frame_time = time.time()  # Measures wall-clock frame intervals
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        self.setWindowTitle("VisionFlow Studio — Computer Vision Pipeline Studio")
        self.resize(1300, 800)
        self.apply_dark_stylesheet()

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- Left Panel: Controls & Telemetry ---
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setSpacing(10)

        # 1. Pipeline Selector
        pipeline_group = QGroupBox("Pipeline Algorithms")
        pipeline_layout = QVBoxLayout(pipeline_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Original", "AI Face Detection", "Grayscale", "Gaussian Blur", 
            "Canny Edges", "Contour / Object Detection", "Color Threshold (HSV)"
        ])
        pipeline_layout.addWidget(self.mode_combo)
        control_layout.addWidget(pipeline_group)

        # 2. Parameters Control
        params_group = QGroupBox("Adjust Parameters")
        params_layout = QVBoxLayout(params_group)

        params_layout.addWidget(QLabel("Blur Radius"))
        self.blur_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_slider.setRange(1, 31)
        self.blur_slider.setValue(5)
        params_layout.addWidget(self.blur_slider)

        params_layout.addWidget(QLabel("Brightness"))
        self.bright_slider = QSlider(Qt.Orientation.Horizontal)
        self.bright_slider.setRange(-100, 100)
        self.bright_slider.setValue(0)
        params_layout.addWidget(self.bright_slider)

        params_layout.addWidget(QLabel("Canny Low Threshold"))
        self.canny_slider = QSlider(Qt.Orientation.Horizontal)
        self.canny_slider.setRange(10, 200)
        self.canny_slider.setValue(50)
        params_layout.addWidget(self.canny_slider)

        control_layout.addWidget(params_group)

        # 3. Stream & Recording Actions
        export_group = QGroupBox("Recording & Media Captures")
        export_layout = QVBoxLayout(export_group)

        self.toggle_btn = QPushButton("Start Video Engine")
        self.toggle_btn.setObjectName("startBtn")
        export_layout.addWidget(self.toggle_btn)

        self.snapshot_btn = QPushButton("Take Snapshot")
        export_layout.addWidget(self.snapshot_btn)

        self.record_btn = QPushButton("Start Video Recording")
        export_layout.addWidget(self.record_btn)

        control_layout.addWidget(export_group)

        # 4. Latency Graph
        self.metrics_widget = PerformanceMetricsWidget()
        control_layout.addWidget(self.metrics_widget)

        main_splitter.addWidget(control_panel)

        # --- Right Panel: Video Viewport ---
        viewport_panel = QWidget()
        viewport_layout = QVBoxLayout(viewport_panel)
        
        self.video_label = QLabel("Stream Stopped. Click 'Start Video Engine' to initiate.")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #11111b;
                border: 2px dashed #45475a;
                border-radius: 10px;
                color: #a6adc8;
                font-size: 14px;
            }
        """)
        viewport_layout.addWidget(self.video_label)
        
        main_splitter.addWidget(viewport_panel)
        main_splitter.setSizes([400, 900])

        self.setCentralWidget(main_splitter)

    def connect_signals(self):
        self.toggle_btn.clicked.connect(self.toggle_stream)
        self.snapshot_btn.clicked.connect(self.take_snapshot)
        self.record_btn.clicked.connect(self.toggle_recording)
        self.mode_combo.currentTextChanged.connect(self.worker.pipeline.set_mode)
        self.blur_slider.valueChanged.connect(self.update_blur)
        self.bright_slider.valueChanged.connect(self.update_brightness)
        self.canny_slider.valueChanged.connect(self.update_canny)
        self.worker.frame_processed.connect(self.on_frame_processed)

    def update_blur(self, val):
        self.worker.pipeline.blur_radius = val

    def update_brightness(self, val):
        self.worker.pipeline.brightness = val

    def update_canny(self, val):
        self.worker.pipeline.canny_low = val

    def toggle_stream(self):
        if not self.worker.isRunning():
            self.worker.start()
            self.toggle_btn.setText("Stop Video Engine")
            self.toggle_btn.setObjectName("stopBtn")
            self.restyle_button(self.toggle_btn)
        else:
            self.worker.stop()
            self.toggle_btn.setText("Start Video Engine")
            self.toggle_btn.setObjectName("startBtn")
            self.restyle_button(self.toggle_btn)
            self.video_label.setText("Stream Stopped.")

    def take_snapshot(self):
        if self.latest_frame is not None:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Frame Snapshot", "", "PNG Image (*.png);;JPEG Image (*.jpg)"
            )
            if file_path:
                cv2.imwrite(file_path, self.latest_frame)

    def toggle_recording(self):
        if not self.worker.recording:
            self.worker.start_recording("pipeline_output.mp4")
            self.record_btn.setText("Stop Video Recording")
            self.record_btn.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold;")
        else:
            self.worker.stop_recording()
            self.record_btn.setText("Start Video Recording")
            self.record_btn.setStyleSheet("")

    def on_frame_processed(self, frame: np.ndarray, latency_ms: float):
        self.latest_frame = frame.copy()

        # Measure accurate hardware FPS
        current_time = time.time()
        delta_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        real_fps = int(1.0 / delta_time) if delta_time > 0 else 0

        # Draw HUD on video feed
        h, w, ch = frame.shape
        hud_text = f"FPS: {real_fps} | Latency: {latency_ms:.1f}ms | Res: {w}x{h}"
        cv2.putText(frame, hud_text, (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(q_img)

        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)
        self.metrics_widget.add_sample(latency_ms)

    def apply_dark_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
            }
            QGroupBox {
                border: 1px solid #45475a;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QComboBox, QSlider {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 4px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#startBtn {
                background-color: #a6e3a1;
            }
            QPushButton#stopBtn {
                background-color: #f38ba8;
            }
        """)

    def restyle_button(self, btn):
        btn.style().unpolish(btn)
        btn.style().polish(btn)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VisionFlowStudio()
    window.show()
    sys.exit(app.exec())