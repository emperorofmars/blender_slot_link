import bpy

from .slot_link import ActionSlotLink


__all__ = ["context_valid", "are_all_actions_setup", "blender_data_keys", "blender_data_subkeys", "needs_migrate_2_0"]


### TODO remove legacy data-model by 2027-08-01
def needs_migrate_2_0() -> bool:
	for action in bpy.data.actions:
		for slot_link in action.slot_link.links:
			if(len(slot_link.targets) == 0):
				return True
	return False


def context_valid(context: bpy.types.Context | None) -> bool:
	"""Check if the context has a valid `active_action`"""
	return context is not None and hasattr(context, "active_action") and context.active_action is not None


def are_all_actions_setup() -> bool:
	for action in bpy.data.actions:
		has_slot = False
		for slot in action.slots:
			has_slot = True
			for slot_link in action.slot_link.links:
				if(slot_link.slot_handle == slot.handle):
					if(len(slot_link.targets) == 0):
						return False
					elif(not slot_link.targets[0].target):
						return False
					break
			else:
				return False
		if(not has_slot):
			return True
	return True


blender_data_keys = ["armatures", "brushes", "cache_files", "cameras", "collections", "curves", "fonts", "grease_pencils", "images", "lattices", "libraries", "lights", "lightprobes", "linestyles", "masks", "materials", "meshes", "metaballs", "movieclips", "node_groups", "objects", "paint_curves", "palettes", "particles", "pointclouds", "scenes", "screens", "sounds", "speakers", "texts", "textures", "volumes", "window_managers", "workspaces", "worlds"]
blender_data_subkeys = ["node_tree", "shape_keys", "compositing_node_group"]

"""
def retrieve_animation_data_holder(target_id_type: str, target_object: bpy.types.Object, datablock_index: int = 0) -> bpy.types.ID | None:
	""
	:param str target_id_type: The `target_id_type` of an `ActionSlot`.
	:param bpy.types.Object target_object: The object from which to retrieve the correct `animation_data` holder for.
	:param int datablock_index: In case the target_id_type is "MATERIAL" or "NODETREE", retrieve the appropriate material or its node_tree.
	:returns bpy.types.ID | None: The object that has the `animation_data` property.
	""
	match(target_id_type):
		case "OBJECT":
			return target_object

		case "MATERIAL":
			if(target_object.material_slots and len(target_object.material_slots) > datablock_index):
				target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[datablock_index]
				if(target_material_slot.material):
					return target_material_slot.material

		case "NODETREE":
			if(target_object.material_slots and len(target_object.material_slots) > datablock_index):
				target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[datablock_index]
				if(target_material_slot.material and target_material_slot.material.node_tree):
					return target_material_slot.material.node_tree

		case "KEY":
			if(target_object.data and hasattr(target_object.data, "shape_keys") and target_object.data.shape_keys):
				for type_candidate in [bpy.types.Mesh, bpy.types.Curve, bpy.types.Lattice]:
					if(isinstance(target_object.data, type_candidate)):
						return target_object.data.shape_keys

		case "ARMATURE":
			if(target_object.data and type(target_object.data) is bpy.types.Armature):
				return target_object.data

		case "CAMERA":
			if(target_object.data and type(target_object.data) is bpy.types.Camera):
				return target_object.data

		case "LIGHT":
			if(target_object.data and isinstance(target_object.data, bpy.types.Light)):
				return target_object.data

		# TODO support more eventually

		case _:
			return None
"""
