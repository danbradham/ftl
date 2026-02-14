import multiprocessing
from dataclasses import dataclass, field

import dearpygui.dearpygui as dpg
import pyautogui

from ftl.ui.theme import get_theme


@dataclass
class Channel:
    inbox: multiprocessing.Queue
    output: multiprocessing.Queue
    broadcast: multiprocessing.Queue


class Hub:
    def __init__(self):
        self.manager = multiprocessing.Manager()
        self.channels = self.manager.dict()
        self.broadcast = self.manager.Queue()

    def new_channel(self, id):
        return Channel(multiprocessing.Queue(), multiprocessing.Queue(), self.broadcast)


def center_viewport(width: int = -1, height: int = -1):
    """Center a viewport on the screen.

    If you want to center a viewport before it's visible, pass the *expected*
    width and height.
    """

    screen_w, screen_h = pyautogui.size()

    viewport_w = [dpg.get_viewport_client_width(), width][width > -1]
    viewport_h = [dpg.get_viewport_client_height(), height][height > -1]

    x = (screen_w - viewport_w) // 2
    y = (screen_h - viewport_h) // 2

    dpg.set_viewport_pos([x, y])


def show_detached(wcls, wid, state, **kwargs):
    """Create a window in a separate process.
    Run a dialog in a separate process until it exits.

    Participating classes can set a result on the provided shared state obj
    using <wid>.

    Returns:
        dict: The state set by the UI for the given wid.
    """

    wait = kwargs.get("wait", True)

    proc = multiprocessing.Process(
        target=show,
        args=(wcls, wid, state),
        kwargs=kwargs,
    )
    proc.start()
    if wait:
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

    window = wcls(wid, state)
    render = getattr(window, "render", None)

    dpg.bind_theme(get_theme("main"))
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("primary", True)

    while dpg.is_dearpygui_running():
        if render:
            render()

        dpg.render_dearpygui_frame()

    dpg.destroy_context()
