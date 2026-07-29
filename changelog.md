# Changelog

## v0.2.0
* Added support for linking multiple targets per SlotLink.
* Due to the changed data-model, implemented an operator to migrate existing animations.\
	It will have to be executed once, before working with SlotLink when SlotLink data already existed.\
	No data gets lost, all will work as before.
* The initial setup for a SlotLink now tries to determine the target automatically.
* "KEY" slots now support linking lattices.

## v0.1.5
* Fixed a bug where a Slot of type NODETREE would not be recognized as correctly linked, even if it was.

## v0.1.4
* Detects if a Slot is linked an additional time somewhere where it shouldn't be.

## v0.1.3
* Preserves the current frame when linking slots.

## v0.1.2
* The Slot Link list displays for material-slots the material name instead of its index
* Added warning if the same target is selected by multiple slots

## v0.1.1
* Fixed a correctly linked Action being detected as unlinked when it contained material slots
* The Material index, if relevant, is now displayed in the slot-link list

## v0.1.0
* Added options to the extensions preferences to set how and where the GUI is drawn.
* The Slot Link editor is by default drawn as part of the Action panel.
	* This can be reverted to a separate panel in the preferences.
* The Dopesheet views top bar now shows the Link Slots button.
	* This can be reverted to a separate panel in the preferences.
* Improved the logic that determines if an Action is linked correctly.
* Improved the Slots target selector to show less irrelevant options.
* Smaller GUI refinements, like coloring the link-button if the Action is not linked.
