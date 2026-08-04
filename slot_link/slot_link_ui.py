#pyright: reportArgumentType=none
import bpy

from .slot_link_ops import ClearScene, LinkSlots, MigrateSlotLink_0_2, PrepareLinks, SetupAllActions
from .slot_link_ui_parts import draw_link_buttons, draw_link_messages, draw_slot_link_editor, draw_slot_target_selector
from .util import context_valid, get_preferences, needs_migrate_2_0


def _draw_editor(self, context: bpy.types.Context):
	"""Draw the full Slot Link editor GUI for the Action panel"""
	if(not context_valid(context) or get_preferences().use_separate_editor):
		return
	layout: bpy.types.UILayout = self.layout
	layout.separator(factor=2, type="LINE")
	draw_slot_link_editor(layout, context.active_action)


def _draw_slot_link_selector(self, context: bpy.types.Context):
	"""Draw the target-selector GUI for the Slot panel"""
	if(not context_valid(context)):
		return
	layout: bpy.types.UILayout = self.layout
	layout.label(text="Slot Link Target(s):")
	draw_slot_target_selector(layout, context.active_action, context.active_action.slots.active, True)


class SlotLinkMenu(bpy.types.Menu):
	bl_idname = "DOPESHEET_MT_slot_link_menu"
	bl_label = "Slot Link"

	def draw(self, context: bpy.types.Context):
		layout: bpy.types.UILayout = self.layout # pyright: ignore[reportAssignmentType]

		if(needs_migrate_2_0()):
			layout.operator(MigrateSlotLink_0_2.bl_idname, icon="WARNING_LARGE")
		elif(context_valid(context) and context.active_action.is_action_legacy):
			layout.operator(PrepareLinks.bl_idname)
		elif(context_valid(context)):
			layout.operator(LinkSlots.bl_idname, text="Link Slots", icon="DECORATE_LINKED").use_reset_animation = True
			col = layout.column()
			col.enabled = context.active_action.slot_link.reset_animation is not None
			col.operator(LinkSlots.bl_idname, text="..without Reset").use_reset_animation = False

		layout.separator(factor=1, type="LINE")
		layout.operator(SetupAllActions.bl_idname)
		layout.operator(ClearScene.bl_idname)

def _draw_link_menu(self, context: bpy.types.Context):
	if(context and context.space_data and context.space_data.mode == "ACTION"):
		self.layout.menu(SlotLinkMenu.bl_idname)

	if(not context_valid(context) or get_preferences().hide_dopesheet_header_ui):
		return

	self.layout.separator(factor=6)
	draw_link_buttons(self.layout, context.active_action, True)
	self.layout.separator(factor=2)
	draw_link_messages(self.layout, context.active_action, True)


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
		return context_valid(context) and get_preferences().use_separate_editor

	def draw_header(self, context: bpy.types.Context):
		self.layout.label(icon="DECORATE_LINKED")

	def draw(self, context: bpy.types.Context):
		draw_slot_link_editor(self.layout, context.active_action)


def register():
	bpy.utils.register_class(SlotLinkEditor)
	bpy.utils.register_class(SlotLinkMenu)

	bpy.types.DOPESHEET_MT_editor_menus.append(_draw_link_menu)
	bpy.types.DOPESHEET_PT_action.append(_draw_editor)
	bpy.types.DOPESHEET_PT_action_slot.append(_draw_slot_link_selector)

def unregister():
	bpy.types.DOPESHEET_PT_action_slot.remove(_draw_slot_link_selector)
	bpy.types.DOPESHEET_PT_action.remove(_draw_editor)
	bpy.types.DOPESHEET_MT_editor_menus.remove(_draw_link_menu)

	bpy.utils.unregister_class(SlotLinkMenu)
	bpy.utils.unregister_class(SlotLinkEditor)
