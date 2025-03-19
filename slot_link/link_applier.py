import bpy

from .slot_link import SlotLink


def unlink_slot(action: bpy.types.Action, blender_data_block):
	if(hasattr(blender_data_block, "animation_data") and blender_data_block.animation_data and blender_data_block.animation_data.action):
		blender_data_block.animation_data.action = action
		blender_data_block.animation_data.action_slot = None

def unlink_all_slots(action: bpy.types.Action):
	# why u no polymorphism?
	for thing in bpy.data.actions: unlink_slot(action, thing)
	for thing in bpy.data.armatures: unlink_slot(action, thing)
	for thing in bpy.data.brushes: unlink_slot(action, thing)
	for thing in bpy.data.cache_files: unlink_slot(action, thing)
	for thing in bpy.data.cameras: unlink_slot(action, thing)
	for thing in bpy.data.collections: unlink_slot(action, thing)
	for thing in bpy.data.curves: unlink_slot(action, thing)
	for thing in bpy.data.fonts: unlink_slot(action, thing)
	for thing in bpy.data.grease_pencils: unlink_slot(action, thing)
	for thing in bpy.data.grease_pencils_v3: unlink_slot(action, thing)
	for thing in bpy.data.images: unlink_slot(action, thing)
	for thing in bpy.data.lattices: unlink_slot(action, thing)
	for thing in bpy.data.libraries: unlink_slot(action, thing)
	for thing in bpy.data.lights:
		unlink_slot(action, thing)
		if(thing.node_tree):
			unlink_slot(action, thing.node_tree)
	for thing in bpy.data.lightprobes: unlink_slot(action, thing)
	for thing in bpy.data.linestyles: unlink_slot(action, thing)
	for thing in bpy.data.masks: unlink_slot(action, thing)
	for thing in bpy.data.materials:
		unlink_slot(action, thing)
		if(thing.node_tree):
			unlink_slot(action, thing.node_tree)
	for thing in bpy.data.meshes:
		unlink_slot(action, thing)
		if(thing.shape_keys):
			unlink_slot(action, thing.shape_keys)
	for thing in bpy.data.metaballs: unlink_slot(action, thing)
	for thing in bpy.data.movieclips: unlink_slot(action, thing)
	for thing in bpy.data.node_groups: unlink_slot(action, thing)
	for thing in bpy.data.objects: unlink_slot(action, thing)
	for thing in bpy.data.paint_curves: unlink_slot(action, thing)
	for thing in bpy.data.palettes: unlink_slot(action, thing)
	for thing in bpy.data.particles: unlink_slot(action, thing)
	for thing in bpy.data.pointclouds: unlink_slot(action, thing)
	for thing in bpy.data.scenes:
		unlink_slot(action, thing)
		if(thing.node_tree):
			unlink_slot(action, thing.node_tree)
	for thing in bpy.data.screens: unlink_slot(action, thing)
	for thing in bpy.data.sounds: unlink_slot(action, thing)
	for thing in bpy.data.speakers: unlink_slot(action, thing)
	for thing in bpy.data.texts: unlink_slot(action, thing)
	for thing in bpy.data.textures: unlink_slot(action, thing)
	for thing in bpy.data.volumes: unlink_slot(action, thing)
	for thing in bpy.data.window_managers: unlink_slot(action, thing)
	for thing in bpy.data.workspaces: unlink_slot(action, thing)
	for thing in bpy.data.worlds:
		unlink_slot(action, thing)
		if(thing.node_tree):
			unlink_slot(action, thing.node_tree)

class UnlinkAllSlots(bpy.types.Operator):
	bl_idname = "slot_link.unlink_all"
	bl_label = "Unlink All Slots"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context): return context.active_action is not None

	def execute(self, context):
		unlink_all_slots(context.active_action)
		return {"FINISHED"}


def set_animtaion_data(blender_thing: any, action: bpy.types.Action, slot: bpy.types.ActionSlot):
	if(not blender_thing.animation_data):
		blender_thing.animation_data_create()
	blender_thing.animation_data.action = action
	blender_thing.animation_data.action_slot = slot

def link_slot(action: bpy.types.Action, slot: bpy.types.ActionSlot, slot_link: SlotLink):
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

def link_slots(action: bpy.types.Action):
	for slot_link in action.slot_links:
		slot_link: SlotLink = slot_link
		if(slot_link.target and slot_link.slot_handle):
			selected_slot = None
			for slot in action.slots:
				if(slot.handle == slot_link.slot_handle):
					selected_slot = slot
					break
			if(selected_slot):
				link_slot(action, selected_slot, slot_link)
			else:
				pass

class LinkSlots(bpy.types.Operator):
	bl_idname = "slot_link.link"
	bl_label = "Link This Action"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context): return context.active_action is not None

	def execute(self, context):
		unlink_all_slots(context.active_action)
		link_slots(context.active_action)
		return {"FINISHED"}

