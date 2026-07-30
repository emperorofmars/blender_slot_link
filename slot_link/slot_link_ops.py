import bpy

from .link_applier import link_slots, prepare_all_data_blocks
from .slot_link import SlotLink, slot_link_poll


__all__ = ["AddSlotLink", "SetupAction", "RemoveSlotLink", "LinkSlots", "PrepareLinks", "ClearScene"]


def _attempt_autosetup(slot: bpy.types.ActionSlot, slot_link: SlotLink):
	"""Try to determine the target for a Slot, if possible"""

	def is_unique(blender_object: bpy.types.Object, datablock_index: int = 0) -> bool:
		for other_slot_link in slot_link.id_data.slot_link.links:
			if(other_slot_link != slot_link and other_slot_link.target == blender_object):
				if(slot.target_id_type in ["MATERIAL", "NODETREE"] and other_slot_link.datablock_index != datablock_index):
					return True
				else:
					return False
		return True

	if(len(slot.users()) == 1 and slot.target_id_type == "OBJECT" and slot_link_poll(slot_link, slot.users()[0]) and is_unique(slot.users()[0])): # pyright: ignore[reportArgumentType]
		slot_link.target = slot.users()[0]
		return

	poll_target = None
	num_poll_targets = 0
	for blender_object in bpy.data.objects:
		if(slot_link_poll(slot_link, blender_object)):
			poll_target = blender_object
			num_poll_targets += 1
	if(poll_target and num_poll_targets == 1):
		if(slot.target_id_type not in ["MATERIAL", "NODETREE"] and is_unique(poll_target)):
			slot_link.target = poll_target
		elif(len(slot.users()) == 1 and slot.target_id_type in ["MATERIAL", "NODETREE"] and poll_target.material_slots and len(poll_target.material_slots) > 0):
			for material_index, material in enumerate(poll_target.material_slots):
				if(is_unique(poll_target, material_index) and (slot.target_id_type == "MATERIAL" and slot.users()[0] == material.material or slot.target_id_type == "NODETREE" and slot.users()[0] == material.material.node_tree)):
					slot_link.target = poll_target
					slot_link.datablock_index = material_index
					break

def _ensure_slot_link(action: bpy.types.Action, slot: bpy.types.ActionSlot) -> SlotLink:
	for slot_link in action.slot_link.links:
		if(slot_link.slot_handle == slot.handle):
			return slot_link

	slot_link: SlotLink = action.slot_link.links.add()
	slot_link.slot_handle = slot.handle

	# Try to determine the target, if possible
	_attempt_autosetup(slot, slot_link)
	return slot_link


class AddSlotLink(bpy.types.Operator):
	"""Setup an animation target for this Action-Slot"""
	bl_idname = "slot_link.add"
	bl_label = "Setup Slot Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	slot_handle: bpy.props.IntProperty(default=-1)

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return hasattr(context, "active_action") and context.active_action is not None

	def execute(self, context: bpy.types.Context) -> set:
		for slot in context.active_action.slots:
			if(slot.handle == self.slot_handle):
				break
		else:
			return {"CANCELLED"} # No slot for the `slot_handle`

		_ensure_slot_link(context.active_action, slot) # pyright: ignore[reportArgumentType]
		return {"FINISHED"}


class SetupAction(bpy.types.Operator):
	"""Setup Slot Link animation targets for this Action.
	Targets will only be assigned if unambiguous.
	This won't modify existing Slot Links."""
	bl_idname = "slot_link.setup_action"
	bl_label = "Autosetup"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return hasattr(context, "active_action") and context.active_action is not None

	def execute(self, context: bpy.types.Context) -> set:
		for slot in context.active_action.slots:
			_ensure_slot_link(context.active_action, slot) # pyright: ignore[reportArgumentType]
		return {"FINISHED"}


class SetupAllActions(bpy.types.Operator):
	"""Setup Slot Link animation targets for all Actions.
	Targets will only be assigned if unambiguous.
	This won't modify existing Slot Links."""
	bl_idname = "slot_link.setup_all_actions"
	bl_label = "Setup Slot Link for all Actions"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context: bpy.types.Context) -> set:
		for action in bpy.data.actions:
			for slot in action.slots:
				_ensure_slot_link(action, slot) # pyright: ignore[reportArgumentType]
		return {"FINISHED"}


class RemoveSlotLink(bpy.types.Operator):
	"""Remove orphaned link"""
	bl_idname = "slot_link.remove"
	bl_label = "Remove Slot Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	index: bpy.props.IntProperty(default=-1)

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return hasattr(context, "active_action") and context.active_action is not None and len(context.active_action.slot_link.links) > 0

	def execute(self, context: bpy.types.Context) -> set:
		context.active_action.slot_link.links.remove(self.index)
		return {"FINISHED"}


class ClearScene(bpy.types.Operator):
	"""Clear the Scene of any animation data"""
	bl_idname = "slot_link.clear_scene"
	bl_label = "Clear Scene"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context: bpy.types.Context) -> set:
		prepare_all_data_blocks(None)
		return {"FINISHED"}


class PrepareLinks(bpy.types.Operator):
	"""Link the Action to everything in the Scene.
	Prevents any other Actions from being linked anywhere"""
	bl_idname = "slot_link.prepare"
	bl_label = "Prepare"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return hasattr(context, "active_action") and context.active_action is not None

	def execute(self, context: bpy.types.Context) -> set:
		prepare_all_data_blocks(context.active_action)
		return {"FINISHED"}


class LinkSlots(bpy.types.Operator):
	"""Link the Action to everything in the Scene.
	Link its Slots to the selected targets.
	If a Reset Animation is selected, it will be used to bring the Scene into a consistent state"""
	bl_idname = "slot_link.link"
	bl_label = "Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	use_reset: bpy.props.BoolProperty(name="Use Reset", default=True, description="If a Reset Animation is selected, it will be used to bring the Scene into a consistent state")

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return hasattr(context, "active_action") and context.active_action is not None

	def execute(self, context: bpy.types.Context) -> set:
		# Link the reset animation first if applicable
		current_frame = context.scene.frame_current
		action: bpy.types.Action = context.active_action # pyright: ignore[reportAssignmentType]
		if(self.use_reset and not action.slot_link.is_reset_animation and action.slot_link.reset_animation):
			link_slots(action.slot_link.reset_animation)
			context.scene.frame_set(1)
		# Link the desired action
		link_slots(action)
		context.scene.frame_set(current_frame)
		return {"FINISHED"}


def register():
	bpy.utils.register_class(AddSlotLink)
	bpy.utils.register_class(SetupAction)
	bpy.utils.register_class(SetupAllActions)
	bpy.utils.register_class(RemoveSlotLink)
	bpy.utils.register_class(ClearScene)
	bpy.utils.register_class(PrepareLinks)
	bpy.utils.register_class(LinkSlots)

def unregister():
	bpy.utils.unregister_class(LinkSlots)
	bpy.utils.unregister_class(PrepareLinks)
	bpy.utils.unregister_class(ClearScene)
	bpy.utils.unregister_class(RemoveSlotLink)
	bpy.utils.unregister_class(SetupAllActions)
	bpy.utils.unregister_class(SetupAction)
	bpy.utils.unregister_class(AddSlotLink)
