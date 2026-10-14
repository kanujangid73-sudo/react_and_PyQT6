import time
import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from pipeline import ImagePipeline


class CameraWorker(QThread):
    """Asynchronous background worker running high-throughput video capture & recording."""
    frame_processed = pyqtSignal(np.ndarray, float)
    error_occurred = pyqtSignal(str)

    def __init__(self, camera_index=0, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self.running = False
        self.recording = False
        self.video_writer = None
        self.pipeline = ImagePipeline()

    def run(self):
        # Explicitly request DirectShow backend on Windows for faster camera initialization
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        
        if not cap.isOpened():
            # Fallback to default backend if DirectShow fails
            cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                self.run_synthetic_stream()
                return

        # Configure hardware camera properties for maximum throughput
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize frame buffer latency

        self.running = True
        while self.running:
            t0 = time.perf_counter()
            ret, frame = cap.read()
            if not ret:
                break

            processed_frame = self.pipeline.process(frame)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            # Write processed frame to output video file when recording
            if self.recording and self.video_writer is not None:
                self.video_writer.write(processed_frame)

            self.frame_processed.emit(processed_frame, elapsed_ms)

        if self.video_writer is not None:
            self.video_writer.release()
        cap.release()

    def run_synthetic_stream(self):
        """Generates animated synthetic frames if no physical webcam is connected."""
        self.running = True
        step = 0
        while self.running:
            t0 = time.perf_counter()
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.circle(
                frame, 
                (320 + int(100 * np.sin(step / 10)), 240 + int(50 * np.cos(step / 10))), 
                40, (0, 165, 255), -1
            )
            step += 1

            processed_frame = self.pipeline.process(frame)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            if self.recording and self.video_writer is not None:
                self.video_writer.write(processed_frame)

            self.frame_processed.emit(processed_frame, elapsed_ms)
            self.msleep(16)  # Maintain ~60 FPS simulated feed

        if self.video_writer is not None:
            self.video_writer.release()

    def start_recording(self, filename="pipeline_output.mp4"):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(filename, fourcc, 30.0, (640, 480))
        self.recording = True

    def stop_recording(self):
        self.recording = False
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

    def stop(self):
        self.running = False
        self.wait()