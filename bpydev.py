#!/bin/python

"""
IDE/editor independent tooling for developing and debugging Blender extensions.

https://codeberg.org/emperorofmars/bpydev

Sets up your Blender extension into a local Blender extensions repository and launches Blender with it enabled.

Copy this script next your `blender_manifest.toml` and run.
Ideally add `bpydev.toml` to your `.gitignore`, so that different developers can have different configs.

Some premade configurations for editors like VSCode or Zed are in this repository.

Be sure to add this script and `bpydev.toml` to `paths_exclude_pattern` in your `blender_manifest.toml`
"""

BLENDER_BINARIES = ("/usr/bin/blender",) # todo platform switch
BLENDER_DEFAULT = "latest"
EXTENSIONS_REPOSITORY = "local_development"
PORT_UDP = 25398
PORT_DEBUGPY = 25399


import io
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class BpydevConfig:
	target_directory: str = "."
	blender_binaries: Sequence[str] = BLENDER_BINARIES
	default_version: str = BLENDER_DEFAULT
	extensions_repository: str = EXTENSIONS_REPOSITORY
	specified_version: str | None = None
	specified_binary: str | None = None
	port_udp: int = PORT_UDP
	port_debugpy: int = PORT_DEBUGPY

	def get_binaries(self) -> list[str]:
		ret = list(self.blender_binaries)
		if(self.specified_binary):
			ret.append(self.specified_binary)
		return ret


def init_config(override: bool = False):
	import os
	if(os.path.isfile("bpydev.toml") and not override):
		print("File 'bpydev.toml' already exists!\nRe-run this command with the --override flag.")
		exit(1)
	with open("bpydev.toml", "w") as bpydev_conf_file:
		binaries = "[\n\t\"" + "\",\n\t\"".join(BLENDER_BINARIES) + "\"\n]"
		bpydev_conf_file.write(f"""\
# Config for bpydev.py
# Ideally add `bpydev.toml` to your `.gitignore`, so that different developers can have different configs.

# Development directory (where your `blender_manifest.toml` is, default: `.`)
# target_directory: "."

# Paths of Blender binaries
blender_binaries = {binaries}

# The default Blender version to use. (default "{BLENDER_DEFAULT}")
default_version = "{BLENDER_DEFAULT}"

# The name of the Blender extension repository to use. (default: "{EXTENSIONS_REPOSITORY}")
extensions_repository = "{EXTENSIONS_REPOSITORY}"

# Port for communicating with the bpydev script
# port_udp: {PORT_UDP}

# Port for debugpy, use this port to connect with a debugpy client.
# port_debugpy: {PORT_DEBUGPY}
""")

def read_config() -> BpydevConfig:
	ret = BpydevConfig()
	try:
		with open("bpydev.toml", "r") as bpydev_conf_file:
			import tomllib
			bpydev_conf = tomllib.loads(bpydev_conf_file.read())
			if("target_directory" in bpydev_conf): ret.target_directory = bpydev_conf["target_directory"]
			if("blender_binaries" in bpydev_conf): ret.blender_binaries = bpydev_conf["blender_binaries"]
			if("default_version" in bpydev_conf): ret.default_version = bpydev_conf["default_version"]
			if("extensions_repository" in bpydev_conf): ret.extensions_repository = bpydev_conf["extensions_repository"]
			if("port_udp" in bpydev_conf): ret.port_udp = bpydev_conf["port_udp"]
			if("port_debugpy" in bpydev_conf): ret.port_debugpy = bpydev_conf["port_debugpy"]
	except:
		pass
	return ret


def try_determine_extensions_dir(blender_binary: str) -> str | None:
	"""Try to get the extensions directory of a Blender installation"""
	import subprocess, re, os
	extensions_dir_output = subprocess.run([blender_binary, "--disable-autoexec", "--factory-startup", "-b", "--python-expr", f"""\
import bpy
extensions_dir = bpy.utils.user_resource("EXTENSIONS", create=True)
print("BPYDEV_EXTENSIONS_DIR:" + str(extensions_dir) + "\\n")
"""], capture_output=True)
	if(extensions_dir_output.returncode == 0 and extensions_dir_output.stdout):
		if(match := re.search(r"BPYDEV_EXTENSIONS_DIR:(?P<extensions_dir>[\S]+)\n", extensions_dir_output.stdout.decode("utf-8"))):
			extensions_dir = match.groupdict()["extensions_dir"]
			if(os.path.isdir(extensions_dir)):
				return extensions_dir


def start_blender_with_extension(config: BpydevConfig, blender_binary: str, extension_id: str):
	"""Launch Blender with the development extension and reload it on file-system change"""
	extension_module = "bl_ext." + config.extensions_repository + "." + extension_id
	import subprocess, time
	print(f"Launching Blender: {blender_binary}")

	from watchdog.observers import Observer
	from watchdog.events import FileSystemEventHandler

	class PythonFileHandler(FileSystemEventHandler):
		def __init__(self):
			self.last_modified = time.time()
		def on_modified(self, event):
			import socket
			if((time.time() - self.last_modified) > 0.05 and not event.is_directory and event.src_path.endswith((".py", ".toml"))): # pyright: ignore[reportArgumentType]
				self.last_modified = time.time()
				print(f"Modified {event.src_path}")
				blender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				blender_socket.sendto("filesystem_update".encode(), ("localhost", config.port_udp))

	event_handler = PythonFileHandler()
	observer = Observer()
	try:
		observer.schedule(event_handler, path=config.target_directory, recursive=True)
		observer.start()

		subprocess.run([blender_binary, "--python-expr", f"""\
import bpy, sys, traceback, queue, threading
bpy.ops.extensions.repo_refresh_all()
bpy.ops.preferences.addon_refresh()
try:
	bpy.ops.preferences.addon_enable(module="{extension_module}")
	print("Addon {extension_module} enabled")
except Exception:
	traceback.print_exc()
	sys.exit(1)

import os, sys, subprocess, site, importlib
try:
	sys.path.append(site.getusersitepackages())
	if(not importlib.util.find_spec("debugpy")):
		python_runtime = os.path.abspath(sys.executable)
		subprocess.call([python_runtime, "-m", "ensurepip"])
		subprocess.call([python_runtime, "-m", "pip", "install", "debugpy"])
	debugpy = importlib.import_module("debugpy")
	debugpy.listen({config.port_debugpy})
	print("Debugpy is listening on port {config.port_debugpy}")
except Exception:
	traceback.print_exc()
	sys.exit(1)
finally:
	sys.path.remove(site.getusersitepackages())

server_event_queue = queue.Queue()

def listen_udp():
	import socket
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(("localhost", {config.port_udp}))
	print(f"Listening on UDP port {config.port_udp}")
	while True:
		try:
			data, addr = s.recvfrom(1024)
			match(data.decode()):
				case "filesystem_update":
					def filesystem_update():
						print("Reloading addon {extension_module}")
						try:
							bpy.ops.preferences.addon_disable(module="{extension_module}")
							bpy.ops.preferences.addon_enable(module="{extension_module}")
						except Exception:
							traceback.print_exc()
					server_event_queue.put(filesystem_update)
				case _: print("Unknown message:", message)
		except Exception as e:
			print("UDP error:", e)
threading.Thread(target=listen_udp, daemon=True).start()

def run():
	while(not server_event_queue.empty()):
		func = server_event_queue.get()
		try:
			func()
		except Exception:
			traceback.print_exc()
	return 0.1
bpy.app.timers.register(run, persistent=True)
"""], capture_output=False)
	finally:
		if(observer.is_alive()):
			observer.stop()


def check_target_dir(target_dir: str) -> bool:
	"""Check if the target directory exists and contains the Blender manifest."""
	import os
	if(not os.path.isdir(target_dir)):
		print(f"Invalid target directory: {target_dir}")
		return False
	if(not os.path.exists(os.path.join(target_dir, "blender_manifest.toml"))):
		print(f"Invalid target directory: {target_dir} (No 'blender_manifest.toml')")
		return False
	return True


def get_extension_id_from_manifest(target_dir: str) -> str | None:
	"""Get a Blender extensions ID from its manifest"""
	import os
	with open(os.path.join(target_dir, "blender_manifest.toml"), "r") as blender_manifest_file:
		import tomllib
		blender_manifest = tomllib.loads(blender_manifest_file.read())
		return blender_manifest.get("id")


def compare_version(a: str, b: str) -> int:
	va = [int(p) for p in a.split(".")]
	vb = [int(p) for p in b.split(".")]
	va.extend([0] * (len(vb) - len(va)))
	vb.extend([0] * (len(va) - len(vb)))
	for v1, v2 in zip(va, vb):
		if v1 < v2: return -1
		if v1 > v2: return 1
	return 0


def get_blender_binaries(blender_binaries: list[str], verbose: bool = False) -> tuple[list[tuple[str, str]], str | None]:
	"""Determine the versions of all valid Blender installations from the 'blender_binaries' argument"""
	import functools, subprocess, re
	versions: list[tuple[str, str]] = []
	latest: str | None = None
	for binary in blender_binaries:
		try:
			version_output = subprocess.run([binary, "-v"], capture_output=True)
			if(version_output.returncode == 0 and version_output.stdout):
				if(match := re.search(r"^Blender (?P<version>[0-9]+.[0-9]+.[0-9]+)", version_output.stdout.decode("utf-8"))):
					version = match.groupdict()["version"]
					if(compare_version(version, "4.4") < 0):
						if(verbose):
							print(f"Skipping too old version {version}")
						continue
					versions.append((version, binary))
					if(not latest or compare_version(version, latest) > 0):
						latest = version
		except Exception:
			print(f"Invalid Blender binary: {binary}")

	versions_sorted = sorted(versions, key=functools.cmp_to_key(lambda v1, v2: compare_version(v2[0], v1[0])))

	if(verbose):
		print("Available Blender versions:")
		for version, binary in versions_sorted:
			print(f" * {binary} ({version}){" [latest]" if version == latest else ""}")
		if(not len(versions_sorted) or not latest):
			print("None")

	return versions_sorted, latest


def determine_blender_binary(versions: list[tuple[str, str]], latest: str, blender_binary: str | None = None, blender_version: str | None = None) -> tuple[str, str]:
	"""Determine which Blender installation to use and its version"""
	import functools
	versions_sorted = sorted(versions, key=functools.cmp_to_key(lambda v1, v2: compare_version(v2[0], v1[0])))

	selected_version: str
	selected_binary: str
	if(blender_binary):
		for version, binary in versions_sorted:
			if(binary == blender_binary):
				selected_version = version
				selected_binary = binary
				break
		else:
			raise Exception(f"Invalid Blender binary: {blender_binary}")
	elif(blender_version and blender_version != "latest"):
		for version, binary in versions_sorted:
			if(version.startswith(blender_version)):
				selected_version = version
				selected_binary = binary
				break
		else:
			raise Exception(f"Invalid Blender version: {blender_version}")
	else:
		selected_version = latest
		for version, binary in versions_sorted:
			if(version == selected_version):
				selected_binary = binary
				break
		else:
			raise Exception("Invalid code path")

	return selected_binary, selected_version


def setup(config: BpydevConfig) -> tuple[str, str] | None:
	"""Sets up a local extension repository for a Blender installation"""
	if(not check_target_dir(config.target_directory)):
		return None
	versions, latest = get_blender_binaries(config.get_binaries(), True)
	if(not len(versions) or not latest):
		raise Exception("No available Blender binaries!")

	selected_binary, selected_version = determine_blender_binary(versions, latest, config.specified_binary, config.specified_version)
	print(f"Selected Blender binary:\n   {selected_binary} ({selected_version})")
	print()

	extensions_dir = try_determine_extensions_dir(selected_binary)
	if(not extensions_dir):
		raise Exception(f"Invalid Extensions Directory: {config.specified_version}")

	print(f"Extensions Directory:\n   {extensions_dir}")
	print()

	import os, subprocess, re
	repo_dir = os.path.join(extensions_dir, config.extensions_repository)

	list_repo_output = subprocess.run([selected_binary, "--command", "extension", "repo-list"], capture_output=True)
	if(list_repo_output.returncode == 0 and list_repo_output.stdout):
		if(match := re.search(rf"{config.extensions_repository}\:\n    name: \"{config.extensions_repository}\"\n    directory: \"{repo_dir}\"\n    source: \"USER\"", list_repo_output.stdout.decode("utf-8"))):
			print(f"Repository {config.extensions_repository} is already installed")
		else:
			print(f"Adding repository {config.extensions_repository}")

			install_repo = subprocess.run([selected_binary, "--command", "extension", "repo-add", config.extensions_repository, "--name", config.extensions_repository, "--source", "USER"], capture_output=True)
			if(install_repo.returncode == 0 ):
				print(f"Successfully added {config.extensions_repository}")
			else:
				raise Exception(f"Failed to add {config.extensions_repository}")
	else:
		raise Exception("Failed to fetch extension repositories")

	extension_id = get_extension_id_from_manifest(config.target_directory)
	if(not extension_id):
		raise Exception("Failed to load extension manifest")

	if(not os.path.exists(repo_dir)):
		os.mkdir(repo_dir)
	if(not os.path.exists(repo_dir)):
		raise Exception(f"Failed to create repository directory {repo_dir}!")

	for path in os.listdir(repo_dir):
		path_full = os.path.join(repo_dir, path)
		if(os.path.islink(path_full) and os.path.realpath(path_full) == os.path.abspath(config.target_directory)):
			os.remove(path_full)

	extension_target = os.path.join(repo_dir, extension_id)
	if(os.path.exists(extension_target)):
		if(os.path.islink(extension_target)):
			os.remove(extension_target)
		else:
			print(f"Extension {extension_id} exists and is not a symlink!\nIt will not be removed, please handle it manually.")
			return None

	import sys
	if sys.platform == "win32":
		import _winapi
		_winapi.CreateJunction(os.path.abspath(config.target_directory), extension_target)
	else:
		os.symlink(os.path.abspath(config.target_directory), extension_target, target_is_directory=True)

	if(os.path.islink(extension_target)):
		print(f"Successfully installed {extension_id}!")
		return selected_binary, extension_id
	else:
		raise Exception(f"Failed to install {extension_id}!")


def build_blender_package(blender_manifest: str, package_buffer: io.BytesIO):
	"""
	Builds a Blender extension .zip package from blender_manifest.toml.

	Easy to use from the commandline, and more importantly, easily usable in a git-ops action.
	"""
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
	import argparse
	parser = argparse.ArgumentParser(description="Blender extension development tooling")
	parser.epilog = "View source & report issues: https://codeberg.org/emperorofmars/bpydev"
	subparsers = parser.add_subparsers(title="commands", dest="command", help="Add -h to print help for a subcommand. (e.g. 'setup -h')")

	init_config_parser = subparsers.add_parser("init-config", aliases=["ic"], usage="init-config", help="Create a configuration file.")
	list_parser = subparsers.add_parser("list", aliases=["ll"], usage="list", help="List available Blender installations.")
	setup_parser = subparsers.add_parser("setup", aliases=["s"], usage="setup .", help="Install an extension for development in Blender.")
	launch_parser = subparsers.add_parser("launch", aliases=["l"], usage="launch .", help="Launch Blender with an extension for development and listen for a debugpy client.", description="Launch Blender with an extension for development and listen for a debugpy client.")
	package_parser = subparsers.add_parser("package", aliases=["p"], usage="package .", help="Create a Blender extension .zip from its manifest")

	def add_subparser_args(parser: argparse.ArgumentParser):
		parser.add_argument("target_directory", nargs="?", type=str, help="Install the specified directory as an extension in Blender. (The directory must contain a 'blender_manifest.toml')", default=".")
		target_group = parser.add_mutually_exclusive_group(required=False)
		target_group.add_argument("-b", "--blender-binary", type=str, help="Specify a Blender executable (e.g. '/usr/bin/blender')")
		target_group.add_argument("-bv", "--blender-version", type=str, help="Specify a Blender version (e.g. 'latest', '5.1', '4.5.1')")
		parser.add_argument("-r", "--ext-repo", type=str, help=f"Extension repository module (e.g. '{EXTENSIONS_REPOSITORY}')", default=EXTENSIONS_REPOSITORY)
	add_subparser_args(setup_parser)
	add_subparser_args(launch_parser)

	init_config_parser.add_argument("-o", "--override", action="store_true", help="Override an already existing config")
	list_parser.add_argument("-b", "--blender-binary", type=str, help="Select the target Blender executable (e.g. '/usr/bin/blender')")

	package_parser.add_argument("target_directory", nargs="?", type=str, help="Install the specified directory as an extension in Blender. (The directory must contain a 'blender_manifest.toml')", default=".")
	package_parser.add_argument("-o", "--output-dir", help="Directory where to place the .zip", default=".")

	args = parser.parse_args()

	config = read_config()
	if("blender_binary" in args): config.specified_binary = args.blender_binary
	if("blender_version" in args): config.specified_version = args.blender_version
	if("target_directory" in args): config.target_directory = args.target_directory

	match(args.command):
		case "init-config" | "ic":
			init_config(args.override)
		case "list" | "ll":
			get_blender_binaries(config.get_binaries(), True)
		case "setup" | "s":
			if(not setup(config)):
				exit(1)
		case "launch" | "l":
			if(ret := setup(config)):
				start_blender_with_extension(config, ret[0], ret[1])
			else:
				exit(1)
		case "package" | "p":
			import os
			with open(os.path.join(config.target_directory, "blender_manifest.toml"), "r") as blender_manifest:
				manifest = blender_manifest.read()
				with open(os.path.join(args.output_dir, package_name_from_manifest(manifest)), "wb") as package:
					build_blender_package(manifest, package) # pyright: ignore[reportArgumentType]
		case _:
			print("Invalid Command")
			parser.print_usage()
			exit(1)
