import bpy
from enum import Enum
from dataclasses import dataclass

from .slot_link import SlotLinkTarget, find_slot_link, retrieve_animation_data_holder
from .util import blender_data_keys, blender_data_subkeys, needs_migrate_2_0


__all__ = ["is_action_linked", "check_slot_link_target_unique", "check_slot_link_all_targets_unique", "SlotLinkError", "SlotLinkActionState", "validate_action", "is_nla_clean"]


def _has_animation_data(blender_data_block: bpy.types.ID) -> bool:
	"""Check if the `blender_data_block` has valid `animation_data`"""
	if(hasattr(blender_data_block, "animation_data") and blender_data_block.animation_data is not None):
		return True
	else:
		return False

def _check_action_in_data_block(action: bpy.types.Action, blender_data_block: bpy.types.ID) -> bool:
	"""Check if the action is linked to the `blender_data_block`"""
	if(not hasattr(blender_data_block, "animation_data")):
		return True
	if(blender_data_block.animation_data is None or blender_data_block.animation_data.action != action):
		return False
	return True

def is_action_linked(action: bpy.types.Action) -> bool:
	"""Check if the action is linked correctly throughout the scene or target collection"""
	if(not action):
		return False
	target_collection: bpy.types.Collection | None = action.slot_link.target_collection

	def check_subkeys(thing) -> bool:
		for sub_key in blender_data_subkeys:
			if(hasattr(thing, sub_key)):
				if(not _check_action_in_data_block(action, getattr(thing, sub_key))):
					return False
		return True

	if(not target_collection):
		for data_key in blender_data_keys:
			thing_type = getattr(bpy.data, data_key)
			for thing in thing_type:
				if(not _check_action_in_data_block(action, thing) or not check_subkeys(thing)):
					return False
	else:
		if(not _check_action_in_data_block(action, target_collection) or not check_subkeys(target_collection)):
			return False

		for blender_object in target_collection.all_objects[:]:
			if(not _check_action_in_data_block(action, blender_object) or not check_subkeys(blender_object)):
				return False
			if(blender_object.data):
				if(not _check_action_in_data_block(action, blender_object.data) or not check_subkeys(blender_object.data)):
					return False
			if(blender_object.material_slots):
				for material_slot in blender_object.material_slots:
					material_slot: bpy.types.MaterialSlot = material_slot
					if(material_slot.material):
						if(not _check_action_in_data_block(action, material_slot.material) or not check_subkeys(material_slot.material)):
							return False

	for slot in action.slots:
		slot_link = find_slot_link(action, slot.handle)
		if(not slot_link):
			return False # No slot link setup for this slot

		if(len(slot.users()) > len(slot_link.targets)):
			return False # The slot is used somewhere where it is not targeted

		valid_targets = 0
		for link_target in slot_link.targets:
			target_object: bpy.types.Object = link_target.target
			if(not target_object):
				continue  # If a target is not set, then there will be one less user. It is still linked correctly.

			if(target_collection and target_object not in target_collection.all_objects.values()):
				return False # Animated object is not part of the target collection

			anim_data_holder = retrieve_animation_data_holder(slot.target_id_type, link_target.target, link_target.datablock_index)
			if(not anim_data_holder or not _has_animation_data(anim_data_holder) or anim_data_holder.animation_data.action_slot != slot):
				return False # Slot is not mapped to the link_target

			valid_targets += 1

		if(len(slot.users()) > valid_targets):
			return False # The slot is used somewhere where it is not targeted

	return True


def _slot_targets_unique(target_id_type: str, a: SlotLinkTarget, b: SlotLinkTarget) -> bool:
	return a == b or a.target != b.target or target_id_type in ["MATERIAL", "NODETREE"] and a.datablock_index != b.datablock_index

def check_slot_link_target_unique(action: bpy.types.Action, slot: bpy.types.ActionSlot, link_target: SlotLinkTarget) -> bool:
	"""Check if this Slot's `link_target` isn't used by any other Slot with the same `target_id_type` or by another of its own targets"""
	slot_link = find_slot_link(action, slot.handle)
	if(not slot_link):
		return True
	for check_target in slot_link.targets:
		if(not _slot_targets_unique(slot.target_id_type, link_target, check_target)):
			return False
	for check_slot in action.slots:
		if(check_slot == slot or check_slot.target_id_type != slot.target_id_type):
			continue
		check_slot_link = find_slot_link(action, check_slot.handle)
		if(not check_slot_link):
			continue
		for check_target in check_slot_link.targets:
			if(not _slot_targets_unique(slot.target_id_type, link_target, check_target)):
				return False
	return True

def check_slot_link_all_targets_unique(action: bpy.types.Action, slot: bpy.types.ActionSlot) -> bool:
	"""Check if this Slot's `target` isn't used by any other Slot with the same `target_id_type`"""
	slot_link = find_slot_link(action, slot.handle)
	if(not slot_link):
		return True
	for link_target in slot_link.targets:
		if(not check_slot_link_target_unique(action, slot, link_target)):
			return False
	return True


class SlotLinkError(Enum):
	NOT_LINKED = 1
	NOT_PREPARED = 2
	NO_SLOT = 3
	SLOTS_NOT_SETUP = 4
	SLOTS_MISSING_TARGET = 5
	SLOTS_INVALID_MATERIAL_INDEX = 6
	SLOTS_DUPLICATE_TARGETS = 7
	TARGETS_OUTSIDE_COLLECTION = 8
	MIGRATION_2_0_NEEDED = -1

@dataclass
class SlotLinkActionState():
	ok: bool
	error: SlotLinkError | None = None

def validate_action(action: bpy.types.Action) -> SlotLinkActionState:
	"""Determine the state of an Action"""

	if(needs_migrate_2_0()):
		return SlotLinkActionState(False, SlotLinkError.MIGRATION_2_0_NEEDED)

	if(action.is_action_legacy):
		if(action.users <= 1): # good enough
			return SlotLinkActionState(False, SlotLinkError.NOT_PREPARED)
		else:
			return SlotLinkActionState(False, SlotLinkError.NO_SLOT)
	if(len(action.slots.values()) == 0):
			return SlotLinkActionState(False, SlotLinkError.NO_SLOT)

	# Check if some Slots are to be linked to the same datablock
	for slot in action.slots:
		if(not check_slot_link_all_targets_unique(action, slot)):
			return SlotLinkActionState(False, SlotLinkError.SLOTS_DUPLICATE_TARGETS)

	# Check if all Slots have valid targets
	successes = 0
	for slot in action.slots:
		slot_link = find_slot_link(action, slot.handle)
		if(not slot_link):
			return SlotLinkActionState(False, SlotLinkError.SLOTS_NOT_SETUP)

		if(slot_link and len(slot_link.targets) > 0): # TODO check if the target supports all animated properties
			link_target_successes = 0
			for link_target in slot_link.targets:
				if(not link_target.target):
					break
				if(action.slot_link.target_collection and link_target.target not in action.slot_link.target_collection.all_objects.values()):
					return SlotLinkActionState(False, SlotLinkError.TARGETS_OUTSIDE_COLLECTION)
				if(slot.target_id_type in ["MATERIAL", "NODETREE"]):
					valid_material = True
					if(link_target.target.material_slots and len(link_target.target.material_slots) <= link_target.datablock_index):
						valid_material = False
					elif(not link_target.target.material_slots[link_target.datablock_index].material):
						valid_material = False
					elif(slot.target_id_type == "NODETREE" and not link_target.target.material_slots[link_target.datablock_index].material.node_tree):
						valid_material = False
					if(not valid_material):
						return SlotLinkActionState(False, SlotLinkError.SLOTS_INVALID_MATERIAL_INDEX)
				link_target_successes += 1
			if(len(slot_link.targets) == link_target_successes):
				successes += 1
	if(successes < len(action.slots)):
		return SlotLinkActionState(False, SlotLinkError.SLOTS_MISSING_TARGET)

	# Check whether this Action is linked everywhere correctly
	if(not is_action_linked(action)):
		return SlotLinkActionState(False, SlotLinkError.NOT_LINKED)

	return SlotLinkActionState(True)


def is_nla_clean() -> bool:
	def _is_datablock_clean(thing):
		if(not hasattr(thing, "animation_data") or not thing.animation_data):
			return True
		animdata: bpy.types.AnimData = thing.animation_data
		if(animdata.use_nla and animdata.nla_tracks is not None and len(animdata.nla_tracks) > 0):
			return False
		return True

	def _check_subkeys(thing):
		for sub_key in blender_data_subkeys:
			if(hasattr(thing, sub_key)):
				if(not _is_datablock_clean(getattr(thing, sub_key))):
					return False
		return True

	for data_key in blender_data_keys:
		thing_type = getattr(bpy.data, data_key)
		for thing in thing_type:
			if(not _is_datablock_clean(thing) or not _check_subkeys(thing)):
				return False

	return True

