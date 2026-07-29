#pyright: reportArgumentType=none
import bpy

from .package_key import get_preferences
from .slot_link_ui_parts import draw_link_buttons, draw_link_messages, draw_slot_link_editor, draw_slot_target_selector


def _context_invalid(context: bpy.types.Context) -> bool:
	return not context or not hasattr(context, "active_action") or not context.active_action


def _draw_editor(self, context: bpy.types.Context):
	"""Draw the full Slot Link editor GUI for the Action panel"""
	if(_context_invalid(context) or get_preferences().use_separate_editor):
		return
	layout: bpy.types.UILayout = self.layout
	layout.separator(factor=2, type="LINE")
	draw_slot_link_editor(layout, context.active_action)


def _draw_slot_link_selector(self, context: bpy.types.Context):
	"""Draw the target-selector GUI for the Slot panel"""
	if(_context_invalid(context)):
		return
	layout: bpy.types.UILayout = self.layout
	layout.label(text="Slot Link Target(s):")
	draw_slot_target_selector(layout, context.active_action, context.active_action.slots.active, True)


def _draw_link_buttons(self, context: bpy.types.Context):
	if(_context_invalid(context) or get_preferences().hide_dopesheet_header_ui):
		return
	draw_link_buttons(self.layout, context.active_action, True)

def _draw_link_messages(self, context: bpy.types.Context):
	if(_context_invalid(context) or get_preferences().hide_dopesheet_header_ui):
		return
	draw_link_messages(self.layout, context.active_action, True)


def _draw_spacer_before(self, context: bpy.types.Context):
	"""Draw a Spacer in the Dopesheet header so there is a gab between the menus and the SlotLink button"""
	if(_context_invalid(context) or get_preferences().hide_dopesheet_header_ui):
		return
	self.layout.separator(factor=6)

def _draw_spacer_after(self, context: bpy.types.Context):
	"""Draw a Spacer in the Dopesheet header so there is a gab between the SlotLink button and the Action & Slot selector"""
	if(_context_invalid(context) or get_preferences().hide_dopesheet_header_ui):
		return
	self.layout.separator(factor=2)


class SlotLinkEditor(bpy.types.Panel):
	"""Link the Slots of an Action to their targets"""
	bl_idname = "OBJECT_PT_slot_link_editor"
	bl_label = "Slot Link Editor"
	bl_region_type = "UI"
	bl_space_type = "DOPESHEET_EDITOR"
	bl_category = "Action"
	bl_order = -10

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return not _context_invalid(context) and get_preferences().use_separate_editor

	def draw_header(self, context: bpy.types.Context):
		self.layout.label(icon="DECORATE_LINKED")

	def draw(self, context: bpy.types.Context):
		draw_slot_link_editor(self.layout, context.active_action)


def register():
	bpy.utils.register_class(SlotLinkEditor)

	bpy.types.DOPESHEET_MT_editor_menus.append(_draw_spacer_before)
	bpy.types.DOPESHEET_MT_editor_menus.append(_draw_link_buttons)
	bpy.types.DOPESHEET_MT_editor_menus.append(_draw_spacer_after)
	bpy.types.DOPESHEET_MT_editor_menus.append(_draw_link_messages)
	bpy.types.DOPESHEET_PT_action.append(_draw_editor)
	bpy.types.DOPESHEET_PT_action_slot.append(_draw_slot_link_selector)

def unregister():
	bpy.types.DOPESHEET_PT_action_slot.remove(_draw_slot_link_selector)
	bpy.types.DOPESHEET_PT_action.remove(_draw_editor)
	bpy.types.DOPESHEET_MT_editor_menus.remove(_draw_link_messages)
	bpy.types.DOPESHEET_MT_editor_menus.remove(_draw_spacer_after)
	bpy.types.DOPESHEET_MT_editor_menus.remove(_draw_link_buttons)
	bpy.types.DOPESHEET_MT_editor_menus.remove(_draw_spacer_before)

	bpy.utils.unregister_class(SlotLinkEditor)
