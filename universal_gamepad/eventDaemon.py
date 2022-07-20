import sys
import multiprocessing as mp
import logging

from PySide2.QtCore import *

import ctypes
from sdl2 import *

from .gamepad import Gamepad
from . import locateAsset

_instance = None

sdlEventTypeObjectMap = {
	SDL_CONTROLLERDEVICEADDED:   'cdevice',
	SDL_CONTROLLERDEVICEREMOVED: 'cdevice',
	SDL_CONTROLLERAXISMOTION:    'caxis',
	SDL_CONTROLLERBUTTONDOWN:    'cbutton',
	SDL_CONTROLLERBUTTONUP:      'cbutton',
}

def getGamepadDaemon():
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
		self.daemon = mp.Process(target=_daemonMain, args=(self.toWorkerQueue, self.fromWorkerQueue), daemon=True)

		self.workerPoller = QTimer()
		self.workerPoller.timeout.connect(self.pollWorker)
		self.setFps(200)
		self.quitOnKeyboardInterrupt = False

	def setFps(self, fps):
		self.workerPoller.setInterval(1000//fps)

	def onSdlEvent(self, event):
		pad = Gamepad.getGamepad(event.instanceID)
		if pad is not None:
			if event.type == SDL_CONTROLLERDEVICEADDED:
				pad.setGuid(event.guid)
				pad.onConnected()
				self.gamepadConnected.emit(pad)

			elif event.type == SDL_CONTROLLERDEVICEREMOVED:
				pad.onDisconnected()
				self.gamepadDisconnected.emit(pad)

			elif event.type == SDL_CONTROLLERBUTTONDOWN:
				pad.onButtonPressed(event.button)

			elif event.type == SDL_CONTROLLERBUTTONUP:
				pad.onButtonReleased(event.button)

			elif event.type == SDL_CONTROLLERAXISMOTION:
				pad.onAxisChanged(event.axis, event.value)

	def start(self):
		self.workerPoller.start()
		self.daemon.start()

	def stop(self, timeout=3):
		self.toWorkerQueue.put('quit')
		self.daemon.join(timeout)

	def addMapping(self, mapping):
		self.toWorkerQueue.put('mapping|' + mapping)

	def pollWorker(self):
		try:
			while not self.fromWorkerQueue.empty():
				self.onSdlEvent(self.fromWorkerQueue.get())
		except KeyboardInterrupt:
			if self.quitOnKeyboardInterrupt:
				QCoreApplication.instance().quit()



def _setHint(hint, value):
	SDL_SetHint(hint, ctypes.c_char_p(value.encode()))

def _addMapping(mapping):
	line_ctype = ctypes.c_char_p(mapping.encode())
	result = SDL_GameControllerAddMapping(line_ctype)

	if result == 1:
		logging.info('Added mapping: %s' % mapping)
	elif result == 0:
		logging.info('Updated mapping: %s' % mapping)
	else:
		logging.warning('Error with mapping: %s' % mapping)

def _daemonMain(inputQueue, outputQueue, extraMappings=None):
	sdlVersion = SDL_version()
	SDL_GetVersion(ctypes.byref(sdlVersion))
	logging.debug(f'SDL Version = {sdlVersion.major}.{sdlVersion.minor}.{sdlVersion.patch}')

	_setHint(SDL_HINT_JOYSTICK_HIDAPI_JOY_CONS, "1")
	_setHint(SDL_HINT_JOYSTICK_HIDAPI_PS4_RUMBLE, "1")
	_setHint(SDL_HINT_JOYSTICK_HIDAPI_PS5_RUMBLE, "1")
	_setHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, "1")

	SDL_Init(SDL_INIT_VIDEO|SDL_INIT_GAMECONTROLLER)

	running = True

	try:
		mappingsFile = open(locateAsset('extra-mappings.txt'), 'r')
		for line in mappingsFile:
			line = line.strip()
			if not line.startswith('#'):
				_addMapping(line)
	except:
		pass

	while running:
		try:
			event = SDL_Event()
			while SDL_WaitEventTimeout(ctypes.byref(event), 100) != 0:
				if event.type == SDL_QUIT:
					running = False
					break
				else:
					# SDL events won't serialize, but the event field (e.g., event.jdevice) will
					if event.type in sdlEventTypeObjectMap:
						eventField = getattr(event, sdlEventTypeObjectMap[event.type])

						if event.type == SDL_CONTROLLERDEVICEADDED:
							controller = SDL_GameControllerOpen(eventField.which)
							joystick = SDL_GameControllerGetJoystick(controller)
							setattr(eventField, 'instanceID', SDL_JoystickInstanceID(joystick))

							guid = SDL_JoystickGetGUID(joystick)
							guid_str = ctypes.create_string_buffer(64)
							SDL_JoystickGetGUIDString(guid, guid_str, 64)
							setattr(eventField, 'guid', guid_str.value)

							mapping = SDL_GameControllerMappingForGUID(guid)
						else:
							setattr(eventField, 'instanceID', eventField.which)

						outputQueue.put(eventField)
						event = SDL_Event()

			while not inputQueue.empty():
				event = inputQueue.get()
				if event == 'quit':
					running = False
				elif event.startswith('mapping|'):
					mapping = event.split('|', 1)[1]
					_addMapping(mapping)
				else:
					print(f'Gamepad daemon received unknown event {event}', file=sys.stderr)

		except KeyboardInterrupt:
			pass
