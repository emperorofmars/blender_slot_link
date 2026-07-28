import bpy

from .slot_link import SlotLink, find_slot_link

__all__ = ["check_action", "check_slot_link_target_unique", "prepare_all_data_blocks", "link_slots"]


# why u no polymorphism?
_blender_data_keys = ["armatures", "brushes", "cache_files", "cameras", "collections", "curves", "fonts", "grease_pencils", "images", "lattices", "libraries", "lights", "lightprobes", "linestyles", "masks", "materials", "meshes", "metaballs", "movieclips", "node_groups", "objects", "paint_curves", "palettes", "particles", "pointclouds", "scenes", "screens", "sounds", "speakers", "texts", "textures", "volumes", "window_managers", "workspaces", "worlds"]
_blender_data_subkeys = ["node_tree", "shape_keys", "compositing_node_group"]


## Check

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

def check_action(action: bpy.types.Action) -> bool:
	"""Check if the action is linked correctly throughout the Scene"""
	for data_key in _blender_data_keys:
		thing_type = getattr(bpy.data, data_key)
		for thing in thing_type:
			if(not _check_action_in_data_block(action, thing)):
				return False
			for sub_key in _blender_data_subkeys:
				if(hasattr(thing, sub_key)):
					if(not _check_action_in_data_block(action, getattr(thing, sub_key))):
						return False

	for slot_link in action.slot_link.links:
		slot_link: SlotLink = slot_link
		for slot in action.slots:
			if(slot.handle == slot_link.slot_handle):
				break
		else:
			continue

		target_object: bpy.types.Object = slot_link.target
		if(not target_object):
			if(len(slot.users()) > 0):
				return False
			continue # The slot is still linked correctly

		if(len(slot.users()) > 1):
			return False

		# why u no polymorphism?
		match(slot.target_id_type):
			case "OBJECT":
				if(target_object.animation_data.action_slot != slot):
					return False

			case "MATERIAL":
				if(target_object.material_slots and len(target_object.material_slots) > slot_link.datablock_index):
					target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[slot_link.datablock_index] # pyright: ignore[reportRedeclaration]
					if(target_material_slot.material):
						if(not _has_animation_data(target_material_slot.material) or target_material_slot.material.animation_data.action_slot != slot):
							return False

			case "NODETREE":
				if(target_object.material_slots and len(target_object.material_slots) > slot_link.datablock_index):
					target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[slot_link.datablock_index]
					if(target_material_slot.material and target_material_slot.material.node_tree):
						if(not _has_animation_data(target_material_slot.material.node_tree) or target_material_slot.material.node_tree.animation_data.action_slot != slot):
							return False

			case "KEY":
				if(target_object.data and type(target_object.data) is bpy.types.Mesh and target_object.data.shape_keys):
					if(not _has_animation_data(target_object.data.shape_keys) or target_object.data.shape_keys.animation_data.action_slot != slot):
						return False

			case "ARMATURE":
				if(target_object.data and type(target_object.data) is bpy.types.Armature):
					if(not _has_animation_data(target_object.data) or target_object.data.animation_data.action_slot != slot):
						return False

			case "CAMERA":
				if(target_object.data and type(target_object.data) is bpy.types.Camera):
					if(not _has_animation_data(target_object.data) or target_object.data.animation_data.action_slot != slot):
						return False

			case "LIGHT":
				if(target_object.data and isinstance(target_object.data, bpy.types.Light)):
					if(not _has_animation_data(target_object.data) or target_object.data.animation_data.action_slot != slot):
						return False
	return True


def check_slot_link_target_unique(action: bpy.types.Action, slot: bpy.types.ActionSlot) -> bool:
	"""Check if this Slot's `target` isn't used by any other Slot with the same `target_id_type`"""
	slot_link = find_slot_link(action, slot.handle)
	if(not slot_link):
		return True
	for check_slot in action.slots:
		if(check_slot == slot or check_slot.target_id_type != slot.target_id_type):
			continue
		check_slot_link = find_slot_link(action, check_slot.handle)
		if(not check_slot_link):
			continue
		if(slot_link.target == check_slot_link.target):
			if(slot.target_id_type in ["MATERIAL", "NODETREE"] and slot_link.datablock_index != check_slot_link.datablock_index):
				continue
			else:
				return False
	return True


## Prepare animation_data

def _prepare_data_block(action: bpy.types.Action | None, blender_data_block: bpy.types.ID):
	"""
	Clear the `animation_data` on a Blender ID.
	If an Action is provided, create new `animation_data`, set the Action, but no Slot.
	"""
	if(hasattr(blender_data_block, "animation_data")):
		blender_data_block.animation_data_clear()
		if(action):
			blender_data_block.animation_data_create()
			if(blender_data_block.animation_data):
				blender_data_block.animation_data.action = action
				blender_data_block.animation_data.action_slot = None

def prepare_all_data_blocks(action: bpy.types.Action | None):
	"""
	Clear the `animation_data` on all Blender IDs.

	If an Action is provided, create new `animation_data`, set the Action, but no Slot.
	"""
	if(action):
		action.use_fake_user = True

	for data_key in _blender_data_keys:
		thing_type = getattr(bpy.data, data_key)
		for thing in thing_type:
			_prepare_data_block(action, thing)
			for sub_key in _blender_data_subkeys:
				if(hasattr(thing, sub_key)):
					_prepare_data_block(action, getattr(thing, sub_key))
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

def _link_slot(action: bpy.types.Action, slot: bpy.types.ActionSlot, slot_link: SlotLink):
	"""
	Determine the animation target based on the `slot_link`.

	Set the `action` and `slot` to that targets `animation_data`.
	"""
	if(not slot_link.target): return
	target_object: bpy.types.Object = slot_link.target

	# why u no polymorphism?
	match(slot.target_id_type):
		case "OBJECT":
			_set_animation_data(target_object, action, slot)

		case "MATERIAL":
			if(target_object.material_slots and len(target_object.material_slots) > slot_link.datablock_index):
				target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[slot_link.datablock_index]
				if(target_material_slot.material):
					_set_animation_data(target_material_slot.material, action, slot)

		case "NODETREE":
			if(target_object.material_slots and len(target_object.material_slots) > slot_link.datablock_index):
				target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[slot_link.datablock_index]
				if(target_material_slot.material and target_material_slot.material.node_tree):
					_set_animation_data(target_material_slot.material.node_tree, action, slot)

		case "KEY":
			if(target_object.data and type(target_object.data) is bpy.types.Mesh and target_object.data.shape_keys):
				_set_animation_data(target_object.data.shape_keys, action, slot)

		case "ARMATURE":
			if(target_object.data and type(target_object.data) is bpy.types.Armature):
				_set_animation_data(target_object.data, action, slot)

		case "CAMERA":
			if(target_object.data and type(target_object.data) is bpy.types.Camera):
				_set_animation_data(target_object.data, action, slot)

		case "LIGHT":
			if(target_object.data and isinstance(target_object.data, bpy.types.Light)):
				_set_animation_data(target_object.data, action, slot)

def link_slots(action: bpy.types.Action):
	"""
	Link the Action to all data-blocks in the Scene.

	Links its Slots to the targets, determined by each Slots `slot_link`.
	"""
	prepare_all_data_blocks(action)

	for slot_link in action.slot_link.links:
		slot_link: SlotLink = slot_link # Because autocomplete
		if(slot_link.target and slot_link.slot_handle):
			for slot in action.slots:
				if(slot.handle == slot_link.slot_handle):
					_link_slot(action, slot, slot_link)
					break
