import bpy
import decimal

from .slot_link import AddSlotLink, RemoveSlotLink, SlotLink, UpdateLegacySlotLink, set_slot_link_poll_type
from .link_applier import LinkSlots, PrepareLinks, UnlinkAction, check_action
from .misc import OpenDocumentation


def _find_slot_link(action: bpy.types.Action, slot_handle: int) -> SlotLink:
	for slot_link in action.slot_link.links:
		if(slot_link.slot_handle == slot_handle):
			return slot_link
	return None


class SlotLinkList(bpy.types.UIList):
	bl_idname = "COLLECTION_UL_slot_link_list"

	def draw_item(self, context: bpy.types.Context, layout: bpy.types.UILayout, data: bpy.types.Action, item: bpy.types.ActionSlot, icon, active_data, active_propname, index):
		slot_link: SlotLink = _find_slot_link(context.active_action, item.handle)
		if(not slot_link or not slot_link.target):
			layout.alert = True

		split = layout.split(factor=0.45)
		split.label(text=f"{item.name_display}", icon_value = item.target_id_type_icon)
		if(slot_link and slot_link.target):
			split.label(text=slot_link.target.name, icon="RIGHTARROW")
		else:
			split.label(text="NONE", icon="ERROR")


class SlotLinkEditor(bpy.types.Panel):
	"""Link the Slots of an Action to their targets"""
	bl_idname = "OBJECT_PT_slot_link_editor"
	bl_label = "Slot Link Editor"
	bl_region_type = "UI"
	bl_space_type = "DOPESHEET_EDITOR"
	bl_category = "Action"

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return (context.active_action is not None)

	def draw_header(self, context: bpy.types.Context):
		self.layout.label(icon="DECORATE_LINKED")

	def draw(self, context: bpy.types.Context):
		row = self.layout.row()
		row.alignment = "RIGHT"
		row.operator(OpenDocumentation.bl_idname, icon="HELP")

		# From old Slot Link version
		if(hasattr(context.active_action, "slot_links") and len(context.active_action.slot_links) > 0 and len(context.active_action.slot_link.links) == 0):
			self.layout.alert = True
			self.layout.label(text="Please migrate old Slot Link data!", icon="INFO")
			self.layout.operator(UpdateLegacySlotLink.bl_idname)
			return

		# Legacy/newly created Action handling
		if(context.active_action.is_action_legacy):
			row = self.layout.row()
			row.alert = True
			if(context.active_action.users <= 1): # good enough
				row.label(text="Please press 'Prepare' first!", icon="WARNING_LARGE")
			self.layout.operator(PrepareLinks.bl_idname)
			if(context.active_action.users > 1):
				self.layout.label(text="Please add a new Slot or animate any property!", icon="INFO")
			return

		# Reset animation
		self.layout.use_property_split = True
		if(not context.active_action.slot_link.reset_animation):
			self.layout.prop(context.active_action.slot_link, "is_reset_animation")
		if(not context.active_action.slot_link.is_reset_animation):
			self.layout.prop(context.active_action.slot_link, "reset_animation")
			if(context.active_action.slot_link.reset_animation and len(context.active_action.slot_link.reset_animation.slot_link.links) == 0):
				row = self.layout.row()
				row.alert = True
				row.label(text="The Reset Animation has no Targets!", icon="ERROR")
		self.layout.separator(factor=2, type="LINE")

		# Check whether this Action is linked everywhere state
		if(not check_action(context.active_action)):
			row = self.layout.row()
			row.alert = True
			row.label(text="Not Linked", icon="WARNING_LARGE")

		# Main link button
		row = self.layout.row()
		row_main = row.row()
		row_main.alignment = "EXPAND"
		row_main.operator(LinkSlots.bl_idname, text="Link Slots", icon="DECORATE_LINKED")
		if(context.active_action.slot_link.reset_animation):
			row_secondary = row.row()
			row_secondary.alignment = "RIGHT"
			row_secondary.operator(LinkSlots.bl_idname, text="Link Without Reset").use_reset = False


		prefix_row = self.layout.row()

		self.layout.template_list(SlotLinkList.bl_idname, "", context.active_action, "slots", context.active_action.slot_link, "active_index")

		if(len(context.active_action.slots) > context.active_action.slot_link.active_index):
			box = self.layout
			active_slot = context.active_action.slots[context.active_action.slot_link.active_index]
			slot_link: SlotLink = _find_slot_link(context.active_action, active_slot.handle)
			if(slot_link):
				if(active_slot.target_id_type in ["KEY", "MESH", "MATERIAL", "NODETREE"]):
					set_slot_link_poll_type(bpy.types.Mesh)
				elif(active_slot.target_id_type in ["ARMATURE"]):
					set_slot_link_poll_type(bpy.types.Armature)
				elif(active_slot.target_id_type in ["CAMERA"]):
					set_slot_link_poll_type(bpy.types.Camera)
				elif(active_slot.target_id_type in ["LIGHT"]):
					set_slot_link_poll_type(bpy.types.Light)
				else:
					set_slot_link_poll_type(None)

				box.use_property_split = True
				box.prop_search(slot_link, "target", bpy.data, "objects", icon="RIGHTARROW")
				if(active_slot.target_id_type in ["MATERIAL", "NODETREE"] and slot_link.target):
					col = box.column()
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
				box.operator(AddSlotLink.bl_idname, icon="ADD").slot_handle = active_slot.handle

		handled_slot_links = []
		successes = 0
		for slot_index, slot in enumerate(context.active_action.slots):
			slot_link: SlotLink = _find_slot_link(context.active_action, slot.handle)
			if(slot_link):
				handled_slot_links.append(slot_link)
				if(slot_link.target):
					successes += 1

		if(successes < len(context.active_action.slots)):
			prefix_row.alert = True
			prefix_row.label(text="Not all Slots have Targets!", icon="WARNING_LARGE")

		orphan_slot_links = []
		for slot_index, slot_link in enumerate(context.active_action.slot_link.links):
			if(slot_link not in handled_slot_links):
				orphan_slot_links.append((slot_index, slot_link))

		if(len(orphan_slot_links) > 0):
			self.layout.separator(factor=2, type="LINE")
			self.layout.label(text="These Links don't belong to any Slot!", icon="WARNING_LARGE")
			self.layout.label(text="Please delete them:")
			for slot_index, slot_link in orphan_slot_links:
				box = self.layout.box().row()
				box.label(text="Slot " + str(slot_index) + " (" + str(slot.target_id_type) + "): " + str(slot.name_display))
				box.operator(RemoveSlotLink.bl_idname, icon="X").index = slot_index
