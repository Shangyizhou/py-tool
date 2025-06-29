import os
import cv2
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QTextEdit, QSpinBox, QProgressBar, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, QThread, Signal
from moviepy import VideoFileClip

class VideoProcessorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.video_path = ""
        self.save_format = "png"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 拖拽区域
        self.drop_label = QLabel("拖拽视频文件到这里")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("border: 2px dashed #aaa; padding: 20px;")
        self.drop_label.setAcceptDrops(True)
        
        # 元数据显示
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        
        # 帧提取控制
        self.spin_box = QSpinBox()
        self.spin_box.setRange(1, 1000)
        
        # 格式选择
        format_group = QButtonGroup()
        for text, value in [("PNG", "png"), ("JPEG", "jpeg")]:
            radio = QRadioButton(text)
            radio.setChecked(value == "png")
            format_group.addButton(radio)
            layout.addWidget(radio)
        format_group.buttonClicked.connect(lambda btn: setattr(self, "save_format", btn.text().lower()))
        
        # 操作按钮
        self.btn_parse = QPushButton("解析视频")
        self.btn_parse.clicked.connect(self._parse_video)
        
        layout.addWidget(self.drop_label)
        layout.addWidget(self.info_text)
        layout.addWidget(self.spin_box)
        layout.addWidget(self.btn_parse)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self.video_path = urls[0].toLocalFile()
            self.drop_label.setText(f"已加载: {os.path.basename(self.video_path)}")

    def _parse_video(self):
        try:
            cap = cv2.VideoCapture(self.video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            
            clip = VideoFileClip(self.video_path)
            duration = clip.duration
            clip.close()
            
            self.info_text.setText(
                f"帧率: {fps:.2f}\n总帧数: {frame_count}\n时长: {duration:.2f}秒"
            )
            self.spin_box.setMaximum(frame_count)
            
        except Exception as e:
            self.info_text.setText(f"视频解析错误: {e}")