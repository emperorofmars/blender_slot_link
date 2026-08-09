import bpy
from typing import Literal

from .slot_link import find_slot, retrieve_animation_data_holder
from .link_applier import prepare_all_data_blocks


__all__ = ["ToNLA"]


def _setup_action_to_nla(action: bpy.types.Action, start_frame: int | None = None) -> int:
	if(start_frame is None):
		start_frame = int(action.frame_range[0])
	for slot_link in action.slot_link.links:
		slot = find_slot(action, slot_link.slot_handle)
		if(not slot):
			continue
		for link_target in slot_link.targets:
			animdata_holder = retrieve_animation_data_holder(slot.target_id_type, link_target.target, link_target.datablock_index)
			if(not animdata_holder):
				continue
			if(not animdata_holder.animation_data):
				animdata_holder.animation_data_create()
			animation_data: bpy.types.AnimData = animdata_holder.animation_data

			track = animation_data.nla_tracks.new()
			track.name = action.name
			strip = track.strips.new(action.name, start_frame, action)
			strip.action_slot = slot
			strip.extrapolation = "NOTHING"
	return start_frame + int(action.frame_range[1]) + 2


class ToNLA(bpy.types.Operator):
	"""Setup all slot link animations onto the NLA in an export ready representation"""
	bl_idname = "slot_link.to_nla"
	bl_label = "Prepare NLA Export"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return len(bpy.data.actions) > 0

	def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]]:
		return context.window_manager.invoke_confirm(self, event, title="Prepare NLA Export", message="This will clear all NLA data!", icon="WARNING")

	def execute(self, context: bpy.types.Context) -> set:
		prepare_all_data_blocks(None, True)

		start_frame: int | None = None
		for action in bpy.data.actions:
			if(action.slot_link.is_reset_animation):
				start_frame = _setup_action_to_nla(action, start_frame)
		for action in bpy.data.actions:
			if(not action.slot_link.is_reset_animation):
				start_frame = _setup_action_to_nla(action, start_frame)

		return {"FINISHED"}



def register():
	bpy.utils.register_class(ToNLA)

def unregister():
	bpy.utils.unregister_class(ToNLA)
