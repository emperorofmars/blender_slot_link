import bpy

from .package_key import package_key
from .slot_link import ActionSlotLink, AddSlotLink, RemoveSlotLink, find_slot_link
from .link_applier import LinkSlots, PrepareLinks, check_action, check_slot_link_target_unique

__all__ = ["draw_link_messages", "draw_reset_animation_selector", "draw_link_buttons", "draw_slot_target_selector", "draw_orphan_slots", "draw_slot_link_editor"]


class SlotLinkList(bpy.types.UIList):
	"""Display the Slot Link for each Slot of an Action"""
	bl_idname = "COLLECTION_UL_slot_link_list"

	def draw_item(self, context: bpy.types.Context, layout: bpy.types.UILayout, data: bpy.types.Action, item: bpy.types.ActionSlot, icon: int, active_data: ActionSlotLink, active_property: str, index, flt_flag: int | None):
		slot_link = find_slot_link(context.active_action, item.handle) # pyright: ignore[reportArgumentType]
		if(not slot_link or not slot_link.target or not check_slot_link_target_unique(data, item)):
			layout.alert = True

		split = layout.split(factor=0.45)
		split.label(text=f"{item.name_display} ({item.target_id_type.capitalize()})", icon_value = item.target_id_type_icon)

		if(not slot_link or not slot_link.target):
			split.label(text="NONE", icon="ERROR")
			return

		row = split.row()
		row.label(text=slot_link.target.name, icon="RIGHTARROW")
		if(item.target_id_type in ["MATERIAL", "NODETREE"]):
			row.label(icon="RIGHTARROW")
			handled = False
			if(slot_link.target.material_slots and len(slot_link.target.material_slots) > slot_link.datablock_index):
				target_material_slot: bpy.types.MaterialSlot = slot_link.target.material_slots[slot_link.datablock_index]
				if(item.target_id_type == "MATERIAL" and target_material_slot.material):
					row.label(text=target_material_slot.material.name, icon_value=item.target_id_type_icon)
					handled = True
				elif(item.target_id_type == "NODETREE" and target_material_slot.material and target_material_slot.material.node_tree):
					handled = True
					row.label(text=target_material_slot.material.node_tree.name, icon_value=item.target_id_type_icon)
			if(not handled):
				row.label(text=f"[ Material {slot_link.datablock_index} ]", icon_value=item.target_id_type_icon)


def draw_link_messages(layout: bpy.types.UILayout, context: bpy.types.Context, only_error: bool = False) -> int:
	"""Draw warnings"""
	action: bpy.types.Action = context.active_action # pyright: ignore[reportAssignmentType]

	if(action.is_action_legacy):
		if(action.users <= 1): # good enough
			row = layout.row()
			row.alert = True
			row.label(text="Prepare the Action!", icon="WARNING_LARGE")
			return -1
		if(action.users > 1):
			row = layout.row()
			row.label(text="Please add a new Slot!", icon="INFO")
			return -1

	# Check if some Slots want to be linked to the same datablock
	for slot in action.slots:
		if(not check_slot_link_target_unique(action, slot)):
			row = layout.row()
			row.alert = True
			row.label(text="Some Slots have duplicate Targets!", icon="WARNING_LARGE")
			return 1

	# Check if all Slots have targets
	successes = 0
	for slot in action.slots:
		slot_link = find_slot_link(action, slot.handle)
		if(slot_link and slot_link.target): # TODO check if the target supports all animated properties
			successes += 1
	if(successes < len(action.slots)):
		row = layout.row()
		row.alert = True
		row.label(text="Not all Slots have Targets!", icon="WARNING_LARGE")
		return 1

	# Check whether this Action is linked everywhere state
	if(not only_error and not check_action(action)):
		row = layout.row()
		row.alert = True
		row.label(text="Not Linked!", icon="WARNING_LARGE")
		return 0
	return 0


def draw_reset_animation_selector(layout: bpy.types.UILayout, context: bpy.types.Context):
	"""Mark the Action as a reset animation, or select a reset animation"""
	layout = layout.column(align=True)

	# Reset animation
	if(not context.active_action.slot_link.reset_animation):
		layout.prop(context.active_action.slot_link, "is_reset_animation")
	if(not context.active_action.slot_link.is_reset_animation):
		layout.prop(context.active_action.slot_link, "reset_animation")
		if(context.active_action.slot_link.reset_animation and len(context.active_action.slot_link.reset_animation.slot_link.links) == 0):
			row = layout.row()
			row.alert = True
			row.label(text="The Reset Animation has no Targets!", icon="ERROR")


def draw_link_buttons(layout: bpy.types.UILayout, context: bpy.types.Context, only_one_button: bool = False, scale: float = 1):
	"""The main 'Link Slots' buttons"""
	# Prepare legacy/newly created Action
	if(context.active_action.is_action_legacy):
		row = layout.row()
		row.alert = True
		layout.operator(PrepareLinks.bl_idname)
		return

	state = check_action(context.active_action) # pyright: ignore[reportArgumentType]

	# Main link button
	row = layout.row(align=True)
	row.alignment = "EXPAND"
	row.alert = state == 0
	row.scale_x = row.scale_y = scale
	row.operator(LinkSlots.bl_idname, text="Link Slots", icon="DECORATE_LINKED").use_reset = True
	if(not only_one_button and context.active_action.slot_link.reset_animation):
		row = row.row(align=True)
		row.alignment = "RIGHT"
		row.operator(LinkSlots.bl_idname, text="..without Reset").use_reset = False


def draw_slot_target_selector(layout: bpy.types.UILayout, context: bpy.types.Context, slot: bpy.types.ActionSlot | None = None):
	"""Gui to select a Slots target"""
	if(slot is not None):
		active_slot: bpy.types.ActionSlot = slot
		slot_link = find_slot_link(context.active_action, slot.handle) # pyright: ignore[reportArgumentType]
	elif(len(context.active_action.slots) > context.active_action.slot_link.active_index):
		active_slot: bpy.types.ActionSlot = context.active_action.slots[context.active_action.slot_link.active_index]
		slot_link = find_slot_link(context.active_action, active_slot.handle) # pyright: ignore[reportArgumentType]
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


def draw_orphan_slots(layout: bpy.types.UILayout, context: bpy.types.Context):
	"""If a slot was removed, the SlotLink on the Action will remain. Remove any orphaned SlotLinks."""
	handled_slot_links = []
	for slot_index, slot in enumerate(context.active_action.slots):
		slot_link = find_slot_link(context.active_action, slot.handle) # pyright: ignore[reportArgumentType]
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


def draw_slot_link_editor(layout: bpy.types.UILayout, context: bpy.types.Context):
	"""Draw the full Slot Link editor GUI"""
	if(not context.preferences.addons[package_key].preferences.hide_documentation_link):
		row = layout.row()
		row.alignment = "RIGHT"
		if(bpy.app.version[0] < 5 or bpy.app.version[1] < 2):
			row.operator("wm.url_open", text="Slot Link Documentation", icon="HELP").url = "https://docs.stfform.at/guide/blender/slot_link.html"
		else:
			row.link(text="Slot Link Documentation", icon="HELP", url="https://docs.stfform.at/guide/blender/slot_link.html")

	draw_reset_animation_selector(layout, context)
	layout.separator(factor=1)
	state = draw_link_messages(layout, context)

	draw_link_buttons(layout, context, scale=1.3)
	if(state < 0): return

	if(not context.preferences.addons[package_key].preferences.hide_slot_link_list):
		layout.template_list(SlotLinkList.bl_idname, "", context.active_action, "slots", context.active_action.slot_link, "active_index")
		draw_slot_target_selector(layout, context)
	elif(state == 1):
		row = layout.row()
		row_icon = row.row()
		row_text = row.column(align=True)
		row_icon.label(icon="INFO_LARGE")
		row_text.label(text="First select a Slot on the left.")
		row_text.label(text="Then select a Target in the Slot panel")

	draw_orphan_slots(layout, context)
