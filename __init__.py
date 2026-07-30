import bpy
from .slot_link import package_key, register_slot_link, unregister_slot_link


package_key.package_key = __package__


class SlotLinkAddonPreferences(bpy.types.AddonPreferences):
	bl_idname = package_key.package_key # pyright: ignore[reportAssignmentType]

	use_separate_editor: bpy.props.BoolProperty(name="Move Slot Link editor to separate Panel", default=False)
	hide_slot_link_list: bpy.props.BoolProperty(name="Hide the list of Slot Links (Use the Slot Panel instead)", default=False)
	hide_dopesheet_header_ui: bpy.props.BoolProperty(name="Hide Dopesheet header GUI", default=False)
	hide_documentation_link: bpy.props.BoolProperty(name="Hide Documentation link", default=False)

	def draw(self, context: bpy.types.Context):
		layout = self.layout
		layout.use_property_split = True
		if(bpy.app.version[0] < 5 or bpy.app.version[1] < 2):
			layout.operator("wm.url_open", text="Slot Link Documentation", icon="HELP").url = "https://docs.stfform.at/guide/blender/slot_link.html"
		else:
			layout.link(text="Slot Link Documentation", icon="HELP", url="https://docs.stfform.at/guide/blender/slot_link.html")

		layout.prop(self, "use_separate_editor")
		layout.prop(self, "hide_slot_link_list")
		layout.prop(self, "hide_dopesheet_header_ui")
		layout.prop(self, "hide_documentation_link")


def slot_link_docs():
	manual_map = (
		("bpy.ops.slot_link.*", ""),
		("bpy.types.slotlinktarget.*", ""),
		("bpy.types.slotlink.*", ""),
		("bpy.types.actionslotlink.*", ""),
		("bpy.types.action.slot_link.*", ""),
	)
	return "https://docs.stfform.at/guide/blender/slot_link.html", manual_map


def register():
	bpy.utils.register_class(SlotLinkAddonPreferences)
	bpy.utils.register_manual_map(slot_link_docs)
	register_slot_link()

def unregister():
	unregister_slot_link()
	bpy.utils.unregister_manual_map(slot_link_docs)
	bpy.utils.unregister_class(SlotLinkAddonPreferences)
