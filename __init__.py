from . import auto_load

auto_load.init()


def register():
	auto_load.register()


def unregister():
	auto_load.unregister()
