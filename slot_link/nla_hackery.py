import bpy
from typing import Literal

from .slot_link import find_slot, find_slot_link, retrieve_animation_data_holder
from .link_applier import prepare_all_data_blocks
from .util import blender_data_keys, blender_data_subkeys, is_any_action_valid, needs_migrate_2_0


__all__ = ["ToNLA", "ExportFBX", "FromNLA"]


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
	bl_label = "Setup NLA for Export"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return len(bpy.data.actions) > 0 and is_any_action_valid() and not needs_migrate_2_0()

	def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]]:
		return context.window_manager.invoke_confirm(self, event, title="Prepare NLA Export", message="This will clear all NLA data!\n\nBe sure to press \"Clear Scene ..including NLA\" after export.", icon="WARNING")

	def execute(self, context: bpy.types.Context) -> set:
		_setup_all_actions_to_nla()
		return {"FINISHED"}


class ExportFBX(bpy.types.Operator):
	"""Setup all slot link animations onto the NLA and open the FBX exporter with sane default settings"""
	bl_idname = "slot_link.export_fbx"
	bl_label = "Export FBX"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return len(bpy.data.actions) > 0 and is_any_action_valid() and not needs_migrate_2_0()

	def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]]:
		return context.window_manager.invoke_confirm(self, event, title="NLA to FBX Export", message="This will clear all NLA data!\n\nBe sure to press \"Clear Scene ..including NLA\" afterwards.", icon="WARNING")

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
			bake_anim_use_all_bones=False,
			bake_anim_use_nla_strips=True,
			bake_anim_use_all_actions=False,
			bake_anim_force_startend_keying=True,
		)


def _setup_slot_link_from_nla():
	for action in bpy.data.actions:
		action.slot_link.links.clear()

	def _setup_slot_link(thing):
		if(not hasattr(thing, "animation_data") or not thing.animation_data):
			return
		animdata: bpy.types.AnimData = thing.animation_data
		if(animdata.nla_tracks is None or len(animdata.nla_tracks) == 0):
			return
		for track in animdata.nla_tracks:
			for strip in track.strips:
				if(not strip.action or not strip.action_slot):
					continue
				slot_link = find_slot_link(strip.action, strip.action_slot_handle)
				if(not slot_link):
					slot_link = strip.action.slot_link.links.add()
					slot_link.slot_handle = strip.action_slot_handle

				match strip.action_slot.target_id_type:

					case "OBJECT":
						link_target = slot_link.targets.add()
						link_target.target = thing

					case "KEY":
						for blender_object in bpy.data.objects:
							if(blender_object.data == thing.user):
								link_target = slot_link.targets.add()
								link_target.target = blender_object

					# TODO other `target_id_type`s

					case _:
						print(f"Unsupported `target_id_type`: {strip.action_slot.target_id_type}")

	def _check_subkeys(thing):
		for sub_key in blender_data_subkeys:
			if(hasattr(thing, sub_key)):
				_setup_slot_link(getattr(thing, sub_key))

	for data_key in blender_data_keys:
		thing_type = getattr(bpy.data, data_key)
		for thing in thing_type:
			_setup_slot_link(thing)
			_check_subkeys(thing)


class FromNLA(bpy.types.Operator):
	"""Setup slot link animations from the NLA"""
	bl_idname = "slot_link.from_nla"
	bl_label = "Setup from NLA"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context: bpy.types.Context) -> bool:
		return len(bpy.data.actions) > 0 and is_any_action_valid() and not needs_migrate_2_0()

	def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]]:
		return context.window_manager.invoke_confirm(self, event, title="Setup Slot Link from NLA", message="This will overwrite all Slot Link data!", icon="WARNING")

	def execute(self, context: bpy.types.Context) -> set:
		_setup_slot_link_from_nla()
		return {"FINISHED"}


def register():
	bpy.utils.register_class(ToNLA)
	bpy.utils.register_class(ExportFBX)
	bpy.utils.register_class(FromNLA)

def unregister():
	bpy.utils.unregister_class(FromNLA)
	bpy.utils.unregister_class(ExportFBX)
	bpy.utils.unregister_class(ToNLA)
