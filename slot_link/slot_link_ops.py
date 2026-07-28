import bpy

from .link_applier import link_slots, prepare_all_data_blocks
from .slot_link import SlotLink


__all__ = ["AddSlotLink", "RemoveSlotLink", "LinkSlots", "PrepareLinks", "ClearScene"]


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
		for link in context.active_action.slot_link.links:
			if(link.slot_handle == self.slot_handle):
				return {"CANCELLED"}
		slot_link: SlotLink = context.active_action.slot_link.links.add()
		slot_link.slot_handle = self.slot_handle
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
