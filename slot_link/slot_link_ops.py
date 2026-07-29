import bpy

from .link_applier import link_slots, prepare_all_data_blocks
from .slot_link import SlotLink, slot_link_poll


__all__ = ["AddSlotLink", "RemoveSlotLink", "LinkSlots", "PrepareLinks", "ClearScene", "MigrateSlotLink_0_2"]


### TODO remove legacy data-model by 2027-08-01
class MigrateSlotLink_0_2(bpy.types.Operator):
	"""Migrate SlotLink Data.

	This is non destructive, and will allow you to specify multiple targets per Slot!"""

	bl_idname = "slot_link.migrate_0_2"
	bl_label = "Migrate Slot Link Data"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context: bpy.types.Context) -> set:
		for action in bpy.data.actions: # pyright: ignore[reportAssignmentType]
			for slot_link in action.slot_link.links:
				if(len(slot_link.targets) == 0):
					target = slot_link.targets.add()
					target.target = slot_link.target
					target.datablock_index = slot_link.datablock_index
				slot_link.target = None
				slot_link.datablock_index = 0
		return {"FINISHED"}


class AddSlotLink(bpy.types.Operator):
	"""Setup an animation target for this Action-Slot.

	If possible, already assign the correct target.
	"""
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
				return {"CANCELLED"} # SlotLink for this `slot_handle` already exists
		for slot in context.active_action.slots:
			if(slot.handle == self.slot_handle):
				break
		else:
			return {"CANCELLED"} # No slot for the `slot_handle`

		slot_link: SlotLink = context.active_action.slot_link.links.add()
		slot_link.slot_handle = self.slot_handle
		link_target = slot_link.targets.add()

		# Try to determine the target, if possible
		if(len(slot.users()) == 1):
			if(slot.target_id_type == "OBJECT"):
				link_target.target = slot.users()[0]
			else:
				poll_target = None
				num_poll_targets = 0
				for blender_object in bpy.data.objects:
					if(slot_link_poll(link_target, blender_object)):
						poll_target = blender_object
						num_poll_targets += 1
				if(poll_target and num_poll_targets == 1):
					link_target.target = poll_target
					if(slot.target_id_type in ["MATERIAL", "NODETREE"] and poll_target.material_slots and len(poll_target.material_slots) > 0):
						for material_index, material in enumerate(poll_target.material_slots):
							if(slot.target_id_type == "MATERIAL" and slot.users()[0] == material.material):
								link_target.datablock_index = material_index
								break
							elif(slot.target_id_type == "NODETREE" and slot.users()[0] == material.material.node_tree):
								link_target.datablock_index = material_index
								break
		return {"FINISHED"}


class AddSlotLinkTarget(bpy.types.Operator):
	"""Setup an additional animation target for this Action-Slot"""
	bl_idname = "slot_link.add_target"
	bl_label = "Add Target"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	slot_handle: bpy.props.IntProperty(default=-1)

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return hasattr(context, "active_action") and context.active_action is not None

	def execute(self, context: bpy.types.Context) -> set:
		for slot_link in context.active_action.slot_link.links:
			if(slot_link.slot_handle == self.slot_handle):
				break
		else:
			return {"CANCELLED"}
		slot_link.targets.add()
		return {"FINISHED"}


class RemoveSlotLinkTarget(bpy.types.Operator):
	"""Remove an animation target for this Action-Slot"""
	bl_idname = "slot_link.remove_target"
	bl_label = "Remove Target"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	slot_handle: bpy.props.IntProperty(default=-1)
	target_index: bpy.props.IntProperty(default=-1)

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return hasattr(context, "active_action") and context.active_action is not None

	def execute(self, context: bpy.types.Context) -> set:
		for slot_link in context.active_action.slot_link.links:
			if(slot_link.slot_handle == self.slot_handle):
				break
		else:
			return {"CANCELLED"}
		if(len(slot_link.targets) <= self.target_index):
			return {"CANCELLED"}

		if(len(slot_link.targets) <= 1):
			# Only reset the last remaining target. This is only possible if the operator is called directly. The SlotLink gui won't shot the delete-button if only one target remains.
			slot_link.targets[self.target_index].target = None
			slot_link.targets[self.target_index].datablock_index = 0
		else:
			# Actually delete the target
			slot_link.targets.remove(self.target_index)
		return {"FINISHED"}


class RemoveSlotLink(bpy.types.Operator):
	"""Remove orphaned link"""
	bl_idname = "slot_link.remove"
	bl_label = "Remove Orphaned Link"
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
	bpy.utils.register_class(AddSlotLinkTarget)
	bpy.utils.register_class(RemoveSlotLinkTarget)
	bpy.utils.register_class(RemoveSlotLink)
	bpy.utils.register_class(ClearScene)
	bpy.utils.register_class(PrepareLinks)
	bpy.utils.register_class(LinkSlots)
	bpy.utils.register_class(MigrateSlotLink_0_2)

def unregister():
	bpy.utils.unregister_class(MigrateSlotLink_0_2)
	bpy.utils.unregister_class(LinkSlots)
	bpy.utils.unregister_class(PrepareLinks)
	bpy.utils.unregister_class(ClearScene)
	bpy.utils.unregister_class(RemoveSlotLink)
	bpy.utils.unregister_class(RemoveSlotLinkTarget)
	bpy.utils.unregister_class(AddSlotLinkTarget)
	bpy.utils.unregister_class(AddSlotLink)
