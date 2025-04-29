from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                            QScrollArea, QPushButton)

class CorrectDynamicScrollArea(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        
        # 滚动区域设置
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        
        # 内容Widget和布局
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        
        # 初始内容
        for i in range(5):
            self.content_layout.addWidget(QPushButton(f"初始按钮 {i+1}"))
        
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)
        
        # 添加删除按钮
        add_btn = QPushButton("添加新组件")
        add_btn.clicked.connect(self.add_component)
        layout.addWidget(add_btn)
        
        del_btn = QPushButton("删除最后组件")
        del_btn.clicked.connect(self.remove_component)
        layout.addWidget(del_btn)
    
    def add_component(self):
        new_btn = QPushButton(f"动态添加 {self.content_layout.count()+1}")
        self.content_layout.addWidget(new_btn)
    
    def remove_component(self):
        if self.content_layout.count() > 0:
            item = self.content_layout.takeAt(self.content_layout.count()-1)
            if item.widget():
                item.widget().deleteLater()

app = QApplication([])
window = CorrectDynamicScrollArea()
window.show()
app.exec_()