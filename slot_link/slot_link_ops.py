import bpy
from typing import Literal

from .link_applier import link_action, prepare_all_data_blocks
from .slot_link import SlotLink, SlotLinkTarget, poll_slot_link_target
from .util import are_all_actions_setup, context_valid, needs_migrate_2_0


__all__ = ["SetupSlotLink", "SetupAction", "RemoveSlotLink", "LinkSlots", "PrepareLinks", "ClearScene", "CreateNew", "DuplicateAction", "MigrateSlotLink_0_2"]


### TODO remove legacy data-model by 2027-08-01
class MigrateSlotLink_0_2(bpy.types.Operator):
	"""Migrate SlotLink Data.

	This is non destructive, and will allow you to specify multiple targets per Slot going forward!"""
	bl_idname = "slot_link.migrate_0_2"
	bl_label = "Please Migrate Slot Link Data"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return needs_migrate_2_0()

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


def _attempt_autosetup(slot: bpy.types.ActionSlot, slot_link: SlotLink):
	"""Try to determine the target for a Slot, if possible."""

	if(len(slot_link.targets) != 1):
		return

	slot_link_target: SlotLinkTarget = slot_link.targets[0]

	def is_unique(blender_object: bpy.types.Object, datablock_index: int = 0) -> bool:
		for other_slot_link in slot_link.id_data.slot_link.links:
			for other_slot in slot_link.id_data.slots:
				if(other_slot.handle == other_slot_link.slot_handle):
					break
			else:
				continue
			if(other_slot_link != slot_link and slot.target_id_type == other_slot.target_id_type):
				for other_target in other_slot_link.targets:
					if(other_target.target == blender_object):
						if(slot.target_id_type in ["MATERIAL", "NODETREE"] and other_target.datablock_index != datablock_index):
							return True
						else:
							return False
		return True

	if(len(slot.users()) == 1 and slot.target_id_type == "OBJECT" and poll_slot_link_target(slot_link_target, slot.users()[0]) and is_unique(slot.users()[0])): # pyright: ignore[reportArgumentType]
		slot_link_target.target = slot.users()[0]
		return

	poll_target = None
	num_poll_targets = 0
	for blender_object in bpy.data.objects:
		if(poll_slot_link_target(slot_link_target, blender_object)):
			poll_target = blender_object
			num_poll_targets += 1
	if(poll_target and num_poll_targets == 1):
		if(slot.target_id_type not in ["MATERIAL", "NODETREE"] and is_unique(poll_target)):
			slot_link_target.target = poll_target
		elif(len(slot.users()) == 1 and slot.target_id_type in ["MATERIAL", "NODETREE"] and poll_target.material_slots and len(poll_target.material_slots) > 0):
			for material_index, material in enumerate(poll_target.material_slots):
				if(is_unique(poll_target, material_index) and (slot.target_id_type == "MATERIAL" and slot.users()[0] == material.material or slot.target_id_type == "NODETREE" and slot.users()[0] == material.material.node_tree)):
					slot_link_target.target = poll_target
					slot_link_target.datablock_index = material_index
					break

def _ensure_slot_link(action: bpy.types.Action, slot: bpy.types.ActionSlot) -> SlotLink:
	for slot_link in action.slot_link.links:
		if(slot_link.slot_handle == slot.handle):
			return slot_link

	slot_link: SlotLink = action.slot_link.links.add()
	slot_link.slot_handle = slot.handle
	slot_link.targets.add()

	# Try to determine the target, if possible
	_attempt_autosetup(slot, slot_link)
	return slot_link


class SetupSlotLink(bpy.types.Operator):
	"""Setup an animation target for this Action-Slot.

	If unambiguously possible, assign the correct target."""
	bl_idname = "slot_link.add"
	bl_label = "Setup Slot Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	slot_handle: bpy.props.IntProperty(default=-1)

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return context_valid(context)

	def execute(self, context: bpy.types.Context) -> set:
		for slot in context.active_action.slots:
			if(slot.handle == self.slot_handle):
				break
		else:
			return {"CANCELLED"} # No slot for the `slot_handle`

		_ensure_slot_link(context.active_action, slot) # pyright: ignore[reportArgumentType]
		return {"FINISHED"}


class SetupAction(bpy.types.Operator):
	"""Setup Slot-Link animation targets for this Action.

	Targets will only be assigned if unambiguous.
	This won't modify already set up Slot-Links."""
	bl_idname = "slot_link.setup_action"
	bl_label = "Autosetup"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return context_valid(context) and not needs_migrate_2_0()

	def execute(self, context: bpy.types.Context) -> set:
		for slot in context.active_action.slots:
			_ensure_slot_link(context.active_action, slot) # pyright: ignore[reportArgumentType]
		return {"FINISHED"}


class SetupAllActions(bpy.types.Operator):
	"""Setup Slot Link animation targets for all Actions.

	Targets will be only assigned if unambiguous.
	This won't modify already set up Slot-Links."""
	bl_idname = "slot_link.setup_all_actions"
	bl_label = "Setup all Actions"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return not are_all_actions_setup() and not needs_migrate_2_0()

	def execute(self, context: bpy.types.Context) -> set:
		for action in bpy.data.actions:
			for slot in action.slots:
				_ensure_slot_link(action, slot) # pyright: ignore[reportArgumentType]
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
		return context_valid(context)

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
		return context_valid(context)

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
		return context_valid(context) and len(context.active_action.slot_link.links) > 0

	def execute(self, context: bpy.types.Context) -> set:
		context.active_action.slot_link.links.remove(self.index)
		return {"FINISHED"}


class ClearScene(bpy.types.Operator):
	"""Clear the Scene of animation data"""
	bl_idname = "slot_link.clear_scene"
	bl_label = "Clear Scene"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	full_reset: bpy.props.BoolProperty(name="Full Reset (also Clear NLA data)", default=False, description="Fully recreate all animation-data. This will remove all NLA data!")

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return len(bpy.data.actions) > 0

	def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]]:
		if(self.full_reset):
			return context.window_manager.invoke_confirm(self, event, title="Clear All Scene Animation Data", message="This will clear all NLA data!", icon="WARNING")
		else:
			return self.execute(context)

	def execute(self, context: bpy.types.Context) -> set:
		prepare_all_data_blocks(None, self.full_reset)
		return {"FINISHED"}


class PrepareLinks(bpy.types.Operator):
	"""Link the Action to everything in the specified Collection or the entire Scene.
	Prevents any other Actions from being linked anywhere."""
	bl_idname = "slot_link.prepare"
	bl_label = "Prepare"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	action: bpy.props.StringProperty(name="Action", default="", description="The action to prepare", search=lambda self, context, text: [a.name for a in bpy.data.actions], search_options=set())

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return len(bpy.data.actions) > 0

	def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]]:
		self.action = self.action if self.action else (context.active_action.name if context_valid(context) else "")
		return self.execute(context)

	def execute(self, context: bpy.types.Context) -> set:
		if(self.action == "" or self.action not in bpy.data.actions):
			return {"CANCELLED"}
		action: bpy.types.Action = bpy.data.actions[self.action]
		prepare_all_data_blocks(action)
		return {"FINISHED"}


class LinkSlots(bpy.types.Operator):
	"""Link the Action to everything in the specified Collection or the entire Scene.
	Link its Slots to the selected Slot-Link targets.

	If a Reset Animation is selected, it will be used to bring the Scene into a consistent state first."""
	bl_idname = "slot_link.link"
	bl_label = "Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	action: bpy.props.StringProperty(name="Action", default="", description="The action to link", search=lambda self, context, text: [a.name for a in bpy.data.actions], search_options=set())
	use_reset_animation: bpy.props.BoolProperty(name="Use Reset Animation", default=True, description="If a Reset Animation is selected, it will be used to bring the Scene into a consistent state")
	full_reset: bpy.props.BoolProperty(name="Full Reset (also Clear NLA data)", default=False, description="Fully recreate the animation-data. This will remove all NLA data!")

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return len(bpy.data.actions) > 0

	def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]]:
		self.action = self.action if self.action else (context.active_action.name if context_valid(context) else "")
		return self.execute(context)

	def execute(self, context: bpy.types.Context) -> set:
		if(self.action == "" or self.action not in bpy.data.actions):
			return {"CANCELLED"}
		action: bpy.types.Action = bpy.data.actions[self.action]

		link_action(context, action, self.use_reset_animation, self.full_reset)
		return {"FINISHED"}


class CreateNew(bpy.types.Operator):
	"""Create a new action and prepare it immediately"""
	bl_idname = "slot_link.create_new"
	bl_label = "Create New"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context: bpy.types.Context) -> set:
		action = bpy.data.actions.new("Action")
		prepare_all_data_blocks(action)
		return {"FINISHED"}


class DuplicateAction(bpy.types.Operator):
	"""Duplicate an action and link it immediately"""
	bl_idname = "slot_link.duplicate_action"
	bl_label = "Duplicate"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	action: bpy.props.StringProperty(name="Action", default="", description="The action to link", search=lambda self, context, text: [a.name for a in bpy.data.actions], search_options=set())

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return len(bpy.data.actions) > 0

	def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]]:
		self.action = self.action if self.action else (context.active_action.name if context_valid(context) else "")
		return self.execute(context)

	def execute(self, context: bpy.types.Context) -> set:
		if(self.action == "" or self.action not in bpy.data.actions):
			return {"CANCELLED"}
		action: bpy.types.Action = bpy.data.actions[self.action]

		link_action(context, action.copy(), True, False)
		return {"FINISHED"}


def register():
	bpy.utils.register_class(SetupSlotLink)
	bpy.utils.register_class(SetupAction)
	bpy.utils.register_class(SetupAllActions)
	bpy.utils.register_class(AddSlotLinkTarget)
	bpy.utils.register_class(RemoveSlotLinkTarget)
	bpy.utils.register_class(RemoveSlotLink)
	bpy.utils.register_class(ClearScene)
	bpy.utils.register_class(PrepareLinks)
	bpy.utils.register_class(LinkSlots)
	bpy.utils.register_class(CreateNew)
	bpy.utils.register_class(DuplicateAction)

	bpy.utils.register_class(MigrateSlotLink_0_2)

def unregister():
	bpy.utils.unregister_class(MigrateSlotLink_0_2)

	bpy.utils.unregister_class(DuplicateAction)
	bpy.utils.unregister_class(CreateNew)
	bpy.utils.unregister_class(LinkSlots)
	bpy.utils.unregister_class(PrepareLinks)
	bpy.utils.unregister_class(ClearScene)
	bpy.utils.unregister_class(RemoveSlotLink)
	bpy.utils.unregister_class(SetupAllActions)
	bpy.utils.unregister_class(SetupAction)
	bpy.utils.unregister_class(RemoveSlotLinkTarget)
	bpy.utils.unregister_class(AddSlotLinkTarget)
	bpy.utils.unregister_class(SetupSlotLink)
