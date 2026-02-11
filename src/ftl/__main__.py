import os
import sys
from ast import literal_eval
from pathlib import Path

import typer
from rich import print

from ftl import tasks
from ftl.settings import Settings, default_settings, get_settings, save_settings


def safe_eval(expr):
    """Try to evaluate an expression as a Python object.

    We handle a couple of edge cases to ensure users
    don't need to escape strings in weird ways.
    """

    try:
        return literal_eval(expr)
    except ValueError as e:
        # If we get malformed node or string
        # the user passed in a string but
        # didn't escape it.
        if "malformed node or string" not in str(e):
            raise typer.Exit(code=1)
    except SyntaxError:
        # If expr starts with . or /
        # the user was probably passing in a file path
        if expr[0] not in (".", "/"):
            raise
    return expr


cli = typer.Typer()


@cli.command("set")
def _set(key: str, value: str):
    """Set the value of a Setting..."""

    value = safe_eval(value)

    key_type = Settings.__annotations__.get(key)
    if key_type is None:
        print(f"{key!r} is not a valid Setting...")
        raise typer.Exit(code=1)

    if not isinstance(value, key_type):
        if key_type is bool:
            expected = "True/False"
        else:
            expected = key_type.__name__
        print(f"{key!r} expected {expected!r}, got {value!r}...")
        raise typer.Exit(code=1)

    settings = get_settings()
    settings[key] = value
    save_settings(settings)
    print(f"Saved {key!r} as {value!r}")


@cli.command()
def reset():
    """Reset to defaults..."""

    save_settings(default_settings())
    print("Reset to defaults...")
    print(default_settings())


@cli.command()
def settings():
    """Show current settings..."""

    print(get_settings())


@cli.command()
def editor():
    """Launch the Settings Editor..."""

    print("Launching Settings...")
    from ftl.ui import SettingsEditor

    SettingsEditor.show()


@cli.command()
def encode(folder: Path = Path("."), recursive: bool = False, max_depth: int = 2):
    """Encode a folder of sequences."""

    from ftl import ui

    results = []
    if not recursive:
        task = tasks.EncodeFolder(folder, get_settings())

        # Show progress dialog...
        ui.TaskProgressDialog.from_tasks([task])

        task()
        results.extend(task.result)

    else:
        folders = set()
        for root, subdirs, _ in os.walk(folder, topdown=True):
            if str(Path(root).relative_to(folder)).count(os.sep) >= max_depth:
                subdirs[:] = []
            folders |= set([seq.path.parent for seq in tasks.get_sequences(Path(root))])

        task_group = []
        for i, folder in enumerate(folders):
            print(f"Encode Folder {i + 1} of {len(folders)}")
            task = tasks.EncodeFolder(folder, get_settings())
            task_group.append(task)

        # Show progress dialog...
        ui.TaskProgressDialog.from_tasks(task_group)

        for task in task_group:
            task()
            results.extend(task.result)

    print("Artifacts...")
    print([r.as_posix() for r in results])


@cli.command()
def ls(folder: Path = Path("."), recursive: bool = False):
    """List sequences in a folder."""

    if not recursive:
        sequences = tasks.get_sequences(folder)
    else:
        sequences = []
        for root, _, _ in os.walk(folder):
            sequences.extend(tasks.get_sequences(Path(root)))

    for sequence in sorted(sequences, key=lambda s: s.path.as_posix()):
        text = sequence.format(relative_to=folder)
        print(text.replace("missing", "[red]missing[/red]"))


@cli.command()
def install():
    """Install system-wide context menu commands..."""

    if sys.platform == "win32":
        from ftl._win import install

        install()

    if sys.platform == "darwin":
        raise RuntimeError("Context Menu commands not supported for MacOS yet...")

    if sys.platform == "linux":
        raise RuntimeError("Context Menu commands not supported for Linux yet...")


@cli.command()
def uninstall():
    """Uninstall system-wide context menu commands..."""

    if sys.platform == "win32":
        from ftl._win import uninstall

        uninstall()

    if sys.platform == "darwin":
        raise RuntimeError("Context Menu commands not supported for MacOS yet...")

    if sys.platform == "linux":
        raise RuntimeError("Context Menu commands not supported for Linux yet...")


@cli.command()
def version():
    """List version and key dependencies."""

    from importlib.metadata import version

    from ftl import tasks

    # Get ffmpeg info
    ffmpeg_version = "N/A"
    try:
        ffmpeg_executable = tasks.get_ffmpeg().replace("\\", "/")
        ffmpeg_version = tasks.get_ffmpeg_version()
    except Exception:
        ffmpeg_executable = "FFMPEG not found..."

    version_info = {
        "python": sys.version,
        "ftl": version("ftl"),
        "dearpygui": version("dearpygui"),
        "ffmpeg": ffmpeg_version,
        "ffmpeg_exe": ffmpeg_executable,
    }
    print(version_info)


if __name__ == "__main__":
    cli()
