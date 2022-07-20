#!/usr/bin/env python

from setuptools import setup

setup(
	name='universal_gamepad',
	version='0.1',
	description='A cross-platform package that attempts to provide a universal game controller interface',
	author='Dominic Canare',
	author_email='dom@dominiccanare.com',
	url='https://github.com/domstoppable/universal_gamepad',
	packages=['universal_gamepad',],
	package_data={
		'universal_gamepad': ['universal_gamepad/assets/*'],
	},
	include_package_data=True,
	install_requires=[ 'PySide2', 'pysdl2', 'pysdl2-dll', ],
)
