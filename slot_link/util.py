import bpy

from .slot_link import retrieve_animation_data_holder


__all__ = ["context_valid", "are_all_actions_setup", "is_any_action_valid", "ensure_selected_object", "blender_data_keys", "blender_data_subkeys", "needs_migrate_2_0"]


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

def is_any_action_valid() -> bool:
	for action in bpy.data.actions:
		for slot in action.slots:
			for slot_link in action.slot_link.links:
				if(slot_link.slot_handle == slot.handle):
					for link_target in slot_link.targets:
						if(link_target.target and retrieve_animation_data_holder(slot.target_id_type, link_target.target, link_target.datablock_index) is not None):
							return True
	return False


def ensure_selected_object(context: bpy.types.Context, action: bpy.types.Action):
	if(action.slot_link.target_collection and context.object not in action.slot_link.target_collection.all_objects.values()):
		for slot_link in action.slot_link.links:
			for link_target in slot_link.targets:
				if(link_target.target):
					link_target.target.select_set(True)
					bpy.context.view_layer.objects.active = link_target.target
					return


blender_data_keys = ["armatures", "brushes", "cache_files", "cameras", "collections", "curves", "fonts", "grease_pencils", "images", "lattices", "libraries", "lights", "lightprobes", "linestyles", "masks", "materials", "meshes", "metaballs", "movieclips", "node_groups", "objects", "paint_curves", "palettes", "particles", "pointclouds", "scenes", "screens", "sounds", "speakers", "texts", "textures", "volumes", "window_managers", "workspaces", "worlds"]
blender_data_subkeys = ["node_tree", "shape_keys", "compositing_node_group"]

