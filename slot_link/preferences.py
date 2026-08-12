import bpy

from . import package_key


__all__ = ["SlotLinkPreferences", "get_preferences"]


class SlotLinkPreferences(bpy.types.AddonPreferences):
	bl_idname = package_key.package_key # pyright: ignore[reportAssignmentType]

	use_separate_editor: bpy.props.BoolProperty(name="Move Slot Link editor to separate Panel", default=False)
	hide_slot_link_list: bpy.props.BoolProperty(name="Hide the list of Slot Links (Use the Slot Panel instead)", default=False)
	hide_dopesheet_header_ui: bpy.props.BoolProperty(name="Hide dopesheet header GUI", default=False)
	hide_documentation_link: bpy.props.BoolProperty(name="Hide documentation link", default=False)

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


def get_preferences() -> SlotLinkPreferences:
	return bpy.context.preferences.addons[package_key.package_key].preferences


def register():
	bpy.utils.register_class(SlotLinkPreferences)

def unregister():
	bpy.utils.unregister_class(SlotLinkPreferences)
