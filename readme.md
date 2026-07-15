# Blender Slot Link
**Slot Link helps you manage Blender projects with multiple separate animations.**

Blender supports only one animation per .blend file.\
Actions are modular pieces from which the one animation is composed of.

**Slot Link redefines Actions to be full standalone animations.**\
To achieve that, you have to set the animation target for each Slot of an Action.

Press the `Link Slots` button to play and edit an animation.\
Easily switch between animations with only one additional button press.

*Requires Blender 4.5 or higher. Not compatible with legacy Actions.*

🌰 **[Installation](https://extensions.blender.org/add-ons/slot-link/)** 🌰 **[User Guide](https://docs.stfform.at/guide/blender/slot_link.html)** 🌰 **[Report Issues](https://codeberg.org/emperorofmars/blender_slot_link/issues)**

![Screenshot of the Slot Link editor. This GUI allows specifying the targeted Objects of the Slots of a Blender Action.](docs/img/slot_link_editor.png)

> [!NOTE]
> Slot Link purposely allows only selecting Objects as targets.
>
> If you animated a Mesh's Shape Keys, simply select the Object on which that Mesh is instantiated.
>
> This has the added advantage of being able to animate multiple instances of the same Mesh separately.

Please open issues for any bugs or misbehavior you notice. Feel free to open issues for feature requests.

## Development Setup
* Have an up to date version of Blender installed.
* Either:
	* Use `bpydev.py` included in this repository.
	* Use VSCode with the [recommended extensions](./.vscode/extensions.json).\
		The most important one is [Blender VS Code](https://github.com/JacquesLucke/blender_vscode).
* Create a Python 3.13 venv in the repo directory.
* Inside the venv run:
	``` sh
	pip install -r requirements.txt
	```

## Contributing
Human made contributions via pull-requests are very welcome.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License
All source-code in this repository, except when noted in individual files and/or directories, is licensed under either:

* MIT License (LICENSE-MIT or <http://opensource.org/licenses/MIT>)
* Apache License, Version 2.0 (LICENSE-APACHE2 or <http://www.apache.org/licenses/LICENSE-2.0>)
* GNU General Public License v3.0 or later (LICENSE-GPL3+ or <https://www.gnu.org/licenses/gpl-2.0-standalone.html>)


<!--
**Build the extension**

Install dependencies (preferably into a venv):
``` sh
pip install -r requirements.txt
```

Build the extension:
``` python
python bpydev.py package -o packages
```
-->
