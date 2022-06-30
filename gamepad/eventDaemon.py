import multiprocessing as mp

from PySide2.QtCore import *

import ctypes
from sdl2 import *

from .gamepad import Gamepad

_instance = None

sdlEventTypeObjectMap = {
	SDL_JOYDEVICEADDED:'jdevice',
	SDL_JOYDEVICEREMOVED:'jdevice',
	SDL_JOYBUTTONDOWN:'jbutton',
	SDL_JOYBUTTONUP:'jbutton',
	SDL_JOYHATMOTION:'jhat',
	SDL_JOYAXISMOTION:'jaxis',
}

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

		self.toWorkerQueue = mp.Queue()
		self.fromWorkerQueue = mp.Queue()
		self.daemon = mp.Process(target=daemonMain, args=(self.toWorkerQueue, self.fromWorkerQueue), daemon=True)

		self.workerPoller = QTimer()
		self.workerPoller.timeout.connect(self.pollWorker)
		self.setFps(200)

	def setFps(self, fps):
		self.workerPoller.setInterval(1000//fps)

	def onSdlEvent(self, event):
		pad = Gamepad.getGamepad(event.instanceID)
		if event.type == SDL_JOYDEVICEADDED:
			pad.onConnected()
			self.gamepadConnected.emit(pad)

		if event.type == SDL_JOYDEVICEREMOVED:
			pad.onDisconnected()
			self.gamepadDisconnected.emit(pad)

		elif event.type == SDL_JOYBUTTONDOWN:
			pad.onButtonPressed(event.button)

		elif event.type == SDL_JOYBUTTONUP:
			pad.onButtonReleased(event.button)

		elif event.type == SDL_JOYHATMOTION:
			pad.onHatChanged(event.hat, event.value)

		elif event.type == SDL_JOYAXISMOTION:
			pad.onAxisChanged(event.axis, event.value)

	def start(self):
		self.workerPoller.start()
		self.daemon.start()

	def stop(self, timeout=3):
		self.toWorkerQueue.put('quit')
		self.daemon.join(timeout)

	def pollWorker(self):
		while not self.fromWorkerQueue.empty():
			self.onSdlEvent(self.fromWorkerQueue.get())

def daemonMain(inputQueue, outputQueue):
	SDL_Init(SDL_INIT_JOYSTICK)

	running = True

	while running:
		event = SDL_Event()

		while SDL_PollEvent(ctypes.byref(event)) != 0:
			if event.type == SDL_QUIT:
				running = False
				break
			else:
				# SDL events won't serialize, but the event field (e.g., event.jdevice) will
				if event.type in sdlEventTypeObjectMap:
					eventField = getattr(event, sdlEventTypeObjectMap[event.type])

					# also, we have to open the device to receive events from it
					if event.type == SDL_JOYDEVICEADDED:
						joystick = SDL_JoystickOpen(event.jdevice.which)
						# jdevice.which is the index, but every other .which is the instanceID
						setattr(eventField, 'instanceID', SDL_JoystickInstanceID(joystick))
					else:
						setattr(eventField, 'instanceID', eventField.which)

					outputQueue.put(eventField)
					event = SDL_Event()

		while not inputQueue.empty():
			event = inputQueue.get()
			if event == 'quit':
				running = False
			else:
				print('daemon thread unknown event:', event)
