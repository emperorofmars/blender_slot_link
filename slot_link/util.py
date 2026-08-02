import bpy


types_with_key = [bpy.types.Mesh, bpy.types.Curve, bpy.types.Lattice]

def has_shapekeys(blender_object: bpy.types.Object) -> bool:
	"""Check if the resource instantiated on this object supports shapekey animation"""
	if(blender_object.data and hasattr(blender_object.data, "shape_keys") and blender_object.data.shape_keys):
		for type_candidate in types_with_key:
			if(isinstance(blender_object.data, type_candidate)):
				return True
	return True
