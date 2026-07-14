import bpy

from .slot_link_ui_parts import draw_link_buttons, draw_link_messages, draw_slot_link_editor, draw_slot_target_selector


def _draw_action_slot_link(self, context: bpy.types.Context):
	"""Draw the full Slot Link editor GUI for the Action panel"""
	if(not context or not hasattr(context, "active_action") or not context.active_action):
		return
	layout: bpy.types.UILayout = self.layout
	layout.separator(factor=2, type="LINE")
	draw_slot_link_editor(self, context)


def _draw_slot_link(self, context: bpy.types.Context):
	"""Draw the target-selector GUI for the Slot panel"""
	if(not context or not hasattr(context, "active_action") or not context.active_action):
		return
	layout: bpy.types.UILayout = self.layout
	draw_slot_target_selector(self, context, context.active_action.slots.active)


def _draw_spacer(self, context: bpy.types.Context):
	"""Draw a Spacer in the Dopesheet header so there is a gab between the menus and the slot link buttons"""
	if(not context or not hasattr(context, "active_action") or not context.active_action):
		return
	self.layout.separator(factor=12)

"""
class SlotLinkEditor(bpy.types.Panel):
	""Link the Slots of an Action to their targets""
	bl_idname = "OBJECT_PT_slot_link_editor"
	bl_label = "Slot Link Editor"
	bl_region_type = "UI"
	bl_space_type = "DOPESHEET_EDITOR"
	bl_category = "Action"
	bl_order = -10

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return hasattr(context, "active_action") and context.active_action is not None

	def draw_header(self, context: bpy.types.Context):
		self.layout.label(icon="DECORATE_LINKED")

	def draw(self, context: bpy.types.Context):
		draw_slot_link_editor(self, context)
"""

def register():
	bpy.types.DOPESHEET_MT_editor_menus.append(_draw_spacer)
	bpy.types.DOPESHEET_MT_editor_menus.append(draw_link_messages)
	bpy.types.DOPESHEET_MT_editor_menus.append(draw_link_buttons)
	bpy.types.DOPESHEET_PT_action.append(_draw_action_slot_link)
	bpy.types.DOPESHEET_PT_action_slot.append(_draw_slot_link)

def unregister():
	bpy.types.DOPESHEET_PT_action_slot.remove(_draw_slot_link)
	bpy.types.DOPESHEET_PT_action.remove(_draw_action_slot_link)
	bpy.types.DOPESHEET_MT_editor_menus.remove(draw_link_buttons)
	bpy.types.DOPESHEET_MT_editor_menus.remove(draw_link_messages)
	bpy.types.DOPESHEET_MT_editor_menus.remove(_draw_spacer)
