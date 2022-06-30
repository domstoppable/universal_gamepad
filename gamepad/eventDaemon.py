import threading

from PySide2.QtCore import *

import ctypes
from sdl2 import *

from .gamepad import Gamepad

_instance = None

def daemon():
	global _instance

	if _instance is None:
		_instance = GamepadDaemon()

	return _instance

class GamepadDaemon(QObject):
	gamepadConnected = Signal(Gamepad)
	gamepadDisconnected = Signal(Gamepad)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.workerThread = DaemonThread()
		self.workerThread.sdlEvent.connect(self.onSdlEvent)

	def onSdlEvent(self, event, joystickInstanceID=None):
		if event.type == SDL_JOYDEVICEADDED:
			pad = Gamepad.getGamepad(joystickInstanceID)
			pad.onConnected()

			self.gamepadConnected.emit(pad)

		if event.type == SDL_JOYDEVICEREMOVED:
			pad = Gamepad.getGamepad(event.jdevice.which)
			pad.onDisconnected()

			self.gamepadDisconnected.emit(pad)

		elif event.type == SDL_JOYBUTTONDOWN:
			pad = Gamepad.getGamepad(event.jbutton.which)
			pad.onButtonPressed(event.jbutton.button)

		elif event.type == SDL_JOYBUTTONUP:
			pad = Gamepad.getGamepad(event.jbutton.which)
			pad.onButtonReleased(event.jbutton.button)

		elif event.type == SDL_JOYHATMOTION:
			pad = Gamepad.getGamepad(event.jhat.which)
			pad.onHatChanged(event.jhat.hat, event.jhat.value)

		elif event.type == SDL_JOYAXISMOTION:
			pad = Gamepad.getGamepad(event.jaxis.which)
			pad.onAxisChanged(event.jaxis.axis, event.jaxis.value)

	def start(self):
		self.workerThread.start()

	def stop(self, timeout=3000):
		self.workerThread.stop()
		self.workerThread.wait(timeout)


class DaemonThread(QThread):
	sdlEvent = Signal(object, object)
	_shutdown = Signal()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._shutdown.connect(self.onShutdownRequested)

	def stop(self):
		self._shutdown.emit()

	def onShutdownRequested(self):
		self.running = False

	def run(self):
		SDL_Init(SDL_INIT_JOYSTICK)

		self.running = True

		while self.running:
			event = SDL_Event()

			while SDL_PollEvent(ctypes.byref(event)) != 0:
				if event.type == SDL_QUIT:
					running = False
					break
				else:
					instanceID = None
					if event.type == SDL_JOYDEVICEADDED:
						joystick = SDL_JoystickOpen(event.jdevice.which)
						instanceID = SDL_JoystickInstanceID(joystick)

					elif event.type in [SDL_JOYDEVICEREMOVED,SDL_JOYBUTTONDOWN,SDL_JOYBUTTONUP,SDL_JOYHATMOTION,SDL_JOYAXISMOTION]:
						instanceID = event.jdevice.which

					if instanceID is not None:
						self.sdlEvent.emit(event, instanceID)
						event = SDL_Event()
