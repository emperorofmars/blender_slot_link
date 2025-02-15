import bpy


class SlotLink(bpy.types.PropertyGroup):
	slot_handle: bpy.props.IntProperty(name="Slot Handle", default=-1) # type: ignore
	target: bpy.props.PointerProperty(type=bpy.types.Object, name="Target") # type: ignore


class AddSlotLink(bpy.types.Operator):
	bl_idname = "slot_link.add"
	bl_label = "Add Slot Link"
	bl_category = "Slot Link"
	bl_options = {"REGISTER", "UNDO"}

	index: bpy.props.IntProperty(name = "Slot Index", default=-1) # type: ignore

	def execute(self, context):
		slot_link = context.active_action.slot_link.add()
		slot_link.slot_handle = context.active_action.slots[self.index].handle
		return {"FINISHED"}


class RemoveSlotAssignment(bpy.types.Operator):
	bl_idname = "slot_link.remove"
	bl_label = "Remove Slot Link"
	bl_category = "Slot Link"
	bl_options = {"REGISTER", "UNDO"}

	index: bpy.props.IntProperty(default=-1) # type: ignore

	def invoke(self, context, event):
		return context.window_manager.invoke_confirm(self, event)

	def execute(self, context):
		context.active_action.slot_link.remove(self.index)
		return {"FINISHED"}


def register():
	bpy.types.Action.slot_link = bpy.props.CollectionProperty(type=SlotLink, name="Slot Links") # type: ignore
	bpy.types.Scene.slot_link_show_info = bpy.props.BoolProperty(name="Show Slot Link Info", default=True) # type: ignore

def unregister():
	if hasattr(bpy.types.Action, "slot_link"):
		del bpy.types.Action.slot_link
	if hasattr(bpy.types.Scene, "slot_link_show_info"):
		del bpy.types.Scene.slot_link_show_info
