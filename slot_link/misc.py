import bpy


class OpenDocumentation(bpy.types.Operator):
	"""Open the Slot Link documentation in a webbrowser"""
	bl_idname = "slot_link.open_documentation"
	bl_label = "Open Documentation"

	def execute(self, context: bpy.types.Context) -> set:
		import webbrowser
		webbrowser.open("https://docs.stfform.at/guide/blender/slot_link.html")
		return {"FINISHED"}
