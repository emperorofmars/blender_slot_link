import bpy

from .slot_link import SlotLink


# why u no polymorphism?
_blender_data_keys = ["actions", "armatures", "brushes", "cache_files", "cameras", "collections", "curves", "fonts", "grease_pencils", "images", "lattices", "libraries", "lights", "lightprobes", "linestyles", "masks", "materials", "meshes", "metaballs", "movieclips", "node_groups", "objects", "paint_curves", "palettes", "particles", "pointclouds", "scenes", "screens", "sounds", "speakers", "texts", "textures", "volumes", "window_managers", "workspaces", "worlds"]
_blender_data_subkeys = ["node_tree", "shape_keys", "compositing_node_group"]


"""
Utils
"""

def find_slot_link(action: bpy.types.Action | None, slot_handle: int) -> SlotLink | None:
	"""Find the SlotLink on an Action based on a Slots handle"""
	if(action):
		for slot_link in action.slot_link.links:
			if(slot_link.slot_handle == slot_handle):
				return slot_link
	return None


"""
Check
"""

def has_animation_data(blender_data_block: bpy.types.ID) -> bool:
	"""Check if the `blender_data_block` has valid `animation_data`"""
	if(hasattr(blender_data_block, "animation_data") and blender_data_block.animation_data is not None):
		return True
	else:
		return False

def check_action_in_data_block(action: bpy.types.Action, blender_data_block: bpy.types.ID) -> bool:
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
			if(not check_action_in_data_block(action, thing)):
				return False
			for sub_key in _blender_data_subkeys:
				if(hasattr(thing, sub_key)):
					if(not check_action_in_data_block(action, getattr(thing, sub_key))):
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
			return True # The action is still linked correctly

		# why u no polymorphism?
		match(slot.target_id_type):
			case "OBJECT":
				if(target_object.animation_data.action_slot != slot):
					return False

			case "MATERIAL":
				if(target_object.material_slots and len(target_object.material_slots) > slot_link.datablock_index):
					target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[slot_link.datablock_index]  # pyright: ignore[reportRedeclaration]
					if(target_material_slot.material):
						if(not has_animation_data(target_material_slot.material) or target_material_slot.material.animation_data.action_slot != slot):
							return False

			case "NODETREE":
				if(target_object.material_slots and len(target_object.material_slots) > slot_link.datablock_index):
					target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[slot_link.datablock_index]
					if(target_material_slot.material and target_material_slot.material.node_tree):
						if(not has_animation_data(target_material_slot.material.node_tree) or target_material_slot.material.node_tree.animation_data.action_slot != slot):
							return False

			case "KEY":
				if(target_object.data and type(target_object.data) is bpy.types.Mesh and target_object.data.shape_keys):
					if(not has_animation_data(target_object.data.shape_keys) or target_object.data.shape_keys.animation_data.action_slot != slot):
						return False

			case "ARMATURE":
				if(target_object.data and type(target_object.data) is bpy.types.Armature):
					if(not has_animation_data(target_object.data) or target_object.data.animation_data.action_slot != slot):
						return False

			case "CAMERA":
				if(target_object.data and type(target_object.data) is bpy.types.Camera):
					if(not has_animation_data(target_object.data) or target_object.data.animation_data.action_slot != slot):
						return False

			case "LIGHT":
				if(target_object.data and isinstance(target_object.data, bpy.types.Light)):
					if(not has_animation_data(target_object.data) or target_object.data.animation_data.action_slot != slot):
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


"""
Prepare animation_data
"""

def prepare_data_block(action: bpy.types.Action | None, blender_data_block: bpy.types.ID):
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
			prepare_data_block(action, thing)
			for sub_key in _blender_data_subkeys:
				if(hasattr(thing, sub_key)):
					prepare_data_block(action, getattr(thing, sub_key))
	return True

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


class ClearScene(bpy.types.Operator):
	"""Clear the Scene of any animation data"""
	bl_idname = "slot_link.clear_scene"
	bl_label = "Clear Scene"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context: bpy.types.Context) -> set:
		prepare_all_data_blocks(None)
		return {"FINISHED"}


"""
Link
"""

def set_animation_data(blender_thing: bpy.types.ID, action: bpy.types.Action, slot: bpy.types.ActionSlot):
	"""
	Set the Action and Slot in the `animation_data` of a Blender ID.
	"""
	if(not blender_thing.animation_data):
		blender_thing.animation_data_create()
	blender_thing.animation_data.action = action
	blender_thing.animation_data.action_slot = slot

def link_slot(action: bpy.types.Action, slot: bpy.types.ActionSlot, slot_link: SlotLink):
	"""
	Determine the animation target based on the `slot_link`.

	Set the `action` and `slot` to that targets `animation_data`.
	"""
	if(not slot_link.target): return
	target_object: bpy.types.Object = slot_link.target

	# why u no polymorphism?
	match(slot.target_id_type):
		case "OBJECT":
			set_animation_data(target_object, action, slot)

		case "MATERIAL":
			if(target_object.material_slots and len(target_object.material_slots) > slot_link.datablock_index):
				target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[slot_link.datablock_index]  # pyright: ignore[reportRedeclaration]
				if(target_material_slot.material):
					set_animation_data(target_material_slot.material, action, slot)
					return

		case "NODETREE":
			if(target_object.material_slots and len(target_object.material_slots) > slot_link.datablock_index):
				target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[slot_link.datablock_index]
				if(target_material_slot.material and target_material_slot.material.node_tree):
					set_animation_data(target_material_slot.material.node_tree, action, slot)
					return

		case "KEY":
			if(target_object.data and type(target_object.data) is bpy.types.Mesh and target_object.data.shape_keys):
				set_animation_data(target_object.data.shape_keys, action, slot)
				return

		case "ARMATURE":
			if(target_object.data and type(target_object.data) is bpy.types.Armature):
				set_animation_data(target_object.data, action, slot)
				return

		case "CAMERA":
			if(target_object.data and type(target_object.data) is bpy.types.Camera):
				set_animation_data(target_object.data, action, slot)
				return

		case "LIGHT":
			if(target_object.data and isinstance(target_object.data, bpy.types.Light)):
				set_animation_data(target_object.data, action, slot)
				return


def link_slots(action: bpy.types.Action):
	"""
	Link the Action to all data-blocks in the Scene.

	Links its Slots to the targets, determined by each Slots `slot_link`.
	"""
	for slot_link in action.slot_link.links:
		slot_link: SlotLink = slot_link # Because autocomplete
		if(slot_link.target and slot_link.slot_handle):
			for slot in action.slots:
				if(slot.handle == slot_link.slot_handle):
					link_slot(action, slot, slot_link)
					break

class LinkSlots(bpy.types.Operator):
	"""Link the Action to everything in the Scene.
	Link its Slots to the selected targets.
	If a Reset Animation is selected, it will be used to bring the Scene into a consistent state"""
	bl_idname = "slot_link.link"
	bl_label = "Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	use_reset: bpy.props.BoolProperty(name="Use Reset", default=True, description="If a Reset Animation is selected, it will be used to bring the Scene into a consistent state") # type: ignore

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return hasattr(context, "active_action") and context.active_action is not None

	def execute(self, context: bpy.types.Context) -> set:
		# Link the reset animation first if applicable
		action: bpy.types.Action = context.active_action  # pyright: ignore[reportAssignmentType]
		if(self.use_reset and not action.slot_link.is_reset_animation and action.slot_link.reset_animation):
			prepare_all_data_blocks(action.slot_link.reset_animation)
			link_slots(action.slot_link.reset_animation)
			context.scene.frame_set(1)
		# Link the desired action
		prepare_all_data_blocks(action)
		link_slots(action)
		return {"FINISHED"}
