import sys
from ast import literal_eval
from pathlib import Path

import typer
from rich import print

from ftl import files as fs
from ftl import path
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

    if key.startswith("rule"):
        top_level_settings = [
            s for s in list(Settings.__annotations__.keys()) if not s.startswith("rule")
        ]
        print(
            "Settings Rules from the CLI is unsupported.\n"
            "Use [bold]'ftl editor'[/bold] instead.\n\n"
        )
        print("The following settings can be set from the CLI:")
        print(top_level_settings)
        raise typer.Exit(code=1)

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

    defaults = default_settings()
    save_settings(defaults)

    print("Reset to defaults...")
    print(defaults)


@cli.command()
def settings():
    """Show current settings..."""
    from ftl.rules import unstructure

    settings = get_settings()
    print(unstructure(settings))


@cli.command()
def editor():
    """Launch the Settings Editor..."""

    print("Launching Settings...")
    from ftl.ui.editor import RuleEditor

    RuleEditor.show()


@cli.command()
def encode(
    folder: Path = Path("."),
    recursive: bool = False,
    max_depth: int = 2,
    dry: bool = False,
):
    """Encode a folder of sequences."""

    from ftl.files import ls
    from ftl.runner import Runner
    from ftl.settings import get_rules
    from ftl.ui.progress import ProgressDialog

    runner = Runner(
        rules=get_rules(),
        files=ls(folder, max_depth=(1, max_depth)[recursive]),
    )
    ProgressDialog.from_runner(runner)
    runner.run(dry=dry)

    print("Artifacts...")
    artifacts = []
    for artifact in runner.artifacts:
        # Check if artifact actually exists
        # Any artifact can implement exists to support this check.
        if not artifact or (hasattr(artifact, "exists") and not artifact.exists()):
            continue

        # Artifacts may support a format method.
        if hasattr(artifact, "format"):
            artifacts.append(artifact.format())
        elif isinstance(artifact, Path):
            artifacts.append(artifact.as_posix())
        else:
            artifacts.append(str(artifact))
    print(artifacts)


@cli.command()
def ls(folder: Path = Path("."), recursive: bool = False, max_depth: int = 2):
    """List sequences in a folder."""

    max_depth = (1, max_depth)[recursive]
    for f in fs.ls(folder, max_depth):
        text = f.format(relative_to=folder)
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

    from ftl import tools

    # Get ffmpeg info
    ffmpeg_version = "N/A"
    try:
        ffmpeg_executable = tools.get_ffmpeg().replace("\\", "/")
        ffmpeg_version = tools.get_ffmpeg_version()
    except FileNotFoundError:
        ffmpeg_executable = "FFMPEG not found..."

    # Get OCIO / OIIO info
    ocio_config = tools.get_ocio_config_name()
    oiio_version = tools.get_oiio_version()

    version_info = {
        "python": sys.version,
        "ftl": version("ftl"),
        "ftl_package": path.as_posix(),
        "dearpygui": version("dearpygui"),
        "ffmpeg": ffmpeg_version,
        "ffmpeg_exe": ffmpeg_executable,
        "ocio_config": ocio_config,
        "oiio_version": oiio_version,
    }
    print(version_info)


if __name__ == "__main__":
    cli()
