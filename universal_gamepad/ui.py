import xml.etree.ElementTree as ET

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from .gamepad import Button, Axis
from . import locateAsset

class Stick():
	def __init__(self, basePosition, radius, color, *args, **kwargs):
		super().__init__()

		self.basePosition = basePosition
		self.position = [*basePosition]
		self.radius = radius
		self.color = color

	def setHorizontalOffset(self, offset):
		self.position[0] = self.basePosition[0] + offset

	def setVerticalOffset(self, offset):
		self.position[1] = self.basePosition[1] + offset

	def render(self, painter):
		painter.save()
		painter.setBrush(self.color)
		painter.drawEllipse(
			self.position[0], self.position[1],
			self.radius*2, self.radius*2
		)
		painter.restore()

class Trigger():
	def __init__(self, basePosition, baseSize, color):
		super().__init__()

		self.basePosition = basePosition
		self.baseSize = baseSize
		self.value = 0
		self.color = color
		self.bgcolor = Qt.gray
		self.vertScale = 0

	def setValue(self, value):
		self.vertScale = value

	def drawRect(self, painter, scale, color):
		width = int(self.baseSize[0])
		height = int(self.baseSize[1]*scale)

		x = int(self.basePosition[0])
		y = int(self.basePosition[1])+self.baseSize[1]-height

		painter.fillRect(
			x,y,
			width,height,
			color
		)

	def render(self, painter):
		painter.save()

		self.drawRect(painter, 1.0, self.bgcolor)
		self.drawRect(painter, self.vertScale, self.color)

		painter.restore()

class ControllerWidget(QLabel):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.document = ET.parse(locateAsset('controller.svg'))

		for button in Button:
			self.setButtonState(button, False)

		self.stickAmplitude = 30

		self.cloneSticks()
		self.cloneTriggers()

		self.updateImage()

	def cloneSticks(self):
		self.sticks = {}
		for side in ['LEFT', 'RIGHT']:
			node = self.getElementById(f'{side}_STICK')
			node.set('visibility', 'hidden')

			radius = float(node.get('r'))
			x = float(node.get('cx'))-radius
			y = float(node.get('cy'))-radius
			self.sticks[side] = Stick(
				[x,y],
				radius,
				Qt.gray
			)

	def cloneTriggers(self):
		self.triggers = {}
		for side in ['LEFT', 'RIGHT']:
			node = self.getElementById(f'{side}_TRIGGER-pressed')
			node.set('visibility', 'hidden')
			self.triggers[side] = Trigger(
				[float(node.get('x')), float(node.get('y'))],
				[float(node.get('width')), float(node.get('height'))],
				Qt.red,
			)

	def updateImage(self):
		pixmap = QPixmap()
		pixmap.loadFromData(ET.tostring(self.document.getroot(), 'utf8'))

		self.setPixmap(pixmap)
		self.setMinimumSize(pixmap.size())
		self.setMaximumSize(pixmap.size())

	def setButtonState(self, button, pressed):
		node = self.getElementById(f'{button.name}-pressed')
		if node is not None:
			node.set('visibility', '' if pressed else 'hidden')
			self.updateImage()

	def setAxisValue(self, axis, value):
		side = 'LEFT' if axis.name.startswith('LEFT') else 'RIGHT'
		if axis.isStick():
			if axis.isHorizontal():
				self.sticks[side].setHorizontalOffset(value*self.stickAmplitude)
			else:
				self.sticks[side].setVerticalOffset(value*self.stickAmplitude)
		else:
			self.triggers[side].setValue(value)

		self.repaint()

	def getElementById(self, nodeID):
		return self.document.find(f".//*[@id='{nodeID}']")

	def updateStyle(self, node, styleValues):
		styleString = node.get('style')
		rules = styleString.split(';')
		pairs = {}
		for rule in rules:
			parts = rule.split(':')
			pairs[parts[0]] = parts[1]

		for key,value in styleValues.items():
			pairs[key] = value

		styleString = ''
		for key,value in pairs.items():
			styleString += f'{key}:{value};'

		node.set('style', styleString)

	def paintEvent(self, paintEvent):
		painter = QPainter(self)
		for side in ['LEFT', 'RIGHT']:
			self.triggers[side].render(painter)

		super().paintEvent(paintEvent)

		for side in ['LEFT', 'RIGHT']:
			self.sticks[side].render(painter)

	def bindToGamepad(self, gamepad):
		gamepad.buttonPressed.connect(lambda button: self.setButtonState(button, True))
		gamepad.buttonReleased.connect(lambda button: self.setButtonState(button, False))
		gamepad.axisChanged.connect(lambda axis, value: self.setAxisValue(axis, value))
