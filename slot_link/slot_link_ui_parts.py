import bpy

from .misc import OpenDocumentation
from .slot_link import AddSlotLink, RemoveSlotLink, SlotLink
from .link_applier import LinkSlots, PrepareLinks, check_action


def find_slot_link(action: bpy.types.Action | None, slot_handle: int) -> SlotLink | None:
	"""Find the SlotLink on an Action based on a Slots handle"""
	if(action):
		for slot_link in action.slot_link.links:
			if(slot_link.slot_handle == slot_handle):
				return slot_link
	return None


class SlotLinkList(bpy.types.UIList):
	"""Display the SlotLinks for each Slot of an Action"""
	bl_idname = "COLLECTION_UL_slot_link_list"

	def draw_item(self, context: bpy.types.Context, layout: bpy.types.UILayout, data: bpy.types.Action, item: bpy.types.ActionSlot, icon, active_data, active_propname, index):  # pyright: ignore[reportIncompatibleMethodOverride]
		slot_link = find_slot_link(context.active_action, item.handle)
		if(not slot_link or not slot_link.target):
			layout.alert = True

		split = layout.split(factor=0.45)
		split.label(text=f"{item.name_display}", icon_value = item.target_id_type_icon)
		if(slot_link and slot_link.target):
			split.label(text=slot_link.target.name, icon="RIGHTARROW")
		else:
			split.label(text="NONE", icon="ERROR")


def draw_link_messages(self, context: bpy.types.Context) -> bool:
	layout: bpy.types.UILayout = self.layout
	action = context.active_action

	if(action.is_action_legacy):
		if(action.users <= 1): # good enough
			row = layout.row()
			row.alert = True
			row.label(text="Prepare the Action!", icon="WARNING_LARGE")
			return False
		if(action.users > 1):
			row = layout.row()
			row.label(text="Please add a new Slot!", icon="INFO")
			return False

	# Check if all Slots have targets!
	successes = 0
	for slot in action.slots:
		slot_link = find_slot_link(action, slot.handle)
		if(slot_link and slot_link.target):
			successes += 1
	if(successes < len(action.slots)):
		row = layout.row()
		row.alert = True
		row.label(text="Not all Slots have Targets!", icon="WARNING_LARGE")
		return True

	# Check whether this Action is linked everywhere state
	if(not action or not check_action(action)):
		row = layout.row()
		row.alert = True
		row.label(text="Not Linked!", icon="WARNING_LARGE")
		return True
	return True


def draw_reset_animation_selector(self, context: bpy.types.Context):
	"""Mark the Action as a reset animation, or select a reset animation"""
	layout: bpy.types.UILayout = self.layout.column(align=True)

	# Reset animation
	if(not context.active_action.slot_link.reset_animation):
		layout.prop(context.active_action.slot_link, "is_reset_animation")
	if(not context.active_action.slot_link.is_reset_animation):
		layout.prop(context.active_action.slot_link, "reset_animation")
		if(context.active_action.slot_link.reset_animation and len(context.active_action.slot_link.reset_animation.slot_link.links) == 0):
			row = layout.row()
			row.alert = True
			row.label(text="The Reset Animation has no Targets!", icon="ERROR")


def draw_link_buttons(self, context: bpy.types.Context):
	"""The main 'Link Slots' buttons"""
	layout: bpy.types.UILayout = self.layout

	# Prepare legacy/newly created Action
	if(context.active_action.is_action_legacy):
		row = layout.row()
		row.alert = True
		layout.operator(PrepareLinks.bl_idname)
		return

	# Main link button
	row = layout.row(align=True)
	row.alignment = "EXPAND"
	row.operator(LinkSlots.bl_idname, text="Link Slots", icon="DECORATE_LINKED").use_reset = True
	if(context.active_action.slot_link.reset_animation):
		row.operator(LinkSlots.bl_idname, text="..without Reset").use_reset = False


def draw_slot_target_selector(self, context: bpy.types.Context, slot: bpy.types.ActionSlot | None = None):
	"""Gui to select a Slots target"""
	layout: bpy.types.UILayout = self.layout

	if(slot is not None):
		active_slot: bpy.types.ActionSlot = slot
		slot_link = find_slot_link(context.active_action, slot.handle)
	elif(len(context.active_action.slots) > context.active_action.slot_link.active_index):
		active_slot: bpy.types.ActionSlot = context.active_action.slots[context.active_action.slot_link.active_index]
		slot_link = find_slot_link(context.active_action, active_slot.handle)
	else:
		return

	if(slot_link):
		layout.use_property_split = True
		col = layout.column()
		if(not slot_link.target):
			col.alert = True
		col.prop_search(slot_link, "target", bpy.data, "objects", icon="RIGHTARROW")
		if(not slot_link.target):
			split = col.split(factor=0.4)
			_ = split.row()
			split.label(text="Invalid Target", icon="WARNING_LARGE")

		if(active_slot.target_id_type in ["MATERIAL", "NODETREE"] and slot_link.target):
			col = layout.column()
			if(slot_link.datablock_index >= len(slot_link.target.data.materials)):
				col.alert = True

			col.prop(slot_link, "datablock_index", text="Material Index")

			split = col.split(factor=0.4)
			_ = split.row()
			if(slot_link.datablock_index >= len(slot_link.target.data.materials)):
				split.label(text="Invalid Material Index", icon="WARNING_LARGE")
			else:
				split.label(text=slot_link.target.data.materials[slot_link.datablock_index].name, icon="MATERIAL_DATA")
	else:
		row = layout.row()
		row.alert = True
		row.operator(AddSlotLink.bl_idname, icon="ADD").slot_handle = active_slot.handle


def draw_orphan_slots(self, context: bpy.types.Context):
	"""If a slot was removed, the SlotLink on the Action will remain. Remove any orphaned SlotLinks."""
	layout: bpy.types.UILayout = self.layout

	handled_slot_links = []
	for slot_index, slot in enumerate(context.active_action.slots):
		slot_link = find_slot_link(context.active_action, slot.handle)
		if(slot_link):
			handled_slot_links.append(slot_link)

	orphan_slot_links = []
	for slot_index, slot_link in enumerate(context.active_action.slot_link.links):
		if(slot_link not in handled_slot_links):
			orphan_slot_links.append((slot_index, slot_link))

	if(len(orphan_slot_links) > 0):
		layout.separator(factor=2, type="LINE")
		layout.label(text="These Links don't belong to any Slot!", icon="WARNING_LARGE")
		layout.label(text="Please delete them:")
		for slot_index, slot_link in orphan_slot_links:
			box = layout.box().row()
			box.label(text="Slot " + str(slot_index))
			box.operator(RemoveSlotLink.bl_idname, icon="X").index = slot_index


def draw_slot_link_editor(self, context: bpy.types.Context):
	"""Draw the full Slot Link editor GUI"""
	layout: bpy.types.UILayout = self.layout

	row = layout.row()
	row.alignment = "RIGHT"
	if(bpy.app.version[0] < 5 or bpy.app.version[1] < 2):
		row.operator(OpenDocumentation.bl_idname, icon="HELP")
	else:
		row.link(text="Slot Link Documentation", icon="HELP", url="https://docs.stfform.at/guide/blender/slot_link.html")

	draw_reset_animation_selector(self, context)
	layout.separator(factor=1)
	state = draw_link_messages(self, context)

	draw_link_buttons(self, context)
	if(not state): return

	layout.template_list(SlotLinkList.bl_idname, "", context.active_action, "slots", context.active_action.slot_link, "active_index")
	draw_slot_target_selector(self, context)

	draw_orphan_slots(self, context)
