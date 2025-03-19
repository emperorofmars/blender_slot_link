import bpy

from .slot_link import AddSlotLink, RemoveSlotLink
from .link_applier import LinkSlots, PrepareLinks


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
			self.layout.label(text="Preserve the targets of Actions")
			self.layout.label(text="and Slots, even if unlinked.")
			self.layout.separator(factor=1, type="SPACE")
			self.layout.label(text="Re-apply them by pressing \"Link This Action\".")
			self.layout.separator(factor=1, type="SPACE")
			self.layout.label(text="Prepare the Scene for animating a new")
			self.layout.label(text="Action by pressing \"Prepare\".")
			self.layout.separator(factor=1, type="SPACE")
			self.layout.label(text="Other extensions can use this information.")
			self.layout.label(text="For example for export.")
			self.layout.separator(factor=1, type="SPACE")
			self.layout.label(text="Note: This is a janky workaround,")
			self.layout.label(text="but without an alternative.")
			self.layout.label(text="Good luck!")
		self.layout.prop(context.scene, "slot_link_show_info")
		self.layout.separator(factor=1, type="SPACE")

		# Does this even work? All actions from a previous Blender version are not marked as legacy.
		if(context.active_action.is_action_legacy):
			self.layout.label(text="Legacy Actions are not supported!")
			return

		self.layout.operator(PrepareLinks.bl_idname)
		self.layout.operator(LinkSlots.bl_idname)
		self.layout.separator(factor=2, type="LINE")

		handled_slot_links = []

		for slot_index, slot in enumerate(context.active_action.slots):
			box = self.layout.box()
			box.label(text="Slot " + str(slot_index) + " (" + str(slot.target_id_type) + "): " + str(slot.name_display))

			selected_slot_link = None
			for slot_link in context.active_action.slot_links:
				if(slot_link.slot_handle == slot.handle):
					selected_slot_link = slot_link
					break
			if(selected_slot_link):
				handled_slot_links.append(selected_slot_link)
				box.prop(selected_slot_link, "target")
				if(slot.target_id_type in ["MATERIAL", "NODETREE"]):
					box.prop(selected_slot_link, "datablock_index", text="Material Index")
			else:
				box.operator(AddSlotLink.bl_idname).index = slot_index

		orphan_slot_links = []
		for slot_index, slot_link in enumerate(context.active_action.slot_links):
			if(slot_link not in handled_slot_links):
				orphan_slot_links.append((slot_index, slot_link))

		if(len(orphan_slot_links) > 0):
			self.layout.separator(factor=2, type="LINE")
			self.layout.label(text="These Links don't belong to any Slot!")
			self.layout.label(text="Consider deleting them.")
			for slot_index, slot_link in orphan_slot_links:
				box = self.layout.box().row()
				box.label(text="Slot " + str(slot_index) + " (" + str(slot.target_id_type) + "): " + str(slot.name_display))
				box.operator(RemoveSlotLink.bl_idname).index = slot_index
