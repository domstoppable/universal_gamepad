import time

from PySide2.QtCore import *
from PySide2.QtWidgets import *

class Task(QThread):
	data = Signal(object)
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def run(self):
		length = 10
#		for i in range(length):
#			self.data.emit(length-i)
#			for i in range(100000000):
#				x = 5**3.2
		while True:
			print('.', end='')


def onData(data):
	print(data)

def onInterval():
	#print('.')
	pass

app = QApplication()
worker = Task()
worker.data.connect(onData)

timer = QTimer()
timer.setInterval(10)
timer.timeout.connect(onInterval)

window = QPushButton('Hello, world!')
window.setMinimumSize(640,480)
window.show()
window.clicked.connect(lambda: print('hi'))

worker.start()
timer.start()

app.exec_()