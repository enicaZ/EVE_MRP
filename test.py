# test_pyside6.py
import sys
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import Qt

app = QApplication(sys.argv)
label = QLabel("Hello PySide6!")
label.setAlignment(Qt.AlignCenter)
label.resize(400, 300)
label.show()
sys.exit(app.exec())