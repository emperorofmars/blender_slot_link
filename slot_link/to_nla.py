import bpy
from typing import Literal

from .slot_link import find_slot, retrieve_animation_data_holder
from .link_applier import prepare_all_data_blocks
from .util import is_any_action_valid, needs_migrate_2_0


__all__ = ["ToNLA"]


def _setup_action_to_nla(action: bpy.types.Action, start_frame: int = 1) -> int:
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
	return start_frame + int(action.frame_range[1] - action.frame_range[0]) + 2


def _setup_all_actions_to_nla():
	prepare_all_data_blocks(None, True)

	start_frame = 1
	for action in bpy.data.actions:
		if(action.slot_link.is_reset_animation):
			start_frame = _setup_action_to_nla(action, start_frame)
	for action in bpy.data.actions:
		if(not action.slot_link.is_reset_animation):
			start_frame = _setup_action_to_nla(action, start_frame)


class ToNLA(bpy.types.Operator):
	"""Setup all slot link animations onto the NLA in an export ready representation"""
	bl_idname = "slot_link.to_nla"
	bl_label = "Prepare NLA Export"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return len(bpy.data.actions) > 0 and is_any_action_valid() and not needs_migrate_2_0()

	def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]]:
		return context.window_manager.invoke_confirm(self, event, title="Prepare NLA Export", message="This will clear all NLA data!", icon="WARNING")

	def execute(self, context: bpy.types.Context) -> set:
		_setup_all_actions_to_nla()
		return {"FINISHED"}


class ExportFBX(bpy.types.Operator):
	"""Setup all slot link animations onto the NLA and open the FBX exporter with sane settings"""
	bl_idname = "slot_link.export_fbx"
	bl_label = "Export FBX"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return len(bpy.data.actions) > 0 and is_any_action_valid() and not needs_migrate_2_0()

	def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]]:
		return context.window_manager.invoke_confirm(self, event, title="NLA to FBX Export", message="This will clear all NLA data!", icon="WARNING")

	def execute(self, context: bpy.types.Context) -> set:
		_setup_all_actions_to_nla()
		return bpy.ops.export_scene.fbx("INVOKE_DEFAULT",
			apply_scale_options="FBX_SCALE_ALL",
			axis_forward="-Z",
			axis_up="Y",
			apply_unit_scale=True,
			use_space_transform=True,
			bake_space_transform=False,
			use_mesh_modifiers=False,
			add_leaf_bones=False,
			bake_anim_use_all_bones=False,
			bake_anim_use_nla_strips=True,
			bake_anim_use_all_actions=False,
			bake_anim_force_startend_keying=True,
		)


def register():
	bpy.utils.register_class(ToNLA)
	bpy.utils.register_class(ExportFBX)

def unregister():
	bpy.utils.unregister_class(ExportFBX)
	bpy.utils.unregister_class(ToNLA)
