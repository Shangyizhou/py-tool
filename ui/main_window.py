from PySide6.QtWidgets import QMainWindow, QTabWidget
from core.json_parser import JsonParserTab
from core.video_processor import VideoProcessorTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多功能工具箱")
        self.setGeometry(100, 100, 800, 600)
        
        # 主标签页
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # 添加功能模块
        self._add_tabs()

    def _add_tabs(self):
        self.tab_widget.addTab(JsonParserTab(), "JSON解析")
        self.tab_widget.addTab(VideoProcessorTab(), "视频处理")