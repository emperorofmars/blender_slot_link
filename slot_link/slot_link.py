import bpy


def _slot_link_poll(self, target_object: bpy.types.Object) -> bool:
	"""
	Super powered poll function.

	Determines if the `target_object` is suitable based on the SlotLinks Slots `target_id_type`.

	If relevant, also looks into the animation and figures out if the `target_object` is suitable, based on the animations fcurve data_paths.
	"""
	action: bpy.types.Action = self.id_data

	for slot in action.slots:
		if(slot.handle == self.slot_handle):
			break
	else:
		return False

	#import re

	match slot.target_id_type:
		case "OBJECT":
			# plz no
			for layer in action.layers:
				for strip in layer.strips: # pyright: ignore[reportAssignmentType]
					if(strip.type == "KEYFRAME"):
						strip: bpy.types.ActionKeyframeStrip = strip
						for channelbag in strip.channelbags:
							if(channelbag.slot_handle == slot.handle):
								for fcurve in channelbag.fcurves:
									if(fcurve.data_path.startswith("pose.")):
										if(type(target_object.data) is not bpy.types.Armature):
											return False

										# Too far? What if user deletes a bone from an animated armature? Calculate confidence based on the percentage of matched bones and use that as a cutoff? What if it animated only one bone??
										#if(match := re.search(r"^pose.bones\[\"(?P<bone_name>[\w. -:,]+)\"\]", fcurve.data_path)):
										#	if(match.groupdict()["bone_name"] not in target_object.data.bones):
										#		return False
			return True
		case "MATERIAL":
			if(target_object.material_slots and len(target_object.material_slots) > 0):
				return True
		case "NODETREE":
			if(target_object.material_slots and len(target_object.material_slots) > 0):
				return True
		case "KEY":
			if(target_object.data and type(target_object.data) is bpy.types.Mesh and target_object.data.shape_keys):
				return True
		case "ARMATURE":
			if(target_object.data and type(target_object.data) is bpy.types.Armature):
				return True
		case "CAMERA":
			if(target_object.data and type(target_object.data) is bpy.types.Camera):
				return True
		case "LIGHT":
			if(target_object.data and isinstance(target_object.data, bpy.types.Light)):
				return True
		# TODO support more eventually
	return False


class SlotLink(bpy.types.PropertyGroup):
	"""
	Links an Actions Slot to a target `bpy.types.Object`.

	If the Slot has a `target_id_type` of i.e. `KEY`, it means this link is targeting the skape-keys of a mesh that is instantiated on the `target` object.

	`datablock_index` is used in case the Slot has a `target_id_type` of `MATERIAL` for example. Then the index points to the instantiated meshes material index.
	"""
	slot_handle: bpy.props.IntProperty(name="Slot Handle", default=-1) # type: ignore
	target: bpy.props.PointerProperty(type=bpy.types.Object, name="Target", description="The Object this Slot should animate", poll=_slot_link_poll) # type: ignore
	datablock_index: bpy.props.IntProperty(name="Datablock Index", description="The index of the Material/Nodetree/etc..", default=0, min=0) # type: ignore


class ActionSlotLink(bpy.types.PropertyGroup):
	"""
	Redefine Blender Actions into full standalone animations.

	Holds a `SlotLink` object for each Slot of an Action.

	Additionally, it can indicate this "animation" to be a reset-animation.

	Or reference an "animation" that is set to be a reset-animation.
	If this is the case, when this "animation" is applied to the Scene, the reset-animation will be applied before, to put the Scene into a consistent state.
	"""
	is_reset_animation: bpy.props.BoolProperty(name="Is Reset-Animation", description="Use this Action to reset every property to a desired default state", default=False) # type: ignore
	reset_animation: bpy.props.PointerProperty(type=bpy.types.Action, name="Reset Animation", description="On 'Link Slots', the Reset Animation will be used to reset the state of the entire scene", poll=lambda self, action: bpy.context.active_action != action and action.slot_link.is_reset_animation, options=set()) # type: ignore
	links: bpy.props.CollectionProperty(type=SlotLink, name="Slot Links", options=set()) # type: ignore
	active_index: bpy.props.IntProperty(name="Active Slot Link", options=set()) # type: ignore


class AddSlotLink(bpy.types.Operator):
	"""Setup an animation target for this Action-Slot"""
	bl_idname = "slot_link.add"
	bl_label = "Setup Slot Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	slot_handle: bpy.props.IntProperty(default=-1) # type: ignore

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return context.active_action is not None

	def execute(self, context: bpy.types.Context) -> set:
		for link in context.active_action.slot_link.links:
			if(link.slot_handle == self.slot_handle):
				return {"CANCELLED"}
		slot_link = context.active_action.slot_link.links.add()
		slot_link.slot_handle = self.slot_handle
		return {"FINISHED"}


class RemoveSlotLink(bpy.types.Operator):
	"""Remove orphaned link"""
	bl_idname = "slot_link.remove"
	bl_label = "Remove Slot Link"
	bl_category = "anim"
	bl_options = {"REGISTER", "UNDO"}

	index: bpy.props.IntProperty(default=-1) # type: ignore

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return context.active_action is not None and len(context.active_action.slot_link.links) > 0

	def execute(self, context: bpy.types.Context) -> set:
		context.active_action.slot_link.links.remove(self.index)
		return {"FINISHED"}


def register():
	bpy.types.Action.slot_link = bpy.props.PointerProperty(type=ActionSlotLink, name="Slot Link", options=set()) # type: ignore

def unregister():
	if hasattr(bpy.types.Action, "slot_link"):
		del bpy.types.Action.slot_link
