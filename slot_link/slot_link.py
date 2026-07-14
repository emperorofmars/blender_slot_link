import bpy


_slot_link_poll_type = None
"""
Filter for which objects will be available to link as a SlotLink's `target`.
I.e. when a Slot is of the type "KEY", show only Objects which instantiate a Mesh.
"""

def set_slot_link_poll_type(slot_link_poll_type: type | None):
	global _slot_link_poll_type
	_slot_link_poll_type = slot_link_poll_type

def _slot_link_poll(self, blender_object: bpy.types.Object) -> bool:
	global _slot_link_poll_type
	return _slot_link_poll_type is None or isinstance(blender_object.data, _slot_link_poll_type)


class SlotLink(bpy.types.PropertyGroup):
	"""
	Links an Actions Slot to a target `bpy.types.Object`.

	If the Slot has a type of i.e. `key_blocks`, it means this link is targeting the skape-keys of the mesh that is instantiated on the target object.

	`datablock_index` is used for in case the Slot has a type of `material` for example. Then the index points to the instantiated meshes material index.
	"""
	slot_handle: bpy.props.IntProperty(name="Slot Handle", default=-1) # type: ignore
	target: bpy.props.PointerProperty(type=bpy.types.Object, name="Target", description="The Object this Slot should animate", poll=_slot_link_poll) # type: ignore
	datablock_index: bpy.props.IntProperty(name="Datablock Index", description="The index of the Material/Nodetree/etc..", default=0, min=0) # type: ignore


class ActionSlotLink(bpy.types.PropertyGroup):
	"""
	Redefine a Blender Action to a full standalone animation.

	Holds a `SlotLink` object for each Slot of an Action.

	Additionally, it can indicate this "animation" to be a reset-animation.

	Or reference an "animation" that is set to be a reset-animation.
	If this is the case, when this "animation" is applied to the Scene, the reset-animation will be applied before, to put the Scene into a consistent state.
	"""
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

	def execute(self, context: bpy.types.Context) -> set:
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

	def execute(self, context: bpy.types.Context) -> set:
		context.active_action.slot_link.links.remove(self.index)
		return {"FINISHED"}


def register():
	bpy.types.Action.slot_link = bpy.props.PointerProperty(type=ActionSlotLink, name="Slot Link", options=set()) # type: ignore

def unregister():
	if hasattr(bpy.types.Action, "slot_link"):
		del bpy.types.Action.slot_link
