import sys
import json
import pyperclip

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QFileDialog, QHeaderView
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent

class JsonParserApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JSON性能数据解析工具")
        self.setGeometry(100, 100, 800, 600)
        
        # 主窗口布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 文件选择区域（可拖拽和点击）
        self.file_drop_area = QLabel("拖拽或点击此处选择JSON文件")
        self.file_drop_area.setAlignment(Qt.AlignCenter)
        self.file_drop_area.setStyleSheet(
            "QLabel { border: 2px dashed #aaa; padding: 20px; }"
            "QLabel:hover { background-color: #f0f0f0; cursor: pointer; }"
        )
        self.file_drop_area.setAcceptDrops(True)
        self.file_drop_area.mousePressEvent = self.open_file_dialog  # 添加点击事件
        self.file_path = ""
        
        # 解析按钮
        self.btn_parse = QPushButton("解析JSON")
        self.btn_parse.clicked.connect(self.parse_json)
        self.btn_parse.setEnabled(False)
        
        # 文件路径显示
        self.label_path = QLabel("未选择文件")
        self.label_path.setWordWrap(True)
        
        # 表格展示区域
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "renderCost", "writeFrameCost", "extractCost",
            "algorithmCost", "feedCost", "segmentCount",
            "isUseSnpe", "isUseMtk"
        ])
        
        # 导出飞书Markdown
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.btn_export = QPushButton("导出为飞书Markdown") 
        self.btn_export.clicked.connect(self.export_to_feishu_md)

        # 布局组合
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.btn_parse)
        
        main_layout.addWidget(self.file_drop_area)
        main_layout.addWidget(self.label_path)
        main_layout.addLayout(file_layout)
        main_layout.addWidget(self.btn_export)
        main_layout.addWidget(self.table)

    
    def open_file_dialog(self, event=None):
        """通过对话框选择文件"""
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("JSON文件 (*.json)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.file_path = selected_files[0]
                self.label_path.setText(f"已选择文件: {self.file_path}")
                self.btn_parse.setEnabled(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入区域时检测是否为文件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """处理拖拽文件"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.json'):
                self.file_path = file_path
                self.label_path.setText(f"已拖拽文件: {self.file_path}")
                self.btn_parse.setEnabled(True)
                break
    
    def parse_json(self):
        """解析JSON并填充表格"""
        if not self.file_path:
            return
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 清空表格并设置行数
            self.table.setRowCount(0)
            if isinstance(data, list):
                self.table.setRowCount(len(data))
                for row_idx, item in enumerate(data):
                    self._fill_table_row(row_idx, item)
            elif isinstance(data, dict):
                self.table.setRowCount(1)
                self._fill_table_row(0, data)
            
        except Exception as e:
            self.label_path.setText(f"解析失败: {str(e)}")
    
    def _fill_table_row(self, row_idx: int, item: dict):
        """填充表格单行数据"""
        fields = [
            "renderCost", "writeFrameCost", "extractCost",
            "algorithmCost", "feedCost", "segmentCount",
            "isUseSnpe", "isUseMtk"
        ]
        for col_idx, field in enumerate(fields):
            value = item.get(field, "N/A")
            self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
    
    def export_to_feishu_md(self):
        """将表格数据转换为飞书兼容的Markdown并复制到剪贴板"""
        if self.table.rowCount() == 0:
            return

        # 生成Markdown表格头
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        md_table = "| " + " | ".join(headers) + " |\n"
        md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

        # 填充表格内容
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            md_table += "| " + " | ".join(row_data) + " |\n"

        # 复制到剪贴板
        pyperclip.copy(md_table)
        self.label_path.setText("Markdown表格已复制到剪贴板！可直接粘贴到飞书文档")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JsonParserApp()
    window.show()
    sys.exit(app.exec())