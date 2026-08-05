import bpy
from .slot_link import package_key, register_slot_link, unregister_slot_link


package_key.package_key = __package__ # Required for ./slot_link/preferences.py


def slot_link_docs():
	manual_map = (
		("bpy.ops.slot_link.*", ""),
		("bpy.types.slotlinktarget.*", ""),
		("bpy.types.slotlink.*", ""),
		("bpy.types.actionslotlink.*", ""),
		("bpy.types.action.slot_link.*", ""),
	)
	return "https://docs.stfform.at/guide/blender/slot_link.html", manual_map


def register():
	bpy.utils.register_manual_map(slot_link_docs)
	register_slot_link()

def unregister():
	unregister_slot_link()
	bpy.utils.unregister_manual_map(slot_link_docs)
