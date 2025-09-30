import bpy


# Filter for which objects will be available to link as a SlotLink's `target`.
# I.e. when a Slot is of the type "KEY", show only Objects which instantiate a Mesh.
_slot_link_poll_type = None

def set_slot_link_poll_type(slot_link_poll_type: type):
	global _slot_link_poll_type
	_slot_link_poll_type = slot_link_poll_type

def _slot_link_poll(self, blender_object: bpy.types.Object) -> bool:
	global _slot_link_poll_type
	return _slot_link_poll_type == None or type(blender_object.data) == _slot_link_poll_type


class SlotLink(bpy.types.PropertyGroup):
	slot_handle: bpy.props.IntProperty(name="Slot Handle", default=-1) # type: ignore
	target: bpy.props.PointerProperty(type=bpy.types.Object, name="Target", description="The Object this Slot should animate", poll=_slot_link_poll) # type: ignore
	datablock_index: bpy.props.IntProperty(name="Datablock Index", description="The index of the Material/Nodetree/etc..", default=0, min=0) # type: ignore


class AddSlotLink(bpy.types.Operator):
	"""Setup a target for this Action-Slot"""
	bl_idname = "slot_link.add"
	bl_label = "Setup Slot Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	slot_handle: bpy.props.IntProperty(default=-1) # type: ignore

	@classmethod
	def poll(cls, context: bpy.types.Context): return context.active_action is not None

	def execute(self, context: bpy.types.Context):
		slot_link = context.active_action.slot_links.add()
		slot_link.slot_handle = self.slot_handle
		return {"FINISHED"}


class RemoveSlotLink(bpy.types.Operator):
	"""Remove orphaned link"""
	bl_idname = "slot_link.remove"
	bl_label = "Remove Slot Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	index: bpy.props.IntProperty(default=-1) # type: ignore

	@classmethod
	def poll(cls, context: bpy.types.Context): return context.active_action is not None

	def execute(self, context: bpy.types.Context):
		context.active_action.slot_links.remove(self.index)
		return {"FINISHED"}


def register():
	bpy.types.Action.slot_links = bpy.props.CollectionProperty(type=SlotLink, name="Slot Links", options=set()) # type: ignore
	bpy.types.Action.slot_links_active_index = bpy.props.IntProperty(name="Active Slot Link", options=set()) # type: ignore

def unregister():
	if hasattr(bpy.types.Action, "slot_links"):
		del bpy.types.Action.slot_links
	if hasattr(bpy.types.Action, "slot_links_active_index"):
		del bpy.types.Action.slot_links_active_index
