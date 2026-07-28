import bpy

from .package_key import get_preferences
from .slot_link import ActionSlotLink, find_slot_link
from .slot_link_ops import AddSlotLink, RemoveSlotLink, LinkSlots, PrepareLinks
from .link_applier import check_action, check_slot_link_target_unique


__all__ = ["draw_link_messages", "draw_reset_animation_selector", "draw_link_buttons", "draw_slot_target_selector", "draw_orphan_slots", "draw_slot_link_editor"]


class SlotLinkList(bpy.types.UIList):
	"""Display the Slot Link for each Slot of an Action"""
	bl_idname = "COLLECTION_UL_slot_link_list"

	def draw_item(self, context: bpy.types.Context, layout: bpy.types.UILayout, data: bpy.types.Action, item: bpy.types.ActionSlot, icon: int, active_data: ActionSlotLink, active_property: str, index, flt_flag: int | None):
		slot_link = find_slot_link(context.active_action, item.handle) # pyright: ignore[reportArgumentType]
		if(not slot_link or not slot_link.target or not check_slot_link_target_unique(data, item)):
			layout.alert = True

		split = layout.split(factor=0.45)
		split.label(text=f"{item.name_display} ({item.target_id_type.capitalize()})", icon_value=item.target_id_type_icon)

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
				row.alert = True
				row.label(text=f"[ Material {slot_link.datablock_index} ]", icon="ERROR")


def draw_link_messages(layout: bpy.types.UILayout, action: bpy.types.Action, only_error: bool = False) -> int:
	"""Draw warnings"""

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
			if(slot.target_id_type in ["MATERIAL", "NODETREE"]):
				valid_material = True
				if(slot_link.target.material_slots and len(slot_link.target.material_slots) <= slot_link.datablock_index):
					valid_material = False
				elif(not slot_link.target.material_slots[slot_link.datablock_index].material):
					valid_material = False
				elif(slot.target_id_type == "NODETREE" and slot_link.target.material_slots[slot_link.datablock_index].material.node_tree):
					valid_material = False
				if(not valid_material):
					row = layout.row()
					row.alert = True
					row.label(text="Some Slots have invalid Material indices!", icon="WARNING_LARGE")
					return 1
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


def draw_reset_animation_selector(layout: bpy.types.UILayout, action: bpy.types.Action):
	"""Mark the Action as a reset animation, or select a reset animation"""
	layout = layout.column(align=True)

	# Reset animation
	if(not action.slot_link.reset_animation):
		layout.prop(action.slot_link, "is_reset_animation")
	if(not action.slot_link.is_reset_animation):
		layout.prop(action.slot_link, "reset_animation")
		if(action.slot_link.reset_animation and len(action.slot_link.reset_animation.slot_link.links) == 0):
			row = layout.row()
			row.alert = True
			row.label(text="The Reset Animation has no Targets!", icon="ERROR")


def draw_link_buttons(layout: bpy.types.UILayout, action: bpy.types.Action, only_one_button: bool = False, scale: float = 1):
	"""The main 'Link Slots' buttons"""
	# Prepare legacy/newly created Action
	if(action.is_action_legacy):
		row = layout.row()
		row.alert = True
		layout.operator(PrepareLinks.bl_idname)
		return

	state = check_action(action)

	# Main link button
	row = layout.row(align=True)
	row.alignment = "EXPAND"
	row.alert = state == 0
	row.scale_x = row.scale_y = scale
	row.operator(LinkSlots.bl_idname, text="Link Slots", icon="DECORATE_LINKED").use_reset = True
	if(not only_one_button and action.slot_link.reset_animation):
		row = row.row(align=True)
		row.alignment = "RIGHT"
		row.operator(LinkSlots.bl_idname, text="..without Reset").use_reset = False


def draw_slot_target_selector(layout: bpy.types.UILayout, action: bpy.types.Action, slot: bpy.types.ActionSlot | None = None, is_slot_panel: bool = False, compact_layout: bool = False):
	"""Gui to select a Slots target"""
	if(slot is not None):
		active_slot: bpy.types.ActionSlot = slot
		slot_link = find_slot_link(action, slot.handle)
	elif(len(action.slots) > action.slot_link.active_index):
		active_slot: bpy.types.ActionSlot = action.slots[action.slot_link.active_index]
		slot_link = find_slot_link(action, active_slot.handle)
	else:
		return

	if(not is_slot_panel):
		layout.label(text=f"{active_slot.name_display} ({active_slot.target_id_type.capitalize()}):", icon_value=active_slot.target_id_type_icon)

	if(slot_link):
		if(compact_layout):
			layout.use_property_split = False

			row = layout.row()
			row.label(text="Target")
			if(slot_link.target and active_slot.target_id_type in ["MATERIAL", "NODETREE"]):
				row.label(text="Material Index")

			if(not slot_link.target):
				layout.alert = True
			elif(active_slot.target_id_type in ["MATERIAL", "NODETREE"] and slot_link.datablock_index >= len(slot_link.target.data.materials)):
				layout.alert = True
			elif(not check_slot_link_target_unique(action, active_slot)):
				layout.alert = True

			selector_layout = layout.row(align=True)
			if(not slot_link.target):
				selector_layout.alert = True

			selector_layout.prop_search(slot_link, "target", bpy.data, "objects", text="", icon="RIGHTARROW")

			if(slot_link.target and active_slot.target_id_type in ["MATERIAL", "NODETREE"]):
				if(slot_link.datablock_index >= len(slot_link.target.data.materials)):
					selector_layout.alert = True
				selector_layout.prop(slot_link, "datablock_index", text=(slot_link.target.data.materials[slot_link.datablock_index].name if slot_link.datablock_index < len(slot_link.target.data.materials) else "Invalid Material Index"))

			if(not slot_link.target):
				layout.label(text="Invalid Target", icon="WARNING_LARGE")
			elif(active_slot.target_id_type in ["MATERIAL", "NODETREE"] and slot_link.datablock_index >= len(slot_link.target.data.materials)):
				layout.label(text="Invalid Material Index", icon="WARNING_LARGE")
			elif(not check_slot_link_target_unique(action, active_slot)):
				layout.label(text="Duplicate Target!", icon="WARNING_LARGE")

		else:
			layout.use_property_split = True

			if(not slot_link.target):
				layout.alert = True
			elif(active_slot.target_id_type in ["MATERIAL", "NODETREE"] and slot_link.datablock_index >= len(slot_link.target.data.materials)):
				layout.alert = True
			elif(not check_slot_link_target_unique(action, active_slot)):
				layout.alert = True

			selector_layout = layout.column(align=True)
			if(not slot_link.target):
				selector_layout.alert = True

			selector_layout.prop_search(slot_link, "target", bpy.data, "objects", icon="RIGHTARROW")
			if(not slot_link.target):
				selector_layout.label(text="Invalid Target", icon="WARNING_LARGE")

			if(slot_link.target and active_slot.target_id_type in ["MATERIAL", "NODETREE"]):
				if(slot_link.datablock_index >= len(slot_link.target.data.materials)):
					selector_layout.alert = True

				selector_layout.prop(slot_link, "datablock_index", text="Material Index")
				split = selector_layout.split(factor=0.4)
				split.row()
				row = split.row()
				if(slot_link.datablock_index < len(slot_link.target.data.materials)):
					row.label(text=slot_link.target.data.materials[slot_link.datablock_index].name, icon="MATERIAL")
				else:
					row.alert = True
					row.label(text="Invalid Material Index", icon="ERROR")

			if(not check_slot_link_target_unique(action, active_slot)):
				selector_layout.label(text="Duplicate Target!", icon="WARNING_LARGE")
	else:
		row = layout.row()
		row.alert = True
		row.operator(AddSlotLink.bl_idname, icon="ADD").slot_handle = active_slot.handle


def draw_orphan_slots(layout: bpy.types.UILayout, action: bpy.types.Action):
	"""If a slot was removed, the SlotLink on the Action will remain. Remove any orphaned SlotLinks."""
	handled_slot_links = []
	for slot_index, slot in enumerate(action.slots):
		slot_link = find_slot_link(action, slot.handle)
		if(slot_link):
			handled_slot_links.append(slot_link)

	orphan_slot_links = []
	for slot_index, slot_link in enumerate(action.slot_link.links):
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


def draw_slot_link_editor(layout: bpy.types.UILayout, action: bpy.types.Action):
	"""Draw the full Slot Link editor GUI"""
	if(not get_preferences().hide_documentation_link):
		row = layout.row()
		row.alignment = "RIGHT"
		if(bpy.app.version[0] < 5 or bpy.app.version[1] < 2):
			row.operator("wm.url_open", text="Slot Link Documentation", icon="HELP").url = "https://docs.stfform.at/guide/blender/slot_link.html"
		else:
			row.link(text="Slot Link Documentation", icon="HELP", url="https://docs.stfform.at/guide/blender/slot_link.html")

	draw_reset_animation_selector(layout, action)
	layout.separator(factor=1)
	state = draw_link_messages(layout, action)

	draw_link_buttons(layout, action, scale=1.3)
	if(state < 0): return

	if(not get_preferences().hide_slot_link_list):
		layout.template_list(SlotLinkList.bl_idname, "", action, "slots", action.slot_link, "active_index")
		draw_slot_target_selector(layout, action)
	elif(state == 1):
		row = layout.row()
		row_icon = row.row()
		row_text = row.column(align=True)
		row_icon.label(icon="INFO_LARGE")
		row_text.label(text="First select a Slot on the left.")
		row_text.label(text="Then select a Target in the Slot panel")

	draw_orphan_slots(layout, action)


def register():
	bpy.utils.register_class(SlotLinkList)

def unregister():
	bpy.utils.unregister_class(SlotLinkList)
