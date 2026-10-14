from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsPathItem
from PyQt6.QtGui import QPen, QColor, QPainter, QPainterPath, QTransform
from PyQt6.QtCore import Qt, QPointF, QLineF

from node_graphics import SocketGraphic


class BezierEdgeGraphic(QGraphicsPathItem):
    """Draws a smooth Bezier wire between two sockets."""
    def __init__(self, start_socket: SocketGraphic, end_socket: SocketGraphic = None):
        super().__init__()
        self.start_socket = start_socket
        self.end_socket = end_socket
        self.end_pos = QPointF(0, 0)

        self.setPen(QPen(QColor("#a6e3a1"), 2.5))
        self.setZValue(-1)

        if start_socket:
            start_socket.edges.append(self)
        if end_socket:
            end_socket.edges.append(self)

    def update_positions(self):
        p1 = self.start_socket.get_scene_pos()
        p2 = self.end_socket.get_scene_pos() if self.end_socket else self.end_pos

        path = QPainterPath(p1)
        dx = abs(p2.x() - p1.x()) * 0.5
        ctrl1 = QPointF(p1.x() + dx, p1.y())
        ctrl2 = QPointF(p2.x() - dx, p2.y())

        path.cubicTo(ctrl1, ctrl2, p2)
        self.setPath(path)


class NodeCanvasScene(QGraphicsScene):
    """Infinite Grid Canvas Scene."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self.grid_size = 20

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor("#1e1e2e"))

        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)

        pen = QPen(QColor("#313244"), 1)
        painter.setPen(pen)

        lines = []
        for x in range(left, int(rect.right()), self.grid_size):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), self.grid_size):
            lines.append(QLineF(rect.left(), y, rect.right(), y))

        painter.drawLines(lines)


class NodeCanvasView(QGraphicsView):
    """Custom view supporting panning, zooming, and interactive wiring."""
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.drag_edge = None
        self.is_panning = False
        self.pan_start = QPointF()

    def wheelEvent(self, event):
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())

        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        if event.button() == Qt.MouseButton.LeftButton and isinstance(item, SocketGraphic):
            if item.is_output:
                self.drag_edge = BezierEdgeGraphic(start_socket=item)
                self.drag_edge.end_pos = self.mapToScene(event.pos())
                self.scene().addItem(self.drag_edge)
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_panning:
            delta = self.mapToScene(event.pos()) - self.mapToScene(self.pan_start)
            self.pan_start = event.pos()
            self.setTransform(QTransform(self.transform().translate(delta.x(), delta.y())))
            return

        if self.drag_edge:
            self.drag_edge.end_pos = self.mapToScene(event.pos())
            self.drag_edge.update_positions()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        if event.button() == Qt.MouseButton.LeftButton and self.drag_edge:
            item = self.itemAt(event.pos())
            if isinstance(item, SocketGraphic) and not item.is_output:
                self.drag_edge.end_socket = item
                item.edges.append(self.drag_edge)
                self.drag_edge.update_positions()
            else:
                self.scene().removeItem(self.drag_edge)
                self.drag_edge.start_socket.edges.remove(self.drag_edge)
            self.drag_edge = None

        super().mouseReleaseEvent(event)