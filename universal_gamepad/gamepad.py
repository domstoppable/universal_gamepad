from enum import Enum, auto

from PySide2.QtCore import *

import ctypes
from sdl2 import *

class Button(Enum):
	SOUTH = auto()
	EAST = auto()
	WEST = auto()
	NORTH = auto()
	BACK = auto()
	GUIDE = auto()
	START = auto()
	LEFT_STICK = auto()
	RIGHT_STICK = auto()
	LEFT_SHOULDER = auto()
	RIGHT_SHOULDER = auto()
	UP = auto()
	DOWN = auto()
	LEFT = auto()
	RIGHT = auto()
	MISC_1 = auto()
	PADDLE_1 = auto()
	PADDLE_2 = auto()
	PADDLE_3 = auto()
	PADDLE_4 = auto()
	TOUCHPAD = auto()
	MAX = auto()

class Axis(Enum):
	LEFT_X = auto()
	LEFT_Y = auto()
	LEFT_TRIGGER = auto()
	RIGHT_X = auto()
	RIGHT_Y = auto()
	RIGHT_TRIGGER = auto()
	# @TODO
	#DPAD_X = auto()
	#DPAD_Y = auto()

	def isStick(self):
		return self.isHorizontal() or self.isVertical()

	def isTrigger(self):
		return self.name.endswith('_TRIGGER')

	def isHorizontal(self):
		return self.name.endswith('_X')

	def isVertical(self):
		return self.name.endswith('_Y')

hatBitMap = [
	Button.UP,
	Button.RIGHT,
	Button.DOWN,
	Button.LEFT,
]

class Gamepad(QObject):
	connected = Signal()
	disconnected = Signal()

	buttonPressed = Signal(Button)
	buttonReleased = Signal(Button)
	axisChanged = Signal(Axis, float)

	_gamepads = {}

	# @TODO
	#buttonHeld = Signal(Button)

	@classmethod
	def getGamepad(cls, id=0):
		if id not in Gamepad._gamepads:
			Gamepad._gamepads[id] = Gamepad(id)

		return Gamepad._gamepads[id]

	def __init__(self, id, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.id = id
		self.sdl_joystick = None
		self.mapHatEventsToDpad = True
		self.hatValues = []

		self.buttonMap = {
			SDL_CONTROLLER_BUTTON_A: Button.SOUTH,
			SDL_CONTROLLER_BUTTON_B: Button.EAST,
			SDL_CONTROLLER_BUTTON_X: Button.WEST,
			SDL_CONTROLLER_BUTTON_Y: Button.NORTH,
			SDL_CONTROLLER_BUTTON_BACK: Button.BACK,
			SDL_CONTROLLER_BUTTON_GUIDE: Button.GUIDE,
			SDL_CONTROLLER_BUTTON_START: Button.START,
			SDL_CONTROLLER_BUTTON_LEFTSTICK: Button.LEFT_STICK,
			SDL_CONTROLLER_BUTTON_RIGHTSTICK: Button.RIGHT_STICK,
			SDL_CONTROLLER_BUTTON_LEFTSHOULDER: Button.LEFT_SHOULDER,
			SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: Button.RIGHT_SHOULDER,
			SDL_CONTROLLER_BUTTON_DPAD_UP: Button.UP,
			SDL_CONTROLLER_BUTTON_DPAD_DOWN: Button.DOWN,
			SDL_CONTROLLER_BUTTON_DPAD_LEFT: Button.LEFT,
			SDL_CONTROLLER_BUTTON_DPAD_RIGHT: Button.RIGHT,
			SDL_CONTROLLER_BUTTON_MISC1: Button.MISC_1,
			SDL_CONTROLLER_BUTTON_PADDLE1: Button.PADDLE_1,
			SDL_CONTROLLER_BUTTON_PADDLE2: Button.PADDLE_2,
			SDL_CONTROLLER_BUTTON_PADDLE3: Button.PADDLE_3,
			SDL_CONTROLLER_BUTTON_PADDLE4: Button.PADDLE_4,
			SDL_CONTROLLER_BUTTON_TOUCHPAD: Button.TOUCHPAD,
			SDL_CONTROLLER_BUTTON_MAX: Button.MAX,
		}

		self.axisMap = {
			SDL_CONTROLLER_AXIS_LEFTX: Axis.LEFT_X,
			SDL_CONTROLLER_AXIS_LEFTY: Axis.LEFT_Y,
			SDL_CONTROLLER_AXIS_TRIGGERLEFT: Axis.LEFT_TRIGGER,
			SDL_CONTROLLER_AXIS_RIGHTX: Axis.RIGHT_X,
			SDL_CONTROLLER_AXIS_RIGHTY: Axis.RIGHT_Y,
			SDL_CONTROLLER_AXIS_TRIGGERRIGHT: Axis.RIGHT_TRIGGER,
		}

	def onConnected(self):
		self.connected.emit()

	def onDisconnected(self):
		self.disconnected.emit()

	def onButtonPressed(self, sdlButton):
		button = self.mapButton(sdlButton)
		self.buttonPressed.emit(button)

	def onButtonReleased(self, sdlButton):
		button = self.mapButton(sdlButton)
		self.buttonReleased.emit(button)

	def onAxisChanged(self, sdlAxis, sdlValue):
		axis = self.mapAxis(sdlAxis)
		value = sdlValue / 32767
		value = max(min(value, 1.0), -1.0)

		self.axisChanged.emit(axis, value)

	def onHatChanged(self, hatIdx, value):
		while hatIdx > len(self.hatValues)-1:
			self.hatValues.append(0)

		oldValue = self.hatValues[hatIdx]
		self.hatValues[hatIdx] = value

		if self.mapHatEventsToDpad:
			horizontalChanged = False
			verticalChanged = True

			delta = oldValue ^ value
			for bit in range(4):
				mask = 1 << bit
				if delta & mask == mask:
					horizontalChanged = horizontalChanged or bit % 2 == 1
					verticalChanged = verticalChanged or bit % 2 == 0

					pressed = value & mask == mask
					if pressed:
						self.buttonPressed.emit(hatBitMap[bit])
					else:
						self.buttonReleased.emit(hatBitMap[bit])

	def mapButton(self, sdlButton):
		if sdlButton in self.buttonMap:
			return self.buttonMap[sdlButton]
		else:
			return sdlButton

	def mapAxis(self, sdlAxis):
		if sdlAxis in self.axisMap:
			return self.axisMap[sdlAxis]
		else:
			return sdlAxis

def getGUID(joystick):
    buffer = ctypes.create_string_buffer(33)
    guid = SDL_JoystickGetGUID(joystick)
    SDL_JoystickGetGUIDString(guid, buffer, 33)

    return buffer.value.decode('utf8')
