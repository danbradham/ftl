import multiprocessing
from pathlib import Path

import dearpygui.dearpygui as dpg

from ftl import const
from ftl.settings import (
    Settings,
    get_settings,
    int_to_sizeStr,
    save_settings,
    sizeStr_to_int,
)


def shared_state(key=None, cache={}):
    """Get a shared state dict, managed by a multiprocessing.Manager.

    This data can be shared between multiprocessing.Processes and
    is the only way of passing data between windows in FTL.

    Use one of these when constructing windows:
        state = shared_state()
        run_detached("Settings", SettingsEditor, state)
    """

    if not cache:
        data_manager = multiprocessing.Manager()
        shared_state = data_manager.dict()
        cache["data_manager"] = data_manager
        cache[key] = shared_state
    return cache[key]


def center_viewport(expected_width: int = -1, expected_height: int = -1):
    """Center a viewport on the screen.

    If you want to center a viewport before it's visible, pass the *expected*
    width and height.
    """

    import pyautogui

    screen_w, screen_h = pyautogui.size()

    viewport_w = [dpg.get_viewport_client_width(), expected_width][expected_width > -1]
    viewport_h = [dpg.get_viewport_client_height(), expected_height][expected_height > -1]

    x = (screen_w - viewport_w) // 2
    y = (screen_h - viewport_h) // 2

    dpg.set_viewport_pos([x, y])


def get_theme(name="main", cache={}):
    """Get a theme by name."""

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
            large_icon=const.ICON_FILE,
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

    @classmethod
    def get_directory(cls, wid=None, state=None):
        wid = wid or "get_directory"
        state = state or shared_state()
        return show_detached(
            cls, wid, state, modal=True, show=True, directory_selector=True
        )


class SettingsEditor:
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
            large_icon=const.ICON_FILE,
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
                        items=const.FPS_ITEMS,
                        tag="mov_fps",
                        default_value=settings["mov_fps"],
                    )
                    dpg.add_combo(
                        label="Size",
                        items=[int_to_sizeStr(s) for s in const.SIZE_ITEMS],
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
                        items=const.FPS_ITEMS,
                        tag="mp4_fps",
                        default_value=settings["mp4_fps"],
                    )
                    dpg.add_combo(
                        label="Size",
                        items=[int_to_sizeStr(s) for s in const.SIZE_ITEMS],
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
                        items=const.FPS_ITEMS,
                        tag="gif_fps",
                        default_value=settings["gif_fps"],
                    )
                    dpg.add_combo(
                        label="Size",
                        items=[int_to_sizeStr(s) for s in const.GIF_SIZE_ITEMS],
                        tag="gif_size",
                        default_value=int_to_sizeStr(settings["gif_size"]),
                    )
                    dpg.add_combo(
                        label="Max Colors",
                        items=const.GIF_MAXCOLORS_ITEMS,
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
        result = FileSelector.get_directory(state=self.state)
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

        dpg.stop_dearpygui()

    @classmethod
    def show(cls, wid=None, state=None):
        wid = wid or "settings"
        state = state or shared_state()
        show(SettingsEditor, wid, state)


def show_detached(wcls, wid, state, **kwargs):
    """Create a window in a separate process.
    Run a dialog in a separate process until it exits.

    Participating classes can set a result on the provided shared state obj
    using <wid>.

    Returns:
        dict: The state set by the UI for the given wid.
    """

    proc = multiprocessing.Process(target=show, args=(wcls, wid, state), kwargs=kwargs)
    proc.start()
    proc.join()
    return state.get(wid, {})


def show(wcls, wid, state, **kwargs):
    """Create a window for the specified class.

    Arguments:
        wid: The window ID.
        wcls: The window class.
        state: The shared state object.
    """

    dpg.create_context()

    with dpg.font_registry():
        font = dpg.add_font(file=const.FONT_FILE, size=14)

    dpg.bind_font(font)

    wcls(wid, state)

    dpg.bind_theme(get_theme("main"))
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("primary", True)
    dpg.start_dearpygui()
    dpg.destroy_context()
