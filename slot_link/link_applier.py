import bpy

from .slot_link import SlotLink


def prepare_data_block(action: bpy.types.Action, blender_data_block: bpy.types.ID):
	if(hasattr(blender_data_block, "animation_data")):
		blender_data_block.animation_data_clear()
		blender_data_block.animation_data_create()
		if(blender_data_block.animation_data):
			blender_data_block.animation_data.action = action
			blender_data_block.animation_data.action_slot = None

def prepare_all_data_blocks(action: bpy.types.Action):
	# why u no polymorphism?
	for thing in bpy.data.actions: prepare_data_block(action, thing)
	for thing in bpy.data.armatures: prepare_data_block(action, thing)
	for thing in bpy.data.brushes: prepare_data_block(action, thing)
	for thing in bpy.data.cache_files: prepare_data_block(action, thing)
	for thing in bpy.data.cameras: prepare_data_block(action, thing)
	for thing in bpy.data.collections: prepare_data_block(action, thing)
	for thing in bpy.data.curves: prepare_data_block(action, thing)
	for thing in bpy.data.fonts: prepare_data_block(action, thing)
	for thing in bpy.data.grease_pencils: prepare_data_block(action, thing)
	for thing in bpy.data.grease_pencils_v3: prepare_data_block(action, thing)
	for thing in bpy.data.images: prepare_data_block(action, thing)
	for thing in bpy.data.lattices: prepare_data_block(action, thing)
	for thing in bpy.data.libraries: prepare_data_block(action, thing)
	for thing in bpy.data.lights:
		prepare_data_block(action, thing)
		if(thing.node_tree):
			prepare_data_block(action, thing.node_tree)
	for thing in bpy.data.lightprobes: prepare_data_block(action, thing)
	for thing in bpy.data.linestyles: prepare_data_block(action, thing)
	for thing in bpy.data.masks: prepare_data_block(action, thing)
	for thing in bpy.data.materials:
		prepare_data_block(action, thing)
		if(thing.node_tree):
			prepare_data_block(action, thing.node_tree)
	for thing in bpy.data.meshes:
		prepare_data_block(action, thing)
		if(thing.shape_keys):
			prepare_data_block(action, thing.shape_keys)
	for thing in bpy.data.metaballs: prepare_data_block(action, thing)
	for thing in bpy.data.movieclips: prepare_data_block(action, thing)
	for thing in bpy.data.node_groups: prepare_data_block(action, thing)
	for thing in bpy.data.objects: prepare_data_block(action, thing)
	for thing in bpy.data.paint_curves: prepare_data_block(action, thing)
	for thing in bpy.data.palettes: prepare_data_block(action, thing)
	for thing in bpy.data.particles: prepare_data_block(action, thing)
	for thing in bpy.data.pointclouds: prepare_data_block(action, thing)
	for thing in bpy.data.scenes:
		prepare_data_block(action, thing)
		if(thing.node_tree):
			prepare_data_block(action, thing.node_tree)
	for thing in bpy.data.screens: prepare_data_block(action, thing)
	for thing in bpy.data.sounds: prepare_data_block(action, thing)
	for thing in bpy.data.speakers: prepare_data_block(action, thing)
	for thing in bpy.data.texts: prepare_data_block(action, thing)
	for thing in bpy.data.textures: prepare_data_block(action, thing)
	for thing in bpy.data.volumes: prepare_data_block(action, thing)
	for thing in bpy.data.window_managers: prepare_data_block(action, thing)
	for thing in bpy.data.workspaces: prepare_data_block(action, thing)
	for thing in bpy.data.worlds:
		prepare_data_block(action, thing)
		if(thing.node_tree):
			prepare_data_block(action, thing.node_tree)

class PrepareLinks(bpy.types.Operator):
	"""Link this Action to every data-block, remove any other Action from being linked anywhere"""
	bl_idname = "slot_link.prepare"
	bl_label = "Prepare"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context): return context.active_action is not None

	def execute(self, context: bpy.types.Context):
		prepare_all_data_blocks(context.active_action)
		return {"FINISHED"}


def set_animtaion_data(blender_thing: bpy.types.ID, action: bpy.types.Action, slot: bpy.types.ActionSlot):
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
			set_animtaion_data(target_object, action, slot)

			# If the target object is an armature-instance, also link all objects with meshes that use this armature to this slot. Why can't you be normal Blender?
			if(type(target_object.data) == bpy.types.Armature):
				for mesh_instance in bpy.data.objects:
					if(mesh_instance.data and type(mesh_instance.data) == bpy.types.Mesh):
						for modifier in mesh_instance.modifiers:
							if(modifier.type == "ARMATURE" and modifier.object == target_object):
								set_animtaion_data(mesh_instance, action, slot)
								break

		case "MATERIAL":
			if(target_object.material_slots and len(target_object.material_slots) > slot_link.datablock_index):
				target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[slot_link.datablock_index]
				if(target_material_slot.material):
					set_animtaion_data(target_material_slot.material, action, slot)

		case "NODETREE":
			if(target_object.material_slots and len(target_object.material_slots) > slot_link.datablock_index):
				target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[slot_link.datablock_index]
				if(target_material_slot.material and target_material_slot.material.node_tree):
					set_animtaion_data(target_material_slot.material.node_tree, action, slot)

		case "KEY":
			if(target_object.data and type(target_object.data) == bpy.types.Mesh and target_object.data.shape_keys):
				set_animtaion_data(target_object.data.shape_keys, action, slot)

		case "ARMATURE":
			if(target_object.data and type(target_object.data) == bpy.types.Armature):
				set_animtaion_data(target_object.data, action, slot)


def link_slots(action: bpy.types.Action):
	for slot_link in action.slot_links:
		slot_link: SlotLink = slot_link # Because autocomplete
		if(slot_link.target and slot_link.slot_handle):
			selected_slot = None
			for slot in action.slots:
				if(slot.handle == slot_link.slot_handle):
					selected_slot = slot
					break
			else:
				continue
			link_slot(action, selected_slot, slot_link)

class LinkSlots(bpy.types.Operator):
	"""Link this Action and its Slots in the selected targets"""
	bl_idname = "slot_link.link"
	bl_label = "Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context): return context.active_action is not None

	def execute(self, context: bpy.types.Context):
		prepare_all_data_blocks(context.active_action)
		link_slots(context.active_action)
		return {"FINISHED"}

