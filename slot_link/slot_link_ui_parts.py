import bpy
from typing import Literal

from .preferences import get_preferences
from .slot_link import ActionSlotLink, SlotLinkTarget, find_slot_link
from .slot_link_ops import SetupSlotLink, AddSlotLinkTarget, RemoveSlotLink, LinkSlots, PrepareLinks, RemoveSlotLinkTarget, SetupAction, MigrateSlotLink_0_2
from .link_validator import SlotLinkActionState, SlotLinkError, check_slot_link_target_unique, check_slot_link_all_targets_unique, is_action_linked, is_nla_clean, validate_action


__all__ = ["draw_link_messages", "draw_link_buttons", "draw_slot_target_selector", "draw_orphan_slots", "draw_slot_link_editor", "AnimationSelector"]


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
			if(active_data.target_collection and not link_target.target in active_data.target_collection.all_objects.values()):
				row.alert = True
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


def draw_link_messages(layout: bpy.types.UILayout, action: bpy.types.Action, state: SlotLinkActionState, only_error: bool = False) -> int:
	"""Draw warnings"""

	if(not is_nla_clean()):
		row = layout.row()
		row.label(text="Actions stashed on NLA, consider clearing them!", icon="INFO_LARGE")

	if(state.ok):
		return 0
	elif(state.error == SlotLinkError.NOT_LINKED and only_error):
		return 1

	match(state.error):
		case SlotLinkError.NOT_LINKED:
			row = layout.row()
			row.alert = True
			row.label(text="Not Linked!", icon="WARNING_LARGE")
			return 0
		case SlotLinkError.NOT_PREPARED:
			row = layout.row()
			row.alert = True
			row.label(text="Prepare the Action!", icon="WARNING_LARGE")
			return -1
		case SlotLinkError.NO_SLOT:
			row = layout.row()
			row.label(text="Please add a new Slot! (animate anything)", icon="INFO")
			return -1
		case SlotLinkError.SLOTS_DUPLICATE_TARGETS:
			row = layout.row()
			row.alert = True
			row.label(text="Some Slots have duplicate Targets!", icon="WARNING_LARGE")
			return 1
		case SlotLinkError.SLOTS_NOT_SETUP:
			row = layout.row()
			row.alert = True
			row.label(text="Some Slots are not set up!", icon="WARNING_LARGE")
			return 1
		case SlotLinkError.TARGETS_OUTSIDE_COLLECTION:
			row = layout.row()
			row.alert = True
			row.label(text="Some Targets are outside Collection!", icon="WARNING_LARGE")
			return 0
		case SlotLinkError.SLOTS_INVALID_MATERIAL_INDEX:
			row = layout.row()
			row.alert = True
			row.label(text="Some Slots have invalid Material indices!", icon="WARNING_LARGE")
			return 1
		case SlotLinkError.SLOTS_MISSING_TARGET:
			row = layout.row()
			row.alert = True
			row.label(text="Not all Slots have Targets!", icon="WARNING_LARGE")
			return 1
		case SlotLinkError.MIGRATION_2_0_NEEDED:
			row = layout.row()
			row.alert = True
			row.label(text="Please migrate to newer data-model!")
			return -1
		case _:
			row = layout.row()
			row.alert = True
			row.label(text="Unknown Error")
			return -1


def draw_link_buttons(layout: bpy.types.UILayout, action: bpy.types.Action, state: SlotLinkActionState, only_one_button: bool = False, scale: float = 1):
	"""The main 'Link Slots' buttons"""

	if(state.error == SlotLinkError.MIGRATION_2_0_NEEDED):
		row = layout.row(align=True)
		row.alert = True
		row.operator(MigrateSlotLink_0_2.bl_idname, icon="WARNING_LARGE")
		return

	# Prepare legacy/newly created Action
	if(state.error in [SlotLinkError.NOT_PREPARED, SlotLinkError.NO_SLOT]):
		row = layout.row(align=True)
		row.alert = state.error == SlotLinkError.NOT_PREPARED
		row.operator(PrepareLinks.bl_idname)
		return

	# Main link button
	row = layout.row(align=True)
	row.alignment = "EXPAND"
	row.alert = state.error == SlotLinkError.NOT_LINKED or not is_action_linked(action)
	row.scale_x = row.scale_y = scale
	row.operator(LinkSlots.bl_idname, text="Link Slots", icon="DECORATE_LINKED").use_reset_animation = True
	if(not only_one_button and action.slot_link.reset_animation):
		row = row.row(align=True)
		row.alignment = "RIGHT"
		row.operator(LinkSlots.bl_idname, text="..without Reset").use_reset_animation = False


def draw_slot_target_selector(layout: bpy.types.UILayout, action: bpy.types.Action, slot: bpy.types.ActionSlot | None = None, is_slot_panel: bool = False):
	"""GUI to select Slot targets"""
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
			link_target: SlotLinkTarget = link_target
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
		row.operator(SetupSlotLink.bl_idname, icon="ADD").slot_handle = active_slot.handle


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

	# Target collection
	col = layout.column(align=True)
	col.prop(action.slot_link, "target_collection")
	col.separator(factor=1, type="SPACE")

	# Reset animation
	if(not action.slot_link.reset_animation):
		col.prop(action.slot_link, "is_reset_animation")
	if(not action.slot_link.is_reset_animation):
		col.prop(action.slot_link, "reset_animation")
		if(action.slot_link.reset_animation and len(action.slot_link.reset_animation.slot_link.links) == 0):
			row = col.row()
			row.alert = True
			row.label(text="The Reset Animation has no Targets!", icon="ERROR")

	layout.separator(factor=1)

	# Messages
	state = validate_action(action)
	draw_link_messages(layout, action, state)

	for slot in action.slots:
		if(not find_slot_link(action, slot.handle)):
			row = layout.row()
			row.scale_x = row.scale_y = 1.3
			row.operator(SetupAction.bl_idname, icon="AUTO")
			break

	draw_link_buttons(layout, action, state, scale=1.3)

	if(state.error in [SlotLinkError.NOT_PREPARED, SlotLinkError.NO_SLOT, SlotLinkError.MIGRATION_2_0_NEEDED]):
		return

	# Slot Link list
	if(not get_preferences().hide_slot_link_list):
		layout.template_list(SlotLinkList.bl_idname, "", action, "slots", action.slot_link, "active_index")
		draw_slot_target_selector(layout, action)
	elif(state.error in [SlotLinkError.SLOTS_NOT_SETUP, SlotLinkError.SLOTS_MISSING_TARGET, SlotLinkError.SLOTS_INVALID_MATERIAL_INDEX, SlotLinkError.SLOTS_DUPLICATE_TARGETS, SlotLinkError.TARGETS_OUTSIDE_COLLECTION]):
		row = layout.row()
		row_icon = row.row()
		row_text = row.column(align=True)
		row_icon.label(icon="INFO_LARGE")
		row_text.label(text="First select a Slot on the left.")
		row_text.label(text="Then select a Target in the Slot panel")

	draw_orphan_slots(layout, action)


class AnimationSelector(bpy.types.Operator):
	"""Select an action and immediately link its slots"""
	bl_idname = "slot_link.animation_selector"
	bl_label = "Select Animation"

	entries_per_column: int = 10

	use_reset: bpy.props.BoolProperty(name="Use Reset Animation (if set)", default=True)
	filter: bpy.props.StringProperty(name="Filter", options={"TEXTEDIT_UPDATE"})

	def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]]:
		return context.window_manager.invoke_popup(self, width=max(int(len(bpy.data.actions) / self.entries_per_column) * 140, 140)) # invoke_props_dialog

	def execute(self, context: bpy.types.Context) -> set[Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]]:
		return {"FINISHED"}

	def draw(self, context: bpy.types.Context):
		layout: bpy.types.UILayout = self.layout # pyright: ignore[reportAssignmentType]
		active_action = context.active_action if hasattr(context, "active_action") else None

		row = layout.row()
		row.label(text="Select Animation")
		row.prop(self, "filter", text="", icon="VIEWZOOM")
		layout.separator(factor=1, type="LINE")

		reset_actions_filtered = []
		actions_filtered = []
		for action in bpy.data.actions:
			if(not self.filter or self.filter.strip().lower() in action.name.lower()):
				if(action.slot_link.is_reset_animation):
					reset_actions_filtered.append(action)
				else:
					actions_filtered.append(action)

		def draw_item(layout: bpy.types.UILayout, action: bpy.types.Action):
			item_layout = layout.row()
			item_layout.alignment = "LEFT"
			item_layout.emboss = "PULLDOWN_MENU"
			if(active_action == action):
				item_layout.enabled = False
			state = validate_action(action)
			icon = "WARNING_LARGE" if not state.ok and state.error not in [SlotLinkError.NOT_LINKED, SlotLinkError.NOT_PREPARED, None] else "NONE"
			button = item_layout.operator(LinkSlots.bl_idname, text=action.name, icon=icon)
			button.action_name = action.name
			button.use_reset_animation = self.use_reset

		def draw_actions(actions: list[bpy.types.Action]):
			num_cols = max(1, int(len(actions) / self.entries_per_column))
			row = layout.row()
			columns = []
			for _ in range(num_cols):
				columns.append(row.column())

			for item_idx in range(0, len(actions)):
				col = columns[item_idx % num_cols]
				draw_item(col, actions[item_idx])

		if(len(reset_actions_filtered) > 0):
			layout.label(text="Reset Animations")
			draw_actions(reset_actions_filtered)
		layout.label(text="Animations")
		draw_actions(actions_filtered)

		layout.separator(factor=1, type="LINE")
		layout.prop(self, "use_reset")


def register():
	bpy.utils.register_class(SlotLinkList)
	bpy.utils.register_class(AnimationSelector)

def unregister():
	bpy.utils.unregister_class(AnimationSelector)
	bpy.utils.unregister_class(SlotLinkList)
