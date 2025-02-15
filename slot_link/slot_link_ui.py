import bpy

from .slot_link import AddSlotLink, RemoveSlotAssignment

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

		for slot_index, slot in enumerate(context.active_action.slots):
			box = self.layout.box()
			box.label(text="Slot " + str(slot_index) + ": " + str(slot.name_display))

			slot_assignment = None
			for assignment in context.active_action.slot_link:
				if(assignment.slot_handle == slot.handle):
					slot_assignment = assignment
					break
			if(slot_assignment):
				box.prop(assignment, "target")
			else:
				box.operator(AddSlotLink.bl_idname).index = slot_index

		# TODO deal with orphan assignment objects

