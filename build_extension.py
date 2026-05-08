"""
Builds a Blender extension .zip package from blender_manifest.toml.

Easy to use from the commandline, and more importantly, easily usable in a git-ops action.
"""

import io

def build_blender_package(blender_manifest: str, package_buffer: io.BytesIO):
		import tomllib
		manifest = tomllib.loads(blender_manifest)
		path_exclude_patterns: list[str] = manifest.get("build", {}).get("paths_exclude_pattern", [])
		path_exclude_patterns.append("__pycache__/")
		path_exclude_patterns.append("/.git/")
		path_exclude_patterns.append("/*.zip")

		from pathspec import GitIgnoreSpec
		spec = GitIgnoreSpec.from_lines(path_exclude_patterns)
		files_to_add = set(spec.match_tree_files(".", negate=True))

		import zipfile
		with zipfile.ZipFile(package_buffer, mode="w") as package:
			for file in files_to_add:
				package.write(file)


def package_name_from_manifest(blender_manifest: str) -> str:
		import tomllib
		manifest = tomllib.loads(blender_manifest)
		return manifest.get("id", "error") + "-" + manifest.get("version", "") + ".zip"


if(__name__ == "__main__"):
	import argparse, os
	parser = argparse.ArgumentParser(description="Create a Blender extension .zip from its manifest")
	parser.add_argument("-o", "--output-dir", help="Directory where to place the .zip", default=".")
	args = parser.parse_args()

	with open("blender_manifest.toml", "r") as blender_manifest:
		manifest = blender_manifest.read()
		with open(os.path.join(args.output_dir, package_name_from_manifest(manifest)), "wb") as package:
			build_blender_package(manifest, package) # pyright: ignore[reportArgumentType]
