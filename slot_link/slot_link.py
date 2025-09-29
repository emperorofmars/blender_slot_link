import bpy


_slot_link_poll_type = None
def set_slot_link_poll_type(slot_link_poll_type: type):
	global _slot_link_poll_type
	_slot_link_poll_type = slot_link_poll_type

def _slot_link_poll(self, blender_object: bpy.types.Object) -> bool:
	global _slot_link_poll_type
	return _slot_link_poll_type == None or type(blender_object.data) == _slot_link_poll_type


class SlotLink(bpy.types.PropertyGroup):
	slot_handle: bpy.props.IntProperty(name="Slot Handle", default=-1) # type: ignore
	target: bpy.props.PointerProperty(type=bpy.types.Object, name="Target", poll=_slot_link_poll) # type: ignore
	datablock_index: bpy.props.IntProperty(name="Datablock Index", default=0, min=0) # type: ignore


class AddSlotLink(bpy.types.Operator):
	bl_idname = "slot_link.add"
	bl_label = "Add Slot Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	index: bpy.props.IntProperty(name = "Slot Index", default=-1) # type: ignore

	@classmethod
	def poll(cls, context): return context.active_action is not None

	def execute(self, context):
		slot_link = context.active_action.slot_links.add()
		slot_link.slot_handle = context.active_action.slots[self.index].handle
		return {"FINISHED"}


class RemoveSlotLink(bpy.types.Operator):
	bl_idname = "slot_link.remove"
	bl_label = "Remove Slot Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	index: bpy.props.IntProperty(default=-1) # type: ignore

	@classmethod
	def poll(cls, context): return context.active_action is not None

	def invoke(self, context, event):
		return context.window_manager.invoke_confirm(self, event)

	def execute(self, context):
		context.active_action.slot_links.remove(self.index)
		return {"FINISHED"}


def register():
	bpy.types.Action.slot_links = bpy.props.CollectionProperty(type=SlotLink, name="Slot Links") # type: ignore
	bpy.types.Action.slot_links_active_index = bpy.props.IntProperty(name="Active Slot Link") # type: ignore

def unregister():
	if hasattr(bpy.types.Action, "slot_links"):
		del bpy.types.Action.slot_links
