import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QPushButton, QTextEdit, QSplitter, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt

from canvas import NodeCanvasScene, NodeCanvasView
from node_graphics import NodeGraphic
from node_engine import LoadImageNode, GrayscaleNode, BlurNode, OutputDisplayNode


NODE_REGISTRY = {
    "Load Color Image": LoadImageNode,
    "Grayscale Filter": GrayscaleNode,
    "Gaussian Blur": BlurNode,
    "Output Saver": OutputDisplayNode,
}


class NodeStudioApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.node_items = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Custom Node-Based Workflow Automation Studio")
        self.resize(1200, 750)
        self.apply_dark_theme()

        main_widget = QWidget()
        main_layout = QHBoxLayout()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sidebar Controls
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout()

        header_btn = QPushButton("Available Nodes")
        header_btn.setEnabled(False)
        sidebar_layout.addWidget(header_btn)

        self.node_list = QListWidget()
        for name in NODE_REGISTRY.keys():
            self.node_list.addItem(name)
        # Allow double-clicking node items to add them instantly
        self.node_list.itemDoubleClicked.connect(self.add_selected_node)
        sidebar_layout.addWidget(self.node_list)

        self.add_node_btn = QPushButton("Add Node to Canvas")
        self.add_node_btn.clicked.connect(self.add_selected_node)
        sidebar_layout.addWidget(self.add_node_btn)

        self.run_pipeline_btn = QPushButton("Execute Workflow")
        self.run_pipeline_btn.setObjectName("runBtn")
        self.run_pipeline_btn.clicked.connect(self.execute_workflow)
        sidebar_layout.addWidget(self.run_pipeline_btn)

        self.save_graph_btn = QPushButton("Save Graph (JSON)")
        self.save_graph_btn.clicked.connect(self.save_graph)
        sidebar_layout.addWidget(self.save_graph_btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Execution logs will appear here...")
        sidebar_layout.addWidget(self.log_output)

        sidebar.setLayout(sidebar_layout)
        splitter.addWidget(sidebar)

        # Canvas Scene & View
        self.scene = NodeCanvasScene()
        self.view = NodeCanvasView(self.scene)
        splitter.addWidget(self.view)

        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def add_selected_node(self):
        selected_items = self.node_list.selectedItems()
        if not selected_items:
            return

        node_type_name = selected_items[0].text()
        node_class = NODE_REGISTRY[node_type_name]

        node_logic = node_class()
        node_graphic = NodeGraphic(node_logic)

        center_pos = self.view.mapToScene(self.view.viewport().rect().center())
        # Offset position slightly per node so they don't stack on top of each other
        offset = len(self.node_items) * 20
        node_graphic.setPos(center_pos.x() - 80 + offset, center_pos.y() - 60 + offset)

        self.scene.addItem(node_graphic)
        self.node_items.append(node_graphic)

    def execute_workflow(self):
        self.log_output.clear()
        self.log_output.append(">>> Initializing Workflow Execution Pipeline...\n")

        # Step 1: Pass data across connected wires
        for node_graphic in self.node_items:
            for out_socket in node_graphic.outputs:
                for edge in out_socket.edges:
                    if edge.end_socket:
                        target_node = edge.end_socket.node.logic
                        source_data = node_graphic.logic.outputs_data.get(out_socket.name)
                        target_node.inputs_data[edge.end_socket.name] = source_data

        # Step 2: Compute logic sequentially and update UI image previews
        for node_graphic in self.node_items:
            msg = node_graphic.logic.compute(parent_widget=self)
            if msg:
                self.log_output.append(f"[{node_graphic.logic.title}]: {msg}")
            
            # Render computed image preview on canvas node
            out_img = node_graphic.logic.outputs_data.get("Image Out")
            if out_img:
                node_graphic.display_pil_image(out_img)

        self.log_output.append("\n>>> Execution Complete.")

        # Step 2: Compute logic sequentially and prompt for files when necessary
        for node_graphic in self.node_items:
            msg = node_graphic.logic.compute(parent_widget=self)
            if msg:
                self.log_output.append(f"[{node_graphic.logic.title}]: {msg}")

        self.log_output.append("\n>>> Execution Complete.")

    def save_graph(self):
        graph_data = []
        for item in self.node_items:
            graph_data.append({
                "title": item.logic.title,
                "x": item.pos().x(),
                "y": item.pos().y()
            })

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Workflow Graph", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, "w") as f:
                json.dump(graph_data, f, indent=4)
            QMessageBox.information(self, "Success", "Workflow graph saved successfully!")

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #11111b;
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
            }
            QListWidget, QTextEdit {
                background-color: #1e1e2e;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton#runBtn {
                background-color: #a6e3a1;
                color: #11111b;
            }
            QPushButton#runBtn:hover {
                background-color: #94e2d5;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NodeStudioApp()
    window.show()
    sys.exit(app.exec())