from PySide2.QtWidgets import *

from gamepad.eventDaemon import *
from gamepad.gamepad import *
from gamepad.ui import ControllerWidget

def onPadConnected(pad):
	frame = ControllerWidget()
	frame.bindToGamepad(pad)
	window.layout().addWidget(frame)

app = QApplication()

window = QWidget()
window.setLayout(QHBoxLayout())
window.show()

daemon = GamepadDaemon()
daemon.gamepadConnected.connect(onPadConnected)
daemon.start()

app.aboutToQuit.connect(daemon.stop)
app.exec_()

