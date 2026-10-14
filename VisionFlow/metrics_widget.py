import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout


class PerformanceMetricsWidget(QWidget):
    """Real-time performance plot monitoring pipeline processing latency."""
    
    def __init__(self, max_samples=100, parent=None):
        super().__init__(parent)
        self.max_samples = max_samples
        self.data_history = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Configure dark aesthetic theme for PyQtGraph
        pg.setConfigOption('background', '#181825')
        pg.setConfigOption('foreground', '#cdd6f4')
        
        self.plot_widget = pg.PlotWidget(title="Pipeline Latency (ms)")
        self.plot_widget.setYRange(0, 50)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        
        self.curve = self.plot_widget.plot(
            pen=pg.mkPen(color="#89b4fa", width=2),
            brush=pg.mkBrush(color="#89b4fa33"),
            fillLevel=0
        )
        layout.addWidget(self.plot_widget)

    def add_sample(self, latency_ms: float):
        self.data_history.append(latency_ms)
        if len(self.data_history) > self.max_samples:
            self.data_history.pop(0)

        self.curve.setData(self.data_history)