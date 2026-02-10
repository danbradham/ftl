import json
import multiprocessing
from pathlib import Path
from typing import TypedDict

import dearpygui.dearpygui as dpg
from platformdirs import user_data_dir

LIB_DIR = Path(__file__).parent
USER_DATA_DIR = Path(user_data_dir("ffmpeg-tools"))
USER_SETTINGS = USER_DATA_DIR / "settings.json"
USER_STATE = USER_DATA_DIR / "state.ini"
FONT_FILE = (LIB_DIR / "resources/CommitMono.ttf").as_posix()
ICON_FILE = (LIB_DIR / "resources/ftl.ico").as_posix()
SIZE_ITEMS = [-1, 4096, 3840, 2048, 1920, 1280, 1024, 768, 512]
FPS_ITEMS = [12, 15, 24, 30, 60]
GIF_SIZE_ITEMS = [-1, 4096, 3840, 2048, 1920, 1280, 1024, 768, 512]
GIF_MAXCOLORS_ITEMS = [8, 16, 32, 64, 128, 256]


def shared_state(cache={}):
    if not cache:
        data_manager = multiprocessing.Manager()
        shared_state = data_manager.dict()
        cache["data_manager"] = data_manager
        cache["shared_state"] = shared_state
    return cache["shared_state"]


class Settings(TypedDict):
    mov_enabled: bool
    mov_size: int
    mov_fps: int
    mov_folder: str
    mp4_enabled: bool
    mp4_size: int
    mp4_fps: int
    mp4_folder: str
    gif_enabled: bool
    gif_size: int
    gif_colors: int
    gif_fps: int
    gif_folder: str


def default_settings() -> Settings:
    return {
        "mov_enabled": True,
        "mov_size": -1,
        "mov_fps": 24,
        "mov_folder": ".",
        "mp4_enabled": True,
        "mp4_size": -1,
        "mp4_fps": 24,
        "mp4_folder": ".",
        "gif_enabled": True,
        "gif_size": 768,
        "gif_colors": 128,
        "gif_fps": 24,
        "gif_folder": ".",
    }


def int_to_sizeStr(value):
    if value <= 0:
        return "original"
    return str(value)


def sizeStr_to_int(value):
    if isinstance(value, str) and value.lower() in ("original", "unchanged"):
        return -1
    return int(value)


def save_settings(data: Settings):
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_SETTINGS.write_text(json.dumps(data))


def get_settings() -> Settings:
    settings = default_settings()
    if USER_SETTINGS.exists():
        settings.update(json.loads(USER_SETTINGS.read_text()))
    return settings


def center_viewport(expected_width: int = -1, expected_height: int = -1):
    vp_w = [dpg.get_viewport_client_width(), expected_width][expected_width > -1]
    vp_h = [dpg.get_viewport_client_height(), expected_height][expected_height > -1]

    import pyautogui

    mon_w, mon_h = pyautogui.size()

    x = (mon_w - vp_w) // 2
    y = (mon_h - vp_h) // 2

    dpg.set_viewport_pos([x, y])


def get_theme(name="main", cache={}):
    if name in cache:
        return cache[name]

    if name == "main":
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(
                    dpg.mvThemeCol_Button,
                    (52, 103, 179),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered,
                    (44, 89, 156),
                    category=dpg.mvThemeCat_Core,
                )
        cache[name] = theme

    if name == "primary_button":
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(
                    dpg.mvThemeCol_Button,
                    (52, 103, 179),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered,
                    (44, 89, 156),
                    category=dpg.mvThemeCat_Core,
                )
        cache[name] = theme

    return cache[name]


class FileSelector:
    title = "FTL / Select a Folder..."
    width = 700
    height = 420

    def __init__(self, wid, state, **options):
        self.wid = wid
        self.state = state
        self.options = {
            "modal": True,
            "show": True,
            "directory_selector": True,
        }
        self.options.update(options)

        dpg.create_viewport(
            title=self.title,
            width=self.width,
            height=self.height,
            large_icon=ICON_FILE,
        )
        with dpg.window(tag="primary"):
            dpg.add_file_dialog(tag="dialog", callback=self.callback, **self.options)

        dpg.set_viewport_resize_callback(self.resize_callback)
        self.resize_callback()

        # Always on top...
        dpg.set_viewport_always_top(True)

        # Centered on screen.
        center_viewport(self.width, self.height)

    def callback(self, sender, app_data):
        self.state[self.wid] = app_data
        dpg.stop_dearpygui()

    def resize_callback(self):
        dpg.set_item_width("dialog", dpg.get_viewport_width() - 20)
        dpg.set_item_height("dialog", dpg.get_viewport_height() - 40)


class SettingsDialog:
    title = "FTL / Settings"
    width = 430
    height = 550

    def __init__(self, wid, state):
        self.wid = wid
        self.state = state
        settings = get_settings()

        dpg.create_viewport(
            title=self.title,
            width=self.width,
            height=self.height,
            large_icon=ICON_FILE,
        )

        with dpg.window(tag="primary", label="Video Settings"):
            # MOV Controls
            with dpg.collapsing_header(label="1. MOV", leaf=True):
                with dpg.group(indent=20):
                    dpg.add_checkbox(
                        label="Enable MOV Output",
                        tag="mov_enabled",
                        default_value=settings["mov_enabled"],
                    )
                    dpg.add_combo(
                        label="FPS",
                        items=FPS_ITEMS,
                        tag="mov_fps",
                        default_value=settings["mov_fps"],
                    )
                    dpg.add_combo(
                        label="Size",
                        items=[int_to_sizeStr(s) for s in SIZE_ITEMS],
                        tag="mov_size",
                        default_value=int_to_sizeStr(settings["mov_size"]),
                    )
                    with dpg.group(horizontal=True, horizontal_spacing=1):
                        dpg.add_input_text(
                            label="",
                            tag="mov_folder",
                            default_value=settings["mov_folder"],
                        )
                        dpg.add_button(
                            label=".",
                            tag="mov_cwd_button",
                            callback=lambda: dpg.set_value("mov_folder", "."),
                        )
                        dpg.add_button(
                            label="..",
                            tag="mov_parent_button",
                            callback=lambda: dpg.set_value("mov_folder", ".."),
                        )
                        dpg.add_button(
                            label="Folder",
                            tag="mov_folder_button",
                            callback=lambda: self.browse_for_folder("mov_folder"),
                        )
                    dpg.add_spacer(height=20)

            # MP4 Controls
            with dpg.collapsing_header(label="2. MP4", leaf=True):
                with dpg.group(indent=20):
                    dpg.add_checkbox(
                        label="Enable MP4 Output",
                        tag="mp4_enabled",
                        default_value=settings["mp4_enabled"],
                    )
                    dpg.add_combo(
                        label="FPS",
                        items=FPS_ITEMS,
                        tag="mp4_fps",
                        default_value=settings["mp4_fps"],
                    )
                    dpg.add_combo(
                        label="Size",
                        items=[int_to_sizeStr(s) for s in SIZE_ITEMS],
                        tag="mp4_size",
                        default_value=int_to_sizeStr(settings["mp4_size"]),
                    )
                    with dpg.group(horizontal=True, horizontal_spacing=1):
                        dpg.add_input_text(
                            label="",
                            tag="mp4_folder",
                            default_value=settings["mp4_folder"],
                        )
                        dpg.add_button(
                            label=".",
                            tag="mp4_cwd_button",
                            callback=lambda: dpg.set_value("mp4_folder", "."),
                        )
                        dpg.add_button(
                            label="..",
                            tag="mp4_parent_button",
                            callback=lambda: dpg.set_value("mp4_folder", ".."),
                        )
                        dpg.add_button(
                            label="Folder",
                            tag="mp4_folder_button",
                            callback=lambda: self.browse_for_folder("mp4_folder"),
                        )
                    dpg.add_spacer(height=20)

            # GIF Controls
            with dpg.collapsing_header(label="3. GIF", leaf=True):
                with dpg.group(indent=20):
                    dpg.add_checkbox(
                        label="Enable GIF Output",
                        tag="gif_enabled",
                        default_value=settings["gif_enabled"],
                    )
                    dpg.add_combo(
                        label="FPS",
                        items=FPS_ITEMS,
                        tag="gif_fps",
                        default_value=settings["gif_fps"],
                    )
                    dpg.add_combo(
                        label="Size",
                        items=[int_to_sizeStr(s) for s in GIF_SIZE_ITEMS],
                        tag="gif_size",
                        default_value=int_to_sizeStr(settings["gif_size"]),
                    )
                    dpg.add_combo(
                        label="Max Colors",
                        items=GIF_MAXCOLORS_ITEMS,
                        tag="gif_colors",
                        default_value=settings["gif_colors"],
                    )
                    with dpg.group(horizontal=True, horizontal_spacing=1):
                        dpg.add_input_text(
                            label="",
                            tag="gif_folder",
                            default_value=settings["gif_folder"],
                        )
                        dpg.add_button(
                            label=".",
                            tag="gif_cwd_button",
                            callback=lambda: dpg.set_value("gif_folder", "."),
                        )
                        dpg.add_button(
                            label="..",
                            tag="gif_parent_button",
                            callback=lambda: dpg.set_value("gif_folder", ".."),
                        )
                        dpg.add_button(
                            label="Folder",
                            tag="gif_folder_button",
                            callback=lambda: self.browse_for_folder("gif_folder"),
                        )
                    dpg.add_spacer(height=20)

            dpg.add_button(
                label="Save",
                tag="save_button",
                width=-1,
                height=32,
                callback=self.save_callback,
            )

        # Center viewport...
        center_viewport(self.width, self.height)

    def browse_for_folder(self, tag):
        result = show_detached("get_directory", FileSelector, self.state)
        if result:
            dpg.set_value(tag, Path(result["file_path_name"]).as_posix())

    def save_callback(self, sender, app_data, user_data):
        form_data: Settings = {
            "mov_enabled": dpg.get_value("mov_enabled"),
            "mov_fps": int(dpg.get_value("mov_fps")),
            "mov_size": sizeStr_to_int(dpg.get_value("mov_size")),
            "mov_folder": dpg.get_value("mov_folder"),
            "mp4_enabled": dpg.get_value("mp4_enabled"),
            "mp4_fps": int(dpg.get_value("mp4_fps")),
            "mp4_size": sizeStr_to_int(dpg.get_value("mp4_size")),
            "mp4_folder": dpg.get_value("mp4_folder"),
            "gif_enabled": dpg.get_value("gif_enabled"),
            "gif_fps": int(dpg.get_value("gif_fps")),
            "gif_size": sizeStr_to_int(dpg.get_value("gif_size")),
            "gif_colors": int(dpg.get_value("gif_colors")),
            "gif_folder": dpg.get_value("gif_folder"),
        }
        save_settings(form_data)

        dpg.save_init_file(USER_STATE.as_posix())
        dpg.stop_dearpygui()


def show_detached(wid, wcls, state):
    """Create a window in a separate process.
    Run a dialog in a separate process until it exits.

    Participating classes can set a result on the provided shared state obj
    using <wid>.

    Returns:
        dict: The state set by the UI for the given wid.
    """

    proc = multiprocessing.Process(target=show, args=(wid, wcls, state))
    proc.start()
    proc.join()
    return state.get(wid, {})


def show(wid, wcls, state):
    """Create a window for the specified class.

    Arguments:
        wid: The window ID.
        wcls: The window class.
        state: The shared state object.
    """

    dpg.create_context()

    with dpg.font_registry():
        font = dpg.add_font(file=FONT_FILE, size=14)

    dpg.bind_font(font)

    wcls(wid, state)

    dpg.bind_theme(get_theme("main"))
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("primary", True)
    dpg.start_dearpygui()
    dpg.destroy_context()


def main():
    show("settings", SettingsDialog, shared_state())


if __name__ == "__main__":
    main()
