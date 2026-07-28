import bpy

package_key: str


class SlotLinkPreferences:
	use_separate_editor: bool
	"""Move Slot Link editor to separate Panel"""

	hide_slot_link_list: bool
	"""Hide the list of Slot Links (Use the Slot Panel instead)"""

	hide_dopesheet_header_ui: bool
	"""Hide Dopesheet header GUI"""

	hide_documentation_link: bool
	"""Hide Documentation link"""


def get_preferences() -> SlotLinkPreferences:
	return bpy.context.preferences.addons[package_key].preferences
