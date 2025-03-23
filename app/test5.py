import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGridLayout
from PyQt5.QtCore import Qt

app = QApplication(sys.argv)
window = QWidget()
grid_layout = QGridLayout()

label = QLabel("Hello PyQt5")
label.setAlignment(Qt.AlignCenter)
grid_layout.addWidget(label)

window.setLayout(grid_layout)
window.show()
sys.exit(app.exec_())
