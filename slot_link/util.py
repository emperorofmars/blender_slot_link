import bpy
from typing import Protocol

from . import package_key


__all__ = ["context_valid", "has_shapekeys", "are_all_actions_setup", "SlotLinkPreferences", "get_preferences", "needs_migrate_2_0"]


def context_valid(context: bpy.types.Context | None) -> bool:
	return context is not None and hasattr(context, "active_action") and context.active_action is not None


types_with_key = [bpy.types.Mesh, bpy.types.Curve, bpy.types.Lattice]

def has_shapekeys(blender_object: bpy.types.Object) -> bool:
	"""Check if the resource instantiated on this object supports shapekey animation"""
	if(blender_object.data and hasattr(blender_object.data, "shape_keys") and blender_object.data.shape_keys):
		for type_candidate in types_with_key:
			if(isinstance(blender_object.data, type_candidate)):
				return True
	return False


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


### TODO remove legacy data-model by 2027-08-01
def needs_migrate_2_0() -> bool:
	for action in bpy.data.actions:
		for slot_link in action.slot_link.links:
			if(len(slot_link.targets) == 0):
				return True
	return False


class SlotLinkPreferences(Protocol):
	use_separate_editor: bool
	"""Move Slot Link editor to separate Panel"""

	hide_slot_link_list: bool
	"""Hide the list of Slot Links (Use the Slot Panel instead)"""

	hide_dopesheet_header_ui: bool
	"""Hide Dopesheet header GUI"""

	hide_documentation_link: bool
	"""Hide Documentation link"""


def get_preferences() -> SlotLinkPreferences:
	return bpy.context.preferences.addons[package_key.package_key].preferences
