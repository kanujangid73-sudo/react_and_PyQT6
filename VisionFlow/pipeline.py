import cv2
import numpy as np


class ImagePipeline:
    """Enhanced Modular Image Processing Engine with AI Face & Contour Detection."""
    
    def __init__(self):
        self.mode = "Original"
        self.blur_radius = 5
        self.brightness = 0
        self.contrast = 1.0
        self.canny_low = 50
        self.canny_high = 150
        
        # Load OpenCV's built-in Haar Cascade classifier for face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def set_mode(self, mode: str):
        self.mode = mode

    def process(self, frame: np.ndarray) -> np.ndarray:
        if frame is None:
            return frame

        # Apply Brightness & Contrast Adjustment
        if self.brightness != 0 or self.contrast != 1.0:
            frame = cv2.convertScaleAbs(frame, alpha=self.contrast, beta=self.brightness)

        # Pipeline Algorithms
        if self.mode == "AI Face Detection":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            output = frame.copy()
            for (x, y, w, h) in faces:
                cv2.rectangle(output, (x, y), (x + w, y + h), (255, 180, 0), 2)
                cv2.putText(output, "Face Target", (x, y - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 180, 0), 2)
            return output

        elif self.mode == "Grayscale":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        elif self.mode == "Gaussian Blur":
            k = max(1, self.blur_radius | 1)  # Ensure kernel dimension is odd
            return cv2.GaussianBlur(frame, (k, k), 0)

        elif self.mode == "Canny Edges":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, self.canny_low, self.canny_high)
            return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        elif self.mode == "Contour / Object Detection":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            output = frame.copy()
            for cnt in contours:
                if cv2.contourArea(cnt) > 500:  # Filter out minor noise
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(output, "Target Object", (x, y - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            return output

        elif self.mode == "Color Threshold (HSV)":
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower = np.array([0, 120, 70])
            upper = np.array([10, 255, 255])
            mask = cv2.inRange(hsv, lower, upper)
            return cv2.bitwise_and(frame, frame, mask=mask)

        return frame