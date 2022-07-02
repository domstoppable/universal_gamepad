import signal

import threading
import time

from PySide2.QtCore import *

from universal_gamepad.eventDaemon import *
from universal_gamepad.gamepad import *

def log(info):
	print(f'{float(time.time()):0.3f}: {info}')

def onPadConnected(pad):
	log(f'{pad.id} Pad connected')

	pad.buttonPressed.connect(lambda button=None, pad=pad: log(f'{pad.id} Pressed  {button}'))
	pad.buttonReleased.connect(lambda button=None, pad=pad: log(f'{pad.id} Released {button}'))
	pad.axisChanged.connect(lambda axis=None, value=None, pad=pad: log(f'{pad.id} axis {axis} = {value}'))


if __name__ == '__main__':
	import multiprocessing as mp
	mp.freeze_support()

	app = QCoreApplication()
	daemon = getGamepadDaemon()
	daemon.quitOnKeyboardInterrupt = True
	daemon.gamepadConnected.connect(onPadConnected)
	daemon.gamepadDisconnected.connect(lambda pad: log(f'{pad.id} disconnected'))

	daemon.start()

	app.exec_()
	daemon.stop()
