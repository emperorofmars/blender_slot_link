import bpy


__all__ = ["SlotLinkTarget", "SlotLink", "ActionSlotLink", "find_slot", "find_slot_link", "retrieve_animation_data_holder", "poll_slot_link_target"]


def poll_slot_link_target(slot_link_target, target_object: bpy.types.Object) -> bool:
	"""
	Super powered poll function!

	Determines if the `target_object` is suitable based on the slots `target_id_type`.
	* The `target_object` must be part of the target collection of the action, if it is set.
	* If relevant, also looks into the animation itself and figures out if the `target_object` is suitable based on the animations fcurve data_paths.

	:param SlotLinkTarget slot_link_target: The target to poll for
	:param bpy.types.Object target_object: The Object to check
	:returns bool: True if the Object can be used as the slot_link_targets `target`.
	"""
	action: bpy.types.Action = slot_link_target.id_data
	slot_link = slot_link_target.rna_ancestors()[2]

	if(action.slot_link.target_collection and target_object not in action.slot_link.target_collection.all_objects.values()):
		return False

	slot = find_slot(action, slot_link.slot_handle)
	if(not slot):
		return False

	anim_data_holder = retrieve_animation_data_holder(slot.target_id_type, target_object, 0)
	if(anim_data_holder):
		match slot.target_id_type: # For cases where more logic is needed
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
			case _:
				return True
	return False


class SlotLinkTarget(bpy.types.PropertyGroup):
	"""
	Links an Actions Slot to a target `bpy.types.Object`.

	If the Slot has a `target_id_type` of i.e. `KEY`, it means this link is targeting the shape-keys of a mesh that is instantiated on that objects `data`.

	`datablock_index` is used in case the Slot has a `target_id_type` of `MATERIAL` for example. In that case the `datablock_index` is the instantiated meshes material-slot index.
	"""
	target: bpy.props.PointerProperty(type=bpy.types.Object, name="Target", description="The Object this Slot should animate", poll=poll_slot_link_target, options=set())
	datablock_index: bpy.props.IntProperty(name="Datablock Index", description="The index of the Material/Nodetree/etc..", default=0, min=0, options=set())


class SlotLink(bpy.types.PropertyGroup):
	"""
	Links an ActionSlot to a set of animation targets.
	"""
	slot_handle: bpy.props.IntProperty(name="Slot Handle", default=-1, options=set())
	targets: bpy.props.CollectionProperty(type=SlotLinkTarget, name="Targets", description="The Objects this Slot should animate", options=set())

	### TODO remove legacy data-model by 2027-08-01
	target: bpy.props.PointerProperty(type=bpy.types.Object, name="Target", description="Legacy, please migrate!", poll=poll_slot_link_target)
	datablock_index: bpy.props.IntProperty(name="Datablock Index", description="Legacy, please migrate!", default=0, min=0)


def _poll_reset_animation(self, animation: bpy.types.Action) -> bool:
	return self.id_data != animation and animation.slot_link.is_reset_animation and (not self.target_collection or not animation.slot_link.target_collection or self.target_collection == animation.slot_link.target_collection)

class ActionSlotLink(bpy.types.PropertyGroup):
	"""
	Redefine Blender Actions into full standalone animations.

	Holds a `SlotLink` object for each Slot of its Action.

	If a `target_collection` is specified, this "animation" will only affect Objects part of it and their instantiated resources.

	Additionally, it can indicate this "animation" to be a reset-animation.

	Or reference an "animation" that is set to be a reset-animation.
	If this is the case, when this "animation" is applied to the Scene, the reset-animation will be applied before, to put the Scene into a consistent state.
	"""
	links: bpy.props.CollectionProperty(type=SlotLink, name="Slot Links", options=set())
	active_index: bpy.props.IntProperty(name="Active Slot Link", options=set())

	target_collection: bpy.props.PointerProperty(type=bpy.types.Collection, name="Target Collection", description="Only link Objects within this Collection. Animation data from other collections will not be touched or reset. If no Collection is specified, the entire scene will be reset and linked.", options=set())

	is_reset_animation: bpy.props.BoolProperty(name="Is Reset-Animation", description="Use this Action to reset every property to a desired default state", default=False, options=set())
	reset_animation: bpy.props.PointerProperty(type=bpy.types.Action, name="Reset Animation", description="On 'Link Slots', the reset-animation will be used to reset the state of the entire scene", poll=_poll_reset_animation, options=set())


def find_slot(action: bpy.types.Action, slot_handle: int) -> bpy.types.ActionSlot | None:
	"""Find the ActionSlot on an Action based on a SlotLinks slot handle"""
	for slot in action.slots:
		if(slot.handle == slot_handle):
			return slot
	return None

def find_slot_link(action: bpy.types.Action, slot_handle: int) -> SlotLink | None:
	"""Find the SlotLink on an Action based on a Slots handle"""
	for slot_link in action.slot_link.links:
		if(slot_link.slot_handle == slot_handle):
			return slot_link
	return None


def retrieve_animation_data_holder(target_id_type: str, target_object: bpy.types.Object, datablock_index: int = 0) -> bpy.types.ID | None:
	"""
	Retrieve the property that holds the `animation_data` relative to the `target_object`, based on the `target_id_type` and `data_block_index`.

	Examples for different `target_id_type` values:
	* "OBJECT": simply returns the `target_object`.
	* "KEY": returns `target_object.data.shape_keys`, if valid.
	* "MATERIAL": returns the material from the material_slot at the `datablock_index`, if valid.

	:param str target_id_type: The `target_id_type` of an `ActionSlot`.
	:param bpy.types.Object target_object: The object from which to retrieve the correct `animation_data` holder for.
	:param int datablock_index: In case the target_id_type is "MATERIAL" or "NODETREE", retrieve the appropriate material or its node_tree.
	:returns bpy.types.ID | None: The property that has the desired `animation_data` property.
	"""
	if(not target_object): # Just in case
		return False
	match(target_id_type):
		case "OBJECT":
			return target_object

		case "MATERIAL":
			if(target_object.material_slots and len(target_object.material_slots) > datablock_index):
				target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[datablock_index]
				if(target_material_slot.material):
					return target_material_slot.material

		case "NODETREE":
			if(target_object.material_slots and len(target_object.material_slots) > datablock_index):
				target_material_slot: bpy.types.MaterialSlot = target_object.material_slots[datablock_index]
				if(target_material_slot.material and target_material_slot.material.node_tree):
					return target_material_slot.material.node_tree

		case "KEY":
			if(target_object.data and hasattr(target_object.data, "shape_keys") and target_object.data.shape_keys):
				for type_candidate in [bpy.types.Mesh, bpy.types.Curve, bpy.types.Lattice]:
					if(isinstance(target_object.data, type_candidate)):
						return target_object.data.shape_keys

		case "ARMATURE":
			if(target_object.data and type(target_object.data) is bpy.types.Armature):
				return target_object.data

		case "CAMERA":
			if(target_object.data and type(target_object.data) is bpy.types.Camera):
				return target_object.data

		case "LIGHT":
			if(target_object.data and isinstance(target_object.data, bpy.types.Light)):
				return target_object.data

		# TODO support more eventually

		case _:
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
