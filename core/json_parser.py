import json
import pyperclip
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, 
    QFileDialog, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent

class JsonParserTab(QWidget):
    def __init__(self):
        super().__init__()
        self.file_path = ""
        self.dynamic_headers = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 文件拖拽区域（支持点击和拖拽）
        self.file_drop_area = QLabel("拖拽或点击选择JSON文件")
        self.file_drop_area.setAlignment(Qt.AlignCenter)
        self.file_drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                padding: 20px;
                background-color: #f9f9f9;
            }
            QLabel:hover {
                background-color: #f0f0f0;
                cursor: pointer;
            }
        """)
        self.file_drop_area.setAcceptDrops(True)
        self.file_drop_area.mousePressEvent = self._open_file_dialog
        
        # 操作按钮区域
        btn_layout = QHBoxLayout()
        self.btn_parse = QPushButton("解析JSON")
        self.btn_parse.clicked.connect(self._parse_json)
        self.btn_parse.setEnabled(False)
        
        self.btn_export = QPushButton("导出为飞书Markdown")
        self.btn_export.clicked.connect(self._export_to_markdown)
        self.btn_export.setEnabled(False)
        
        btn_layout.addWidget(self.btn_parse)
        btn_layout.addWidget(self.btn_export)
        
        # 表格展示
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.file_drop_area)
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)

    def _open_file_dialog(self, event):
        """点击选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择JSON文件", 
            "", 
            "JSON文件 (*.json)"
        )
        if file_path:
            self._handle_file_selection(file_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入时验证文件类型"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """处理拖拽文件"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.json'):
                self._handle_file_selection(file_path)
                break

    def _handle_file_selection(self, file_path):
        """统一处理文件选择逻辑"""
        self.file_path = file_path
        self.btn_parse.setEnabled(True)
        self.file_drop_area.setText(f"已选择: {file_path.split('/')[-1]}")
        self.file_drop_area.setStyleSheet("border: 2px solid #4CAF50; padding: 20px;")

    def _parse_json(self):
        """解析JSON并填充表格"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 统一数据格式为列表
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                raise ValueError("JSON格式不支持：必须为字典或列表")
            
            # 动态提取表头
            all_fields = set()
            for item in data:
                if isinstance(item, dict):
                    all_fields.update(item.keys())
            self.dynamic_headers = sorted(all_fields)
            
            # 渲染表格
            self.table.clear()
            self.table.setColumnCount(len(self.dynamic_headers))
            self.table.setHorizontalHeaderLabels(self.dynamic_headers)
            self.table.setRowCount(len(data))
            
            for row_idx, item in enumerate(data):
                for col_idx, field in enumerate(self.dynamic_headers):
                    value = str(item.get(field, "N/A"))
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(value))
            
            self.btn_export.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "解析错误", f"无法解析JSON文件:\n{str(e)}")

    def _export_to_markdown(self):
        """将表格转换为飞书Markdown格式并复制到剪贴板"""
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "导出失败", "没有可导出的数据")
            return
        
        try:
            # 生成表头
            headers = [
                self.table.horizontalHeaderItem(i).text() 
                for i in range(self.table.columnCount())
            ]
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
            QMessageBox.information(
                self, 
                "导出成功", 
                "Markdown表格已复制到剪贴板，可直接粘贴到飞书文档"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "导出错误", 
                f"生成Markdown时出错:\n{str(e)}"
            )