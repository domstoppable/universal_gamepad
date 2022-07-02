import os
import pkg_resources

def locateAsset(*path):
	resource = '/'.join(['assets'] + list(path))
	return pkg_resources.resource_filename(__name__, resource)

try:
	import sdl2dll
	import sdl2
except:
	os.environ["PYSDL2_DLL_PATH"] = locateAsset('.')
	import sdl2