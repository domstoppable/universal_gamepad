from PySide2.QtWidgets import *

from universal_gamepad.eventDaemon import *
from universal_gamepad.gamepad import *
from universal_gamepad.ui import ControllerWidget

padWidgets = {}

def removeWidget(widget):
		window.layout().takeAt(window.layout().indexOf(widget))
		widget.setParent(None)

def onPadConnected(pad):
	padWidgets[pad] = ControllerWidget()
	padWidgets[pad].bindToGamepad(pad)
	window.layout().addWidget(padWidgets[pad])

	window.layout().removeWidget(pluginLabel)
	pluginLabel.setParent(None)

def onPadDisconnected(pad):
	if pad in padWidgets:
		window.layout().takeAt(window.layout().indexOf(padWidgets[pad]))
		padWidgets[pad].setParent(None)

		if window.layout().count() == 0:
			window.layout().addWidget(pluginLabel)

if __name__ == '__main__':
	import multiprocessing as mp
	mp.freeze_support()

	app = QApplication()

	window = QWidget()
	window.setLayout(QHBoxLayout())

	pluginLabel = QLabel('Please connect a controller')
	pluginLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
	pluginLabel.setMargin(200)
	window.layout().addWidget(pluginLabel)

	daemon = GamepadDaemon()
	daemon.gamepadConnected.connect(onPadConnected)
	daemon.gamepadDisconnected.connect(onPadDisconnected)
	daemon.start()

	app.aboutToQuit.connect(daemon.stop)

	window.show()
	app.exec_()
