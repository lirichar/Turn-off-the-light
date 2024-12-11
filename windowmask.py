import sys
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QSlider, QLabel, QHBoxLayout, QMessageBox


# 全局变量存储亮度值
global_opacity = 150  # 初始默认亮度值


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("屏幕遮罩选择区域")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        
        # 提示标签
        self.label = QLabel("调整遮罩亮度，然后点击“确定”进入选择区域")
        layout.addWidget(self.label)
        
        # 亮度调节滑动条
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(50, 255)  # 遮罩透明度范围
        self.slider.setValue(global_opacity)  # 初始值
        self.slider.valueChanged.connect(self.update_brightness)  # 监听滑动条值变化
        layout.addWidget(self.slider)

        # 按钮
        button_layout = QHBoxLayout()
        self.preview_button = QPushButton("预览")
        self.preview_button.clicked.connect(self.preview_brightness)
        button_layout.addWidget(self.preview_button)

        self.start_button = QPushButton("确定")
        self.start_button.clicked.connect(self.start_selection_mode)
        button_layout.addWidget(self.start_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def update_brightness(self):
        """滑动条值变化时更新亮度"""
        global global_opacity
        global_opacity = self.slider.value()  # 更新全局亮度

    def preview_brightness(self):
        """预览遮罩亮度"""
        self.preview_window = PreviewWindow(global_opacity)
        self.preview_window.show()

    def start_selection_mode(self):
        """进入选择区域模式"""
        self.selection_window = SelectionWindow(global_opacity)
        self.selection_window.show()
        self.close()


class PreviewWindow(QWidget):
    def __init__(self, opacity):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.opacity = opacity

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, self.opacity))

    def mousePressEvent(self, event):
        """鼠标点击时退出预览"""
        if event.button() == Qt.LeftButton:
            self.close()


class SelectionWindow(QWidget):
    def __init__(self, preview_opacity):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.start_point = None
        self.end_point = None
        self.selection = QRect()  # 存储选中区域
        self.is_selecting = False
        self.preview_opacity = preview_opacity  # 预览时选择的亮度
        self.is_confirmed = False  # 是否确认了选区

    def paintEvent(self, event):
        painter = QPainter(self)
        # 画出半透明遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))  # 半透明背景

        # 如果已经有选区，绘制高亮的选中区域
        if not self.selection.isNull():
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.selection, Qt.transparent)  # 选区透明
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QColor(255, 255, 255))
            painter.drawRect(self.selection)

        # 如果选区已经确认，则应用亮度
        if self.is_confirmed:
            painter.fillRect(self.rect(), QColor(0, 0, 0, global_opacity))  # 使用全局亮度遮罩
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.selection, Qt.transparent)  # 显示选区

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_confirmed:
                # 如果已经确认选区，点击外部不再创建新选区
                return

            self.start_point = event.pos()
            self.is_selecting = True
            self.selection = QRect()

    def mouseMoveEvent(self, event):
        if self.is_selecting and self.start_point:
            self.end_point = event.pos()
            self.selection = QRect(self.start_point, self.end_point).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False

            # 弹出确认框，询问是否确认选择区域
            reply = QMessageBox.question(self, '确认', '确认选定此区域吗？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.is_confirmed = True  # 确认选区
                self.update()  # 更新显示遮罩

            else:
                self.selection = QRect()  # 如果取消选择，清除选区
                self.update()

    def wheelEvent(self, event):
        """Ctrl + 滚轮调节亮度"""
        global global_opacity
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            if event.angleDelta().y() > 0:  # 滚轮向上滚动
                global_opacity = min(global_opacity + 10, 255)
            else:  # 滚轮向下滚动
                global_opacity = max(global_opacity - 10, 50)
            self.update()

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Up:
                self.selection.moveTop(self.selection.top() - 10)
            elif event.key() == Qt.Key_Down:
                self.selection.moveTop(self.selection.top() + 10)
            elif event.key() == Qt.Key_Left:
                self.selection.moveLeft(self.selection.left() - 10)
            elif event.key() == Qt.Key_Right:
                self.selection.moveLeft(self.selection.left() + 10)
            elif event.key() == Qt.Key_C:  # 退出选择模式
                self.close()
            self.update()

    def closeEvent(self, event):
        if not self.is_confirmed:
            event.ignore()  # 如果没有确认选区，则不退出
            QMessageBox.warning(self, "警告", "请先确认选区！")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
