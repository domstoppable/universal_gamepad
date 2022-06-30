import signal

import threading
import time

from PySide2.QtCore import *

from gamepad.eventDaemon import *
from gamepad.gamepad import *

def log(info):
	print(f'{int(time.time())}: {info}')

def onPadConnected(pad):
	log(f'{pad.id} Pad connected')

	pad.buttonPressed.connect(lambda button=None, pad=pad: log(f'{pad.id} Pressed  {button}'))
	pad.buttonReleased.connect(lambda button=None, pad=pad: log(f'{pad.id} Released {button}'))
	pad.axisChanged.connect(lambda axis=None, value=None, pad=pad: log(f'{pad.id} axis {axis} = {value}'))
	pad.disconnected.connect(lambda pad=pad: log(f'{pad.id} disconnected'))

def checkInterrupt():
	try:
		pass
	except KeyboardInterrupt:
		app.quit()


app = QCoreApplication()
daemon = GamepadDaemon()
daemon.gamepadConnected.connect(onPadConnected)

daemon.start()

timer = QTimer()
timer.timeout.connect(checkInterrupt)
timer.start(500)

app.exec_()
daemon.stop()
