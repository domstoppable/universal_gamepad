import pkg_resources

def locateAsset(*path):
	resource = '/'.join(['assets'] + list(path))
	return pkg_resources.resource_filename(__name__, resource)