from .slot_link.misc import OpenDocumentation
from .slot_link import package_key
from . import auto_load
import bpy


package_key.package_key = __package__

auto_load.init()


class SlotLinkAddonPreferences(bpy.types.AddonPreferences):
	bl_idname = package_key.package_key  # pyright: ignore[reportAssignmentType]

	use_separate_editor: bpy.props.BoolProperty(name="Move SlotLink editor to separate Panel", default=False)
	hide_dopesheet_header_ui: bpy.props.BoolProperty(name="Hide Dopesheet header GUI", default=False)

	def draw(self, context: bpy.types.Context):
		layout = self.layout
		layout.use_property_split = True
		if(bpy.app.version[0] < 5 or bpy.app.version[1] < 2):
			layout.operator(OpenDocumentation.bl_idname, icon="HELP")
		else:
			layout.link(text="Slot Link Documentation", icon="HELP", url="https://docs.stfform.at/guide/blender/slot_link.html")

		layout.prop(self, "use_separate_editor")
		layout.prop(self, "hide_dopesheet_header_ui")


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
