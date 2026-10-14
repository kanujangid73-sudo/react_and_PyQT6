from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem, 
    QGraphicsProxyWidget, QPushButton, QFileDialog, QLabel, QVBoxLayout, QWidget
)
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPixmap
from PyQt6.QtCore import Qt, QRectF
from PIL import ImageQt


class SocketGraphic(QGraphicsItem):
    """Interactive connection pin (Socket) for wiring nodes."""
    def __init__(self, parent_node, name: str, is_output: bool = False):
        super().__init__(parent_node)
        self.node = parent_node
        self.name = name
        self.is_output = is_output
        self.radius = 7.0
        self.edges = []

        # Label next to pin
        self.label = QGraphicsTextItem(name, self)
        self.label.setDefaultTextColor(QColor("#a6adc8"))
        self.label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        
        if is_output:
            self.label.setPos(-self.label.boundingRect().width() - 6, -11)
        else:
            self.label.setPos(10, -11)

    def boundingRect(self):
        return QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

    def paint(self, painter, option, widget=None):
        # Green for output sockets, Blue for input sockets
        pin_color = QColor("#a6e3a1") if self.is_output else QColor("#89b4fa")
        painter.setBrush(QBrush(pin_color))
        painter.setPen(QPen(QColor("#11111b"), 2))
        painter.drawEllipse(self.boundingRect())

    def get_scene_pos(self):
        return self.scenePos()


class NodeGraphic(QGraphicsRectItem):
    """Sleek UI Node container with structured inner layout."""
    def __init__(self, node_logic):
        super().__init__()
        self.logic = node_logic
        self.width = 200
        self.height = 220

        self.setRect(0, 0, self.width, self.height)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        # Node Title Bar Header
        self.title_item = QGraphicsTextItem(node_logic.title, self)
        self.title_item.setDefaultTextColor(QColor("#11111b"))
        self.title_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.title_item.setPos(8, 3)

        self.inputs = []
        self.outputs = []
        self.setup_sockets()

        # Inner Content Layout
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(10, 0, 10, 10)
        layout.setSpacing(6)

        # Dedicated "Browse Image" Button inside Load Image Node
        if hasattr(self.logic, 'file_path'):
            self.btn = QPushButton("Browse Image")
            self.btn.setStyleSheet("""
                QPushButton {
                    background-color: #89b4fa;
                    color: #11111b;
                    font-weight: bold;
                    font-size: 11px;
                    border-radius: 5px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #b4befe;
                }
            """)
            self.btn.clicked.connect(self.browse_file)
            layout.addWidget(self.btn)

        # Image Preview Box
        self.image_preview = QLabel("No Image Selected")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setFixedSize(180, 115)
        self.image_preview.setStyleSheet("""
            QLabel {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 6px;
                color: #6c7086;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.image_preview)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(self.container)
        
        # Position inner container below title and socket header
        start_y = 65 if hasattr(self.logic, 'file_path') else 65
        proxy.setPos(0, start_y)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Select Input Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.logic.set_file_path(file_path)
            self.btn.setText("Change Image")
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    175, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                self.image_preview.setPixmap(scaled_pixmap)

    def display_pil_image(self, pil_img):
        """Displays PIL Image directly inside the node preview box."""
        if pil_img:
            q_img = ImageQt.ImageQt(pil_img)
            pixmap = QPixmap.fromImage(q_img)
            scaled_pixmap = pixmap.scaled(
                175, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.image_preview.setPixmap(scaled_pixmap)

    def setup_sockets(self):
        # Input Sockets
        for i, in_name in enumerate(self.logic.input_names):
            sock = SocketGraphic(self, in_name, is_output=False)
            sock.setPos(0, 42 + i * 22)
            self.inputs.append(sock)

        # Output Sockets
        for j, out_name in enumerate(self.logic.output_names):
            sock = SocketGraphic(self, out_name, is_output=True)
            sock.setPos(self.width, 42 + j * 22)
            self.outputs.append(sock)

    def paint(self, painter, option, widget=None):
        # Card Body Background & Border
        body_color = QColor("#2a2b3d") if not self.isSelected() else QColor("#36374f")
        painter.setBrush(QBrush(body_color))
        border_color = QColor("#f5e0dc") if self.isSelected() else QColor("#45475a")
        painter.setPen(QPen(border_color, 2 if self.isSelected() else 1))
        painter.drawRoundedRect(self.rect(), 10, 10)

        # Header Bar Styling
        painter.setBrush(QBrush(QColor("#89b4fa")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width, 28, 10, 10)
        painter.drawRect(0, 18, self.width, 10)