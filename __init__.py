from .slot_link.misc import OpenDocumentation
from .slot_link import package_key
from . import auto_load
import bpy


package_key.package_key = __package__

auto_load.init()


class SlotLinkAddonPreferences(bpy.types.AddonPreferences):
	bl_idname = __package__

	def draw(self, context):
		self.layout.operator(OpenDocumentation.bl_idname, icon="HELP")


def slot_link_docs():
	manual_map = (
		("bpy.ops.slot_link.*", ""),
		("bpy.types.slotlink.*", ""),
		("bpy.types.actionslotlink.*", ""),
		("bpy.types.action.slot_link.*", ""),
	)
	return "https://docs.stfform.at/guide/blender/slot_link.html", manual_map


def register():
	auto_load.register()
	bpy.utils.register_class(SlotLinkAddonPreferences)
	bpy.utils.register_manual_map(slot_link_docs)

def unregister():
	bpy.utils.unregister_manual_map(slot_link_docs)
	bpy.utils.unregister_class(SlotLinkAddonPreferences)
	auto_load.unregister()
