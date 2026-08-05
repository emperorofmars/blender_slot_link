import bpy

from .slot_link import SlotLink, find_slot, retrieve_animation_data_holder
from .util import blender_data_keys, blender_data_subkeys


__all__ = ["prepare_all_data_blocks", "link_slots"]


## Prepare animation_data

def _prepare_data_block(action: bpy.types.Action | None, blender_data_block: bpy.types.ID, full_reset: bool = False, clear_if_linked_already: bool = False):
	"""
	Clear the `animation_data` on a Blender ID.
	If an Action is provided, create new `animation_data`, set the Action, but no Slot.
	"""
	if(hasattr(blender_data_block, "animation_data")):
		if(full_reset):
			blender_data_block.animation_data_clear()
		if(action and not blender_data_block.animation_data):
			blender_data_block.animation_data_create()
		if(blender_data_block.animation_data):
			if(clear_if_linked_already): # Only remove the action if it is already linked, otherwise do nothing
				if(blender_data_block.animation_data.action == action):
					blender_data_block.animation_data.action = None
			else: # Link the action
				blender_data_block.animation_data.action = action
				if(action):
					blender_data_block.animation_data.action_slot = None

def prepare_all_data_blocks(action: bpy.types.Action | None, full_reset: bool = False, override_target_collection: bpy.types.Collection | None = None, clear_outside_target_collection: bool = False):
	"""
	Clear the `animation_data` on all Blender IDs.
	A full reset recreates the `AnimData` structs, removing all NLA data as well.

	If an Action is provided, set the action, but no slot.

	:param bpy.types.Action action: The action to set in the animation data.
	:param bool full_reset: Fully reset all animation data, including NLA.
	:param bpy.types.Collection | None override_target_collection: Override the actions SlotLink target collection. This happens when preparing a reset animation which may apply globally, but the intended action has a target collection set.
	:param bool clear_outside_target_collection: If the Action has a target collection, and it should be unlinked from outside the target collection.
	"""
	target_collection: bpy.types.Collection | None = override_target_collection if override_target_collection else (action.slot_link.target_collection if action else None)

	if(action):
		action.use_fake_user = True

	def check_subkeys(thing, clear_if_linked_already: bool = False):
		for sub_key in blender_data_subkeys:
			if(hasattr(thing, sub_key)):
				_prepare_data_block(action, getattr(thing, sub_key), full_reset, clear_if_linked_already)

	if(not target_collection): # Prepare everything in the scene
		for data_key in blender_data_keys:
			thing_type = getattr(bpy.data, data_key)
			for thing in thing_type:
				_prepare_data_block(action, thing, full_reset)
				check_subkeys(thing)
	else: # Only objects from the target_collection and resources instantiated on them
		if(clear_outside_target_collection):
			# Just in case the action was linked outside the collection before, clear scene of just this action.
			# Don't do this if applying an actions reset animation.
			for data_key in blender_data_keys:
				thing_type = getattr(bpy.data, data_key)
				for thing in thing_type:
					_prepare_data_block(action, thing, full_reset, True)
					check_subkeys(thing, True)

		# Prepare collection
		_prepare_data_block(action, target_collection, full_reset)
		for blender_object in target_collection.all_objects[:]:
			_prepare_data_block(action, blender_object, full_reset)
			if(blender_object.data):
				_prepare_data_block(action, blender_object.data, full_reset)
				check_subkeys(blender_object.data)
			if(blender_object.material_slots):
				for material_slot in blender_object.material_slots:
					material_slot: bpy.types.MaterialSlot = material_slot
					if(material_slot.material):
						_prepare_data_block(action, material_slot.material, full_reset)
						check_subkeys(material_slot.material)

	return True


## Link

def _set_animation_data(blender_thing: bpy.types.ID, action: bpy.types.Action, slot: bpy.types.ActionSlot):
	"""
	Set the Action and Slot in the `animation_data` of a Blender ID.
	"""
	if(not blender_thing.animation_data):
		blender_thing.animation_data_create()
	blender_thing.animation_data.action = action
	blender_thing.animation_data.action_slot = slot

def _link_slot(action: bpy.types.Action, slot: bpy.types.ActionSlot, slot_link: SlotLink, override_target_collection: bpy.types.Collection | None = None):
	"""
	Determine the animation target based on the `slot_link`.

	Set the `action` and `slot` to that targets `animation_data`.
	"""
	target_collection: bpy.types.Collection | None = override_target_collection if override_target_collection else action.slot_link.target_collection

	if(len(slot_link.targets) == 0): return
	for link_target in slot_link.targets:
		if(not link_target.target):
			continue
		target_object: bpy.types.Object = link_target.target
		if(target_collection and target_object not in target_collection.all_objects.values()):
			continue

		anim_data_holder = retrieve_animation_data_holder(slot.target_id_type, link_target.target, link_target.datablock_index)
		if(anim_data_holder):
			_set_animation_data(anim_data_holder, action, slot)

def link_slots(action: bpy.types.Action, full_reset: bool = False, override_target_collection: bpy.types.Collection | None = None, clear_outside_target_collection: bool = False):
	"""
	Link the Action to all data-blocks in the Scene.

	Links its Slots to the targets, determined by each Slots `slot_link`.

	:param bpy.types.Action action: The Action to link
	:param bool full_reset: Fully reset all animation data, including NLA
	:param bpy.types.Collection | None override_target_collection: Override the actions SlotLink target Collection
	"""
	prepare_all_data_blocks(action, full_reset, override_target_collection, clear_outside_target_collection)

	for slot_link in action.slot_link.links:
		if(slot := find_slot(action, slot_link.slot_handle)):
			_link_slot(action, slot, slot_link, override_target_collection)
