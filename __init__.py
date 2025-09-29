from .slot_link.misc import OpenDocumentation
from .slot_link import package_key
from . import auto_load
import bpy


package_key.package_key = __package__

auto_load.init()


class SlotLinkAddonPreferences(bpy.types.AddonPreferences):
	bl_idname = __package__

	def draw(self, context):
		self.layout.operator(OpenDocumentation.bl_idname)


def register():
	auto_load.register()
	bpy.utils.register_class(SlotLinkAddonPreferences)

def unregister():
	bpy.utils.unregister_class(SlotLinkAddonPreferences)
	auto_load.unregister()
