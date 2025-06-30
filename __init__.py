from .slot_link import package_key
from . import auto_load
import bpy


package_key.package_key = __package__

auto_load.init()


class ExampleAddonPreferences(bpy.types.AddonPreferences):
	# This must match the add-on name, use `__package__`
	# when defining this for add-on extensions or a sub-module of a python package.
	bl_idname = __package__

	slot_link_show_info: bpy.props.BoolProperty(name="Show Info Text", default=True) # type: ignore

	def draw(self, context):
		self.layout.prop(self, "boolean")


def register():
	auto_load.register()
	bpy.utils.register_class(ExampleAddonPreferences)

def unregister():
	bpy.utils.unregister_class(ExampleAddonPreferences)
	auto_load.unregister()
