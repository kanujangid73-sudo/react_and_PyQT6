from PIL import Image, ImageFilter, ImageOps, ImageQt
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QImage


class BaseNode:
    """Abstract Base Class for Workflow Nodes."""
    title = "Base Node"
    input_names = []
    output_names = []

    def __init__(self):
        self.inputs_data = {}
        self.outputs_data = {}

    def compute(self, parent_widget=None):
        pass


class LoadImageNode(BaseNode):
    title = "Load Color Image"
    input_names = []
    output_names = ["Image Out"]

    def __init__(self):
        super().__init__()
        self.file_path = None

    def set_file_path(self, path):
        self.file_path = path

    def compute(self, parent_widget=None):
        if not self.file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                parent_widget,
                "Select Input Image",
                "",
                "Image Files (*.png *.jpg *.jpeg *.bmp)"
            )
            if file_path:
                self.file_path = file_path

        if self.file_path:
            img = Image.open(self.file_path)
            self.outputs_data["Image Out"] = img
            return f"Loaded Image: {self.file_path}"
        
        return "Load failed: No file selected."


class GrayscaleNode(BaseNode):
    title = "Grayscale Filter"
    input_names = ["Image In"]
    output_names = ["Image Out"]

    def compute(self, parent_widget=None):
        img = self.inputs_data.get("Image In")
        if img:
            gray_img = ImageOps.grayscale(img)
            self.outputs_data["Image Out"] = gray_img
            return "Converted image to Grayscale."
        return "Grayscale failed: No input image connected."


class BlurNode(BaseNode):
    title = "Gaussian Blur"
    input_names = ["Image In"]
    output_names = ["Image Out"]

    def compute(self, parent_widget=None):
        img = self.inputs_data.get("Image In")
        if img:
            blurred_img = img.filter(ImageFilter.GaussianBlur(radius=5))
            self.outputs_data["Image Out"] = blurred_img
            return "Applied Gaussian Blur (Radius: 5)."
        return "Blur failed: No input image connected."


class OutputDisplayNode(BaseNode):
    title = "Output Saver"
    input_names = ["Image In"]
    output_names = []

    def compute(self, parent_widget=None):
        img = self.inputs_data.get("Image In")
        if img:
            file_path, _ = QFileDialog.getSaveFileName(
                parent_widget,
                "Save Processed Image",
                "output.png",
                "PNG Files (*.png);;JPEG Files (*.jpg)"
            )
            if file_path:
                img.save(file_path)
                return f"Processed image saved to: {file_path}"
            return "Save cancelled by user."
        return "Output failed: No input image connected."