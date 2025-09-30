import bpy
import decimal

from .slot_link import AddSlotLink, RemoveSlotLink, SlotLink, set_slot_link_poll_type
from .link_applier import LinkSlots, PrepareLinks
from .misc import OpenDocumentation


def _find_slot_link(action: bpy.types.Action, slot_handle: int) -> SlotLink:
	for slot_link in action.slot_links:
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

		if(context.active_action.is_action_legacy):
			self.layout.label(text="Please add a new Slot")
			self.layout.operator(PrepareLinks.bl_idname)
			return
		else:
			self.layout.operator(LinkSlots.bl_idname, text="Link Slots", icon="DECORATE_LINKED")

		prefix_row = self.layout.row()

		self.layout.template_list(SlotLinkList.bl_idname, "", context.active_action, "slots", context.active_action, "slot_links_active_index")

		if(len(context.active_action.slots) > context.active_action.slot_links_active_index):
			box = self.layout
			active_slot = context.active_action.slots[context.active_action.slot_links_active_index]
			slot_link: SlotLink = _find_slot_link(context.active_action, active_slot.handle)
			if(slot_link):
				if(active_slot.target_id_type in ["KEY", "MESH", "MATERIAL", "NODETREE"]):
					set_slot_link_poll_type(bpy.types.Mesh)
				elif(active_slot.target_id_type in ["ARMATURE"]):
					set_slot_link_poll_type(bpy.types.Armature)
				else:
					set_slot_link_poll_type(None)

				box.use_property_split = True
				box.prop_search(slot_link, "target", bpy.data, "objects")
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
			prefix_row.label(text="Not all Slots are Linked!", icon="WARNING_LARGE")
		else:
			prefix_row.label(text="Slot Links:")

		orphan_slot_links = []
		for slot_index, slot_link in enumerate(context.active_action.slot_links):
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

