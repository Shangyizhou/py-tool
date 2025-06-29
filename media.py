import os
import cv2
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, 
                             QTextEdit, QFileDialog, QWidget, QHBoxLayout, QRadioButton, 
                             QButtonGroup, QSpinBox, QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from moviepy import VideoFileClip

class VideoProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 视频处理工具")
        self.setGeometry(100, 100, 800, 600)
        
        # 初始化变量
        self.video_path = ""
        self.save_format = "png"
        self.frame_count = 0
        
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 拖拽区域
        self.drop_label = QLabel("拖拽视频文件到这里", self)
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                padding: 20px;
                font-size: 16px;
            }
        """)
        self.drop_label.setAcceptDrops(True)
        layout.addWidget(self.drop_label)
        
        # 视频信息显示
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        layout.addWidget(self.info_text)
        
        # 帧提取控制
        frame_control = QHBoxLayout()
        self.spin_box = QSpinBox()
        self.spin_box.setRange(1, 1000)
        self.spin_box.setValue(10)
        frame_control.addWidget(QLabel("保存前多少帧:"))
        frame_control.addWidget(self.spin_box)
        layout.addLayout(frame_control)
        
        # 格式选择
        format_group = QButtonGroup(self)
        formats = [("PNG", "png"), ("JPEG", "jpeg"), ("GIF", "gif")]
        for text, value in formats:
            radio = QRadioButton(text)
            radio.setChecked(value == "png")
            format_group.addButton(radio)
            layout.addWidget(radio)
        format_group.buttonClicked.connect(lambda btn: setattr(self, "save_format", btn.text().lower()))
        
        # 进度条
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # 操作按钮
        self.parse_btn = QPushButton("解析视频信息")
        self.parse_btn.clicked.connect(self.parse_video)
        self.save_btn = QPushButton("开始保存帧")
        self.save_btn.clicked.connect(self.start_save_frames)
        layout.addWidget(self.parse_btn)
        layout.addWidget(self.save_btn)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            self.video_path = urls[0].toLocalFile()
            self.drop_label.setText(f"已加载: {os.path.basename(self.video_path)}")
    
    def parse_video(self):
        """解析视频元数据"""
        if not self.video_path:
            self.info_text.setText("错误: 请先拖拽视频文件！")
            return
        
        try:
            # 使用OpenCV获取基础信息
            cap = cv2.VideoCapture(self.video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            # 使用MoviePy获取更多元数据
            clip = VideoFileClip(self.video_path)
            duration = clip.duration
            audio_info = "有音频" if clip.audio else "无音频"
            clip.close()
            
            # 显示信息
            info = f"""视频路径: {self.video_path}
基本参数:
- 分辨率: {width}x{height}
- 帧率(FPS): {fps:.2f}
- 总帧数: {frame_count}
- 时长: {duration:.2f}秒
- 音频轨道: {audio_info}
文件大小: {os.path.getsize(self.video_path)/1024/1024:.2f}MB
"""
            self.info_text.setText(info)
            self.frame_count = frame_count
            self.spin_box.setMaximum(frame_count)
            
        except Exception as e:
            self.info_text.setText(f"解析错误: {str(e)}")
    
    def start_save_frames(self):
        """启动多线程保存帧"""
        if not self.video_path:
            self.info_text.append("错误: 请先加载并解析视频！")
            return
        
        self.worker = SaveFramesWorker(
            self.video_path, 
            self.spin_box.value(), 
            self.save_format
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_save_complete)
        self.worker.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def on_save_complete(self, save_dir):
        self.info_text.append(f"保存完成！文件位于: {save_dir}")

class SaveFramesWorker(QThread):
    progress = Signal(int)
    finished = Signal(str)
    
    def __init__(self, video_path, save_count, save_format):
        super().__init__()
        self.video_path = video_path
        self.save_count = save_count
        self.save_format = save_format
    
    def run(self):
        try:
            # 创建保存目录
            save_dir = os.path.join(os.path.dirname(self.video_path), "extracted_frames")
            os.makedirs(save_dir, exist_ok=True)
            
            # 读取视频
            cap = cv2.VideoCapture(self.video_path)
            total_frames = min(self.save_count, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            
            # 逐帧保存
            for i in range(total_frames):
                ret, frame = cap.read()
                if not ret:
                    break
                
                save_path = os.path.join(save_dir, f"frame_{i:04d}.{self.save_format}")
                cv2.imwrite(save_path, frame)
                self.progress.emit(int((i + 1) / total_frames * 100))
            
            cap.release()
            self.finished.emit(save_dir)
            
        except Exception as e:
            print(f"保存错误: {str(e)}")

if __name__ == "__main__":
    app = QApplication([])
    window = VideoProcessor()
    window.show()
    app.exec()