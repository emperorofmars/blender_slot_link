import bpy

from .slot_link import AddSlotLink, RemoveSlotAssignment
from .link_applier import LinkSlots, UnlinkAllSlots


class SlotLinkEditor(bpy.types.Panel):
	"""Link the Slots of an Action to their Targets"""
	bl_idname = "OBJECT_PT_slot_link_editor"
	bl_label = "Slot Link Editor"
	bl_region_type = "UI"
	bl_space_type = "DOPESHEET_EDITOR"
	bl_category = "Action"

	@classmethod
	def poll(cls, context):
		return (context.active_action is not None)

	def draw(self, context):
		if(context.scene.slot_link_show_info):
			self.layout.label(text="In Blender, any given data-block")
			self.layout.label(text="can be targeted by only one Slot :(")
			self.layout.label(text="This is not how the rest of the world works.")
			self.layout.separator(factor=1, type="SPACE")
			self.layout.label(text="Assign Slots with this UI,")
			self.layout.label(text="until Blender fixes this limitation.")
			self.layout.separator(factor=1, type="SPACE")
			self.layout.label(text="Other extensions can use this information.")
			self.layout.label(text="For example for export.")
			self.layout.separator(factor=1, type="SPACE")
			self.layout.label(text="Note: This workaround is jank but without an alternative.")
			self.layout.label(text="Good luck!")
		self.layout.prop(context.scene, "slot_link_show_info")
		self.layout.separator(factor=1, type="SPACE")

		# Does this even work? All actions from a previous Blender version are not marked as legacy.
		if(context.active_action.is_action_legacy):
			self.layout.label(text="Legacy Actions are not supported!")
			return

		self.layout.operator(UnlinkAllSlots.bl_idname)
		self.layout.operator(LinkSlots.bl_idname)
		self.layout.separator(factor=2, type="LINE")

		for slot_index, slot in enumerate(context.active_action.slots):
			box = self.layout.box()
			box.label(text="Slot " + str(slot_index) + " (" + str(slot.target_id_type) + "): " + str(slot.name_display))

			selected_slot_link = None
			for slot_link in context.active_action.slot_links:
				if(slot_link.slot_handle == slot.handle):
					selected_slot_link = slot_link
					break
			if(selected_slot_link):
				box.prop(selected_slot_link, "target")
				if(slot.target_id_type in ["MATERIAL", "NODETREE"]):
					box.prop(selected_slot_link, "datablock_index")
			else:
				box.operator(AddSlotLink.bl_idname).index = slot_index

		# TODO deal with orphan assignment objects

