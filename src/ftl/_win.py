import sys
import winreg
from pathlib import Path

LIB_DIR = Path(__file__).parent
ICON_FILE = LIB_DIR / "resources/ftl.ico"
ENCODE_ICON_FILE = LIB_DIR / "resources/encode.ico"
SETTINGS_ICON_FILE = LIB_DIR / "resources/settings.ico"


def install():
    """Add Windows explorer context menu entries."""

    exe = Path(sys.executable)
    if exe.stem == "python":
        exe = exe.parent / "pythonw.exe"

    # fmt: off
    # Build Context Menu
    menu_path = r"Directory\ContextMenus\FTL.menu"
    menu_key = winreg.CreateKeyEx(winreg.HKEY_CLASSES_ROOT, menu_path, 0, winreg.KEY_WRITE)

    verb_key = winreg.CreateKeyEx(menu_key, r"shell\FTL.settings", 0, winreg.KEY_WRITE)
    winreg.SetValueEx(verb_key, "MUIVerb", 0, winreg.REG_SZ, "Open Settings")
    winreg.SetValueEx(verb_key, "Icon", 0, winreg.REG_SZ, str(SETTINGS_ICON_FILE))
    cmd_key = winreg.CreateKeyEx(verb_key, r"command", 0, winreg.KEY_WRITE)
    winreg.SetValueEx(cmd_key, None, 0, winreg.REG_SZ, rf'{exe} -m ftl editor')

    verb_key = winreg.CreateKeyEx(menu_key, r"shell\FTL.encode", 0, winreg.KEY_WRITE)
    winreg.SetValueEx(verb_key, "MUIVerb", 0, winreg.REG_SZ, "Encode Folder")
    winreg.SetValueEx(verb_key, "Icon", 0, winreg.REG_SZ, str(ENCODE_ICON_FILE))
    cmd_key = winreg.CreateKeyEx(verb_key, r"command", 0, winreg.KEY_WRITE)
    winreg.SetValueEx(cmd_key, None, 0, winreg.REG_SZ, rf'{exe} -i -m ftl encode --folder="%V"')

    verb_key = winreg.CreateKeyEx(menu_key, r"shell\FTL.encode.recursive", 0, winreg.KEY_WRITE)
    winreg.SetValueEx(verb_key, "MUIVerb", 0, winreg.REG_SZ, "Encode Folder - Recusrive")
    winreg.SetValueEx(verb_key, "Icon", 0, winreg.REG_SZ, str(ENCODE_ICON_FILE))
    cmd_key = winreg.CreateKeyEx(verb_key, r"command", 0, winreg.KEY_WRITE)
    winreg.SetValueEx(cmd_key, None, 0, winreg.REG_SZ, rf'{exe} -i -m ftl encode --folder="%V" --recursive --max-depth=2')

    # Directory: Set ExtendedSubCommandsKey to menu_path
    key = winreg.CreateKeyEx(winreg.HKEY_CLASSES_ROOT, r"Directory\shell\FTL", 0, winreg.KEY_WRITE)
    winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "FTL")
    winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, str(ICON_FILE))
    winreg.SetValueEx(key, "ExtendedSubCommandsKey", 0, winreg.REG_SZ, menu_path)

    # Directory Background: Set ExtendedSubCommandsKey to menu_path
    key = winreg.CreateKeyEx(winreg.HKEY_CLASSES_ROOT, r"Directory\background\shell\FTL", 0, winreg.KEY_WRITE)
    winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "FTL")
    winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, str(ICON_FILE))
    winreg.SetValueEx(key, "ExtendedSubCommandsKey", 0, winreg.REG_SZ, menu_path)
    # fmt: on


def uninstall():
    """Remove Windows explorer context menu entries."""

    # fmt: off
    # Remove Directory Background Verb
    with winreg.OpenKeyEx(winreg.HKEY_CLASSES_ROOT, r"Directory\background\shell\FTL") as key:
        winreg.DeleteKeyEx(key, "")

    # Remove Directory Verb
    with winreg.OpenKeyEx(winreg.HKEY_CLASSES_ROOT, r"Directory\shell\FTL") as key:
        winreg.DeleteKeyEx(key, "")

    # Remove ContextMenu
    with winreg.OpenKeyEx(winreg.HKEY_CLASSES_ROOT, r"Directory\ContextMenus\FTL.menu") as key:
        with winreg.OpenKeyEx(key, r"shell\FTL.settings") as subkey:
            winreg.DeleteKeyEx(subkey, "command")
            winreg.DeleteKeyEx(subkey, "")
        with winreg.OpenKeyEx(key, r"shell\FTL.encode") as subkey:
            winreg.DeleteKeyEx(subkey, "command")
            winreg.DeleteKeyEx(subkey, "")
        with winreg.OpenKeyEx(key, r"shell\FTL.encode.recursive") as subkey:
            winreg.DeleteKeyEx(subkey, "command")
            winreg.DeleteKeyEx(subkey, "")
    # fmt: on
