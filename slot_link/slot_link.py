import bpy


# Filter for which objects will be available to link as a SlotLink's `target`.
# I.e. when a Slot is of the type "KEY", show only Objects which instantiate a Mesh.
_slot_link_poll_type = None

def set_slot_link_poll_type(slot_link_poll_type: type):
	global _slot_link_poll_type
	_slot_link_poll_type = slot_link_poll_type

def _slot_link_poll(self, blender_object: bpy.types.Object) -> bool:
	global _slot_link_poll_type
	return _slot_link_poll_type == None or isinstance(blender_object.data, _slot_link_poll_type)


class SlotLink(bpy.types.PropertyGroup):
	slot_handle: bpy.props.IntProperty(name="Slot Handle", default=-1) # type: ignore
	target: bpy.props.PointerProperty(type=bpy.types.Object, name="Target", description="The Object this Slot should animate", poll=_slot_link_poll) # type: ignore
	datablock_index: bpy.props.IntProperty(name="Datablock Index", description="The index of the Material/Nodetree/etc..", default=0, min=0) # type: ignore


class ActionSlotLink(bpy.types.PropertyGroup):
	is_reset_animation: bpy.props.BoolProperty(name="Is Reset-Animation", description="Use this Action to reset every property to a desired default state", default=False) # type: ignore
	reset_animation: bpy.props.PointerProperty(type=bpy.types.Action, name="Reset Animation", description="On 'Link Slots', the Reset Animation will be used to reset the state of the entire scene", poll=lambda self, action: bpy.context.active_action != action and action.slot_link.is_reset_animation, options=set()) # type: ignore
	links: bpy.props.CollectionProperty(type=SlotLink, name="Slot Links", options=set()) # type: ignore
	active_index: bpy.props.IntProperty(name="Active Slot Link", options=set()) # type: ignore


class AddSlotLink(bpy.types.Operator):
	"""Setup a target for this Action-Slot"""
	bl_idname = "slot_link.add"
	bl_label = "Setup Slot Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	slot_handle: bpy.props.IntProperty(default=-1) # type: ignore

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return context.active_action is not None

	def execute(self, context: bpy.types.Context):
		for link in context.active_action.slot_link.links:
			if(link.slot_handle == self.slot_handle):
				return {"CANCELLED"}
		slot_link = context.active_action.slot_link.links.add()
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
	def poll(cls, context: bpy.types.Context):
		return context.active_action is not None and len(context.active_action.slot_link.links) > 0

	def execute(self, context: bpy.types.Context):
		context.active_action.slot_link.links.remove(self.index)
		return {"FINISHED"}


class UpdateLegacySlotLink(bpy.types.Operator):
	"""Upgrade from old Slot-Link version"""
	bl_idname = "slot_link.update_legacy"
	bl_label = "Upgrade Legacy Slot Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return context.active_action is not None and hasattr(context.active_action, "slot_links") and len(context.active_action.slot_links) > 0 and len(context.active_action.slot_link.links) == 0

	def execute(self, context: bpy.types.Context):
		for old_link in context.active_action.slot_links:
			new_link: SlotLink = context.active_action.slot_link.links.add()
			new_link.slot_handle = old_link.slot_handle
			new_link.target = old_link.target
			new_link.datablock_index = old_link.datablock_index
		return {"FINISHED"}


def register():
	bpy.types.Action.slot_link = bpy.props.PointerProperty(type=ActionSlotLink, name="Slot Link", options=set()) # type: ignore

	# todo Legacy, remove in the future
	bpy.types.Action.slot_links = bpy.props.CollectionProperty(type=SlotLink, name="Slot Links", options=set()) # type: ignore

def unregister():
	if hasattr(bpy.types.Action, "slot_link"):
		del bpy.types.Action.slot_link

	# todo Legacy, remove in the future
	if hasattr(bpy.types.Action, "slot_links"):
		del bpy.types.Action.slot_links
