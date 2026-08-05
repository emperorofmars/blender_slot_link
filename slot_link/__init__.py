import bpy

from . import package_key

__all__ = ["register_slot_link", "unregister_slot_link", "package_key"]

register_slot_link, unregister_slot_link = bpy.utils.register_submodule_factory(__name__, ["slot_link", "slot_link_ops", "slot_link_ui", "slot_link_ui_parts", "preferences"])
