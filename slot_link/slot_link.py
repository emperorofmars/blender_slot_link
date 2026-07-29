import bpy


__all__ = ["SlotLink", "ActionSlotLink", "find_slot_link", "slot_link_poll"]


def slot_link_poll(link_target, target_object: bpy.types.Object) -> bool:
	"""
	Super powered poll function!

	Determines if the `target_object` is suitable based on the SlotLinks Slots `target_id_type`.

	If relevant, also looks into the animation and figures out if the `target_object` is suitable, based on the animations fcurve data_paths.

	:param SlotLinkTarget link_target: The slot_link target to poll for
	:param bpy.types.Object target_object: The Object to check
	:returns bool: True if the Object can be used as the `link_targets` `target`.
	"""
	action: bpy.types.Action = link_target.id_data
	slot_link = link_target.rna_ancestors()[2]

	for slot in action.slots:
		if(slot.handle == slot_link.slot_handle):
			break
	else:
		return False

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
			return True
		case "MATERIAL":
			if(target_object.material_slots and len(target_object.material_slots) > 0):
				return True
		case "NODETREE":
			if(target_object.material_slots and len(target_object.material_slots) > 0):
				return True
		case "KEY":
			if(target_object.data and type(target_object.data) in [bpy.types.Mesh, bpy.types.Lattice] and target_object.data.shape_keys):
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


class SlotLinkTarget(bpy.types.PropertyGroup):
	"""
	Links an Actions Slot to a target `bpy.types.Object`.

	If the Slot has a `target_id_type` of i.e. `KEY`, it means this link is targeting the shape-keys of a mesh that is instantiated on that objects `data`.

	`datablock_index` is used in case the Slot has a `target_id_type` of `MATERIAL` for example. Then the index points to the instantiated meshes material-slot index.
	"""
	target: bpy.props.PointerProperty(type=bpy.types.Object, name="Target", description="The Object this Slot should animate", poll=slot_link_poll)
	datablock_index: bpy.props.IntProperty(name="Datablock Index", description="The index of the Material/Nodetree/etc..", default=0, min=0)


class SlotLink(bpy.types.PropertyGroup):
	"""
	Links an Actions Slot to a set of targets.
	"""
	slot_handle: bpy.props.IntProperty(name="Slot Handle", default=-1)
	targets: bpy.props.CollectionProperty(type=SlotLinkTarget, name="Targets", description="The Objects this Slot should animate")

	### TODO remove legacy data-model by 2027-08-01
	target: bpy.props.PointerProperty(type=bpy.types.Object, name="Target", description="Legacy, please migrate!", poll=slot_link_poll)
	datablock_index: bpy.props.IntProperty(name="Datablock Index", description="Legacy, please migrate!", default=0, min=0)


class ActionSlotLink(bpy.types.PropertyGroup):
	"""
	Redefine Blender Actions into full standalone animations.

	Holds a `SlotLink` object for each Slot of an Action.

	Additionally, it can indicate this "animation" to be a reset-animation.

	Or reference an "animation" that is set to be a reset-animation.
	If this is the case, when this "animation" is applied to the Scene, the reset-animation will be applied before, to put the Scene into a consistent state.
	"""
	links: bpy.props.CollectionProperty(type=SlotLink, name="Slot Links", options=set())
	active_index: bpy.props.IntProperty(name="Active Slot Link", options=set())

	is_reset_animation: bpy.props.BoolProperty(name="Is Reset-Animation", description="Use this Action to reset every property to a desired default state", default=False)
	reset_animation: bpy.props.PointerProperty(type=bpy.types.Action, name="Reset Animation", description="On 'Link Slots', the reset-animation will be used to reset the state of the entire scene", poll=lambda self, action: bpy.context.active_action != action and action.slot_link.is_reset_animation, options=set())


def find_slot_link(action: bpy.types.Action, slot_handle: int) -> SlotLink | None:
	"""Find the SlotLink on an Action based on a Slots handle"""
	for slot_link in action.slot_link.links:
		if(slot_link.slot_handle == slot_handle):
			return slot_link
	return None


def register():
	bpy.utils.register_class(SlotLinkTarget)
	bpy.utils.register_class(SlotLink)
	bpy.utils.register_class(ActionSlotLink)

	bpy.types.Action.slot_link = bpy.props.PointerProperty(type=ActionSlotLink, name="Slot Link", options=set())

def unregister():
	if hasattr(bpy.types.Action, "slot_link"):
		del bpy.types.Action.slot_link

	bpy.utils.unregister_class(ActionSlotLink)
	bpy.utils.unregister_class(SlotLink)
	bpy.utils.unregister_class(SlotLinkTarget)
