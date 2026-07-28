import bpy

from .package_key import get_preferences
from .slot_link import ActionSlotLink, find_slot_link
from .slot_link_ops import AddSlotLink, AddSlotLinkTarget, MigrateSlotLink_0_2, RemoveSlotLink, LinkSlots, PrepareLinks, RemoveSlotLinkTarget
from .link_applier import check_action, check_slot_link_target_unique, check_slot_link_all_targets_unique


__all__ = ["draw_link_messages", "draw_reset_animation_selector", "draw_link_buttons", "draw_slot_target_selector", "draw_orphan_slots", "draw_slot_link_editor"]


class SlotLinkList(bpy.types.UIList):
	"""Display the Slot Link for each Slot of an Action"""
	bl_idname = "COLLECTION_UL_slot_link_list"

	def draw_item(self, context: bpy.types.Context, layout: bpy.types.UILayout, data: bpy.types.Action, item: bpy.types.ActionSlot, icon: int, active_data: ActionSlotLink, active_property: str, index, flt_flag: int | None):
		slot_link = find_slot_link(context.active_action, item.handle) # pyright: ignore[reportArgumentType]
		if(not slot_link or len(slot_link.targets) == 0 or not check_slot_link_all_targets_unique(data, item)):
			layout.alert = True

		split = layout.split(factor=0.45)
		split.label(text=f"{item.name_display} ({item.target_id_type.capitalize()})", icon_value=item.target_id_type_icon)

		col = split.column(align=True)
		if(not slot_link or len(slot_link.targets) == 0):
			col.label(text="NONE", icon="ERROR")
			return
		for link_target_index, link_target in enumerate(slot_link.targets):
			row = col.row(align=True)
			if(not link_target or not link_target.target):
				row.alert = True
				row.label(text="NONE", icon="ERROR")
				continue
			row.label(text=link_target.target.name, icon=("RIGHTARROW" if link_target_index == 0 else "THREE_DOTS"))
			if(item.target_id_type in ["MATERIAL", "NODETREE"]):
				row.label(icon="RIGHTARROW")
				handled = False
				if(link_target.target.material_slots and len(link_target.target.material_slots) > link_target.datablock_index):
					target_material_slot: bpy.types.MaterialSlot = link_target.target.material_slots[link_target.datablock_index]
					if(item.target_id_type == "MATERIAL" and target_material_slot.material):
						row.label(text=target_material_slot.material.name, icon_value=item.target_id_type_icon)
						handled = True
					elif(item.target_id_type == "NODETREE" and target_material_slot.material and target_material_slot.material.node_tree):
						handled = True
						row.label(text=target_material_slot.material.node_tree.name, icon_value=item.target_id_type_icon)
				if(not handled):
					row.alert = True
					row.label(text=f"[ Material {link_target.datablock_index} ]", icon="ERROR")


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
		if(not check_slot_link_all_targets_unique(action, slot)):
			row = layout.row()
			row.alert = True
			row.label(text="Some Slots have duplicate Targets!", icon="WARNING_LARGE")
			return 1

	# Check if all Slots have targets
	successes = 0
	for slot in action.slots:
		slot_link = find_slot_link(action, slot.handle)
		if(slot_link and len(slot_link.targets) > 0): # TODO check if the target supports all animated properties
			link_target_successes = 0
			for link_target in slot_link.targets:
				if(not link_target.target):
					break
				if(slot.target_id_type in ["MATERIAL", "NODETREE"]):
					valid_material = True
					if(link_target.target.material_slots and len(link_target.target.material_slots) <= link_target.datablock_index):
						valid_material = False
					elif(not link_target.target.material_slots[link_target.datablock_index].material):
						valid_material = False
					elif(slot.target_id_type == "NODETREE" and not link_target.target.material_slots[link_target.datablock_index].material.node_tree):
						valid_material = False
					if(not valid_material):
						row = layout.row()
						row.alert = True
						row.label(text="Some Slots have invalid Material indices!", icon="WARNING_LARGE")
						return 1
				link_target_successes += 1
			if(len(slot_link.targets) == link_target_successes):
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


def draw_slot_target_selector(layout: bpy.types.UILayout, action: bpy.types.Action, slot: bpy.types.ActionSlot | None = None, is_slot_panel: bool = False):
	"""GUI to select a Slots targets"""
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
		layout.separator(factor=0.5, type="SPACE")

	if(slot_link):
		if(len(slot_link.targets) == 0):
			row = layout.row()
			row.alert = True
			row.operator(MigrateSlotLink_0_2.bl_idname, icon="WARNING_LARGE")
			return

		layout.use_property_split = False

		any_error = False
		for link_target_index, link_target in enumerate(slot_link.targets):
			target_layout = layout.column()
			if(not link_target.target):
				target_layout.alert = True
				any_error = True
			elif(active_slot.target_id_type in ["MATERIAL", "NODETREE"] and link_target.datablock_index >= len(link_target.target.data.materials)):
				target_layout.alert = True
				any_error = True
			elif(not check_slot_link_target_unique(action, active_slot, link_target)):
				target_layout.alert = True
				any_error = True

			selector_layout = target_layout.row(align=True)
			if(not link_target.target):
				selector_layout.alert = True

			selector_layout.prop_search(link_target, "target", bpy.data, "objects", text="", icon="RIGHTARROW")

			if(link_target.target and active_slot.target_id_type in ["MATERIAL", "NODETREE"]):
				if(link_target.datablock_index >= len(link_target.target.data.materials)):
					selector_layout.alert = True
				selector_layout.prop(link_target, "datablock_index", text=(link_target.target.data.materials[link_target.datablock_index].name if link_target.datablock_index < len(link_target.target.data.materials) else "Invalid Material Index"))

			if(len(slot_link.targets) > 1):
				delete_row = selector_layout.row()
				delete_row.alignment = "RIGHT"
				delete_row.alert = False
				delete_button = delete_row.operator(RemoveSlotLinkTarget.bl_idname, text="", icon="X")
				delete_button.slot_handle = slot_link.slot_handle
				delete_button.target_index = link_target_index

			if(not link_target.target):
				row = target_layout.row()
				row.alignment = "CENTER"
				row.label(text="Invalid Target", icon="WARNING_LARGE")
			elif(active_slot.target_id_type in ["MATERIAL", "NODETREE"] and link_target.datablock_index >= len(link_target.target.data.materials)):
				row = target_layout.row()
				row.alignment = "CENTER"
				row.label(text="Invalid Material Index", icon="WARNING_LARGE")
			elif(not check_slot_link_target_unique(action, active_slot, link_target)):
				row = target_layout.row()
				row.alignment = "CENTER"
				row.label(text="Duplicate Target!", icon="WARNING_LARGE")

			if(link_target_index < len(slot_link.targets) - 1):
				layout.separator(factor=0.5, type="LINE")

		if(not any_error):
			layout.separator(factor=0.5, type="SPACE")
			row = layout.row()
			row.alignment = "LEFT"
			row.operator(AddSlotLinkTarget.bl_idname, icon="PLUS").slot_handle = slot_link.slot_handle
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

	for slot_link in action.slot_link.links:
		if(len(slot_link.targets) == 0):
			row = layout.row()
			row.alert = True
			row.operator(MigrateSlotLink_0_2.bl_idname, icon="WARNING_LARGE")
			return

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
