import bpy


class OpenDocumentation(bpy.types.Operator):
	"""Open the Slot Link Documentation in Webbrowser"""
	bl_idname = "slot_link.open_documentation"
	bl_label = "Open Documentation"

	def execute(self, context):
		import webbrowser
		webbrowser.open("https://docs.stfform.at/guide/blender/slot_link.html")
		return {"FINISHED"}
