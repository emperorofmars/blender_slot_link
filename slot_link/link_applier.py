import bpy

from .slot_link import SlotLink


# why u no polymorphism?
_blender_data_keys = ["actions", "armatures", "brushes", "cache_files", "cameras", "collections", "curves", "fonts", "grease_pencils", "images", "lattices", "libraries", "lights", "lightprobes", "linestyles", "masks", "materials", "meshes", "metaballs", "movieclips", "node_groups", "objects", "paint_curves", "palettes", "particles", "pointclouds", "scenes", "screens", "sounds", "speakers", "texts", "textures", "volumes", "window_managers", "workspaces", "worlds"]
_blender_data_subkeys = ["node_tree", "shape_keys", "compositing_node_group"]


"""
Check
"""

def check_action_in_data_block(action: bpy.types.Action, blender_data_block: bpy.types.ID) -> bool:
	if(hasattr(blender_data_block, "animation_data")):
		if(not blender_data_block.animation_data or blender_data_block.animation_data.action != action):
			# todo check slots as well if present
			return False
	return True

def check_action(action: bpy.types.Action) -> bool:
	for data_key in _blender_data_keys:
		thing_type = getattr(bpy.data, data_key)
		for thing in thing_type:
			if(not check_action_in_data_block(action, thing)): return False
			for sub_key in _blender_data_subkeys:
				if(hasattr(thing, sub_key)):
					if(not check_action_in_data_block(action, getattr(thing, sub_key))): return False
	return True


"""
Prepare animation_data
"""

def prepare_data_block(action: bpy.types.Action | None, blender_data_block: bpy.types.ID):
	if(hasattr(blender_data_block, "animation_data")):
		blender_data_block.animation_data_clear()
		if(action):
			blender_data_block.animation_data_create()
			if(blender_data_block.animation_data):
				blender_data_block.animation_data.action = action
				blender_data_block.animation_data.action_slot = None

def prepare_all_data_blocks(action: bpy.types.Action | None):
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
	"""Link this Action to every data-block, remove any other Action from being linked anywhere"""
	bl_idname = "slot_link.prepare"
	bl_label = "Prepare"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return context.active_action is not None

	def execute(self, context: bpy.types.Context):
		prepare_all_data_blocks(context.active_action)
		return {"FINISHED"}

class UnlinkAction(bpy.types.Operator):
	"""Remove any Action from being linked anywhere"""
	bl_idname = "slot_link.unlink"
	bl_label = "Unlink"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context: bpy.types.Context):
		prepare_all_data_blocks(None)
		return {"FINISHED"}


"""
Link
"""

def set_animation_data(blender_thing: bpy.types.ID, action: bpy.types.Action, slot: bpy.types.ActionSlot):
	if(not blender_thing.animation_data):
		blender_thing.animation_data_create()
	blender_thing.animation_data.action = action
	blender_thing.animation_data.action_slot = slot

def link_slot(action: bpy.types.Action, slot: bpy.types.ActionSlot, slot_link: SlotLink):
	if(not slot_link.target): return
	target_object: bpy.types.Object = slot_link.target

	# why u no polymorphism?
	match(slot.target_id_type):
		case "OBJECT":
			set_animation_data(target_object, action, slot)

		case "MATERIAL":
			if(target_object.material_slots and len(target_object.material_slots) > slot_link.datablock_index):
				target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[slot_link.datablock_index]
				if(target_material_slot.material):
					set_animation_data(target_material_slot.material, action, slot)

		case "NODETREE":
			if(target_object.material_slots and len(target_object.material_slots) > slot_link.datablock_index):
				target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[slot_link.datablock_index]
				if(target_material_slot.material and target_material_slot.material.node_tree):
					set_animation_data(target_material_slot.material.node_tree, action, slot)

		case "KEY":
			if(target_object.data and type(target_object.data) == bpy.types.Mesh and target_object.data.shape_keys):
				set_animation_data(target_object.data.shape_keys, action, slot)

		case "ARMATURE":
			if(target_object.data and type(target_object.data) == bpy.types.Armature):
				set_animation_data(target_object.data, action, slot)

		case "CAMERA":
			if(target_object.data and type(target_object.data) == bpy.types.Camera):
				set_animation_data(target_object.data, action, slot)

		case "LIGHT":
			if(target_object.data and isinstance(target_object.data, bpy.types.Light)):
				set_animation_data(target_object.data, action, slot)


def link_slots(action: bpy.types.Action):
	for slot_link in action.slot_link.links:
		slot_link: SlotLink = slot_link # Because autocomplete
		if(slot_link.target and slot_link.slot_handle):
			for slot in action.slots:
				if(slot.handle == slot_link.slot_handle):
					link_slot(action, slot, slot_link)
					break

class LinkSlots(bpy.types.Operator):
	"""Link this Action and its Slots in the selected targets"""
	bl_idname = "slot_link.link"
	bl_label = "Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return context.active_action is not None

	def execute(self, context: bpy.types.Context):
		# Link the reset animation first if applicable
		action = context.active_action
		if(not action.slot_link.is_reset_animation and action.slot_link.reset_animation):
			prepare_all_data_blocks(action.slot_link.reset_animation)
			link_slots(action.slot_link.reset_animation)
			context.scene.frame_set(1)
		# Link the desired action
		prepare_all_data_blocks(action)
		link_slots(action)
		return {"FINISHED"}

