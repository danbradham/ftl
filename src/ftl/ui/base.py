import atexit
import contextlib
import multiprocessing as mp
import queue
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from inspect import isclass
from uuid import uuid4

import dearpygui.dearpygui as dpg
import pyautogui

from ftl import const, resources
from ftl.ui.theme import get_theme

# Setup some global state so we can track child processes
# and gracefully clean them up on exit.
state = {"child_windows": [], "primary_window": -1, "item_alignments": {}}
fonts = {}


# Alignment "ENUM"
TOP = 0
CENTER = 1
BOTTOM = 2
LEFT = 0
MIDDLE = 1
RIGHT = 2


def on_exit():
    # Send a stop event to each window.
    for win in state["child_windows"]:
        win.stop()

    # Join to allow them time to stop on their own.
    for proc in mp.active_children():
        try:
            proc.join()
        except FileNotFoundError:
            pass


atexit.register(on_exit)


@dataclass
class Event:
    type: str
    payload: dict = field(default_factory=dict)


@dataclass
class Channel:
    inbox: mp.Queue = field(default_factory=mp.Queue)
    outbox: mp.Queue = field(default_factory=mp.Queue)


class Window(ABC):
    title = "FTL"
    width = 800
    height = 600
    primary_window = "primary"

    def __init__(self, *, channel):
        self.channel = channel

    def stop(self):
        """Send None to signal stop."""

        self.channel.inbox.put(None)

    @abstractmethod
    def setup(self):
        """Subclasses must implement this method to build the UI."""

    def update(self):
        """Perform an action each step of the event loop."""

    def event(self, event: Event):
        """Handle events received on the Windows channel queue."""

    def _handle_event(self, event):
        if event is None:
            dpg.stop_dearpygui()
            return

        match event.type:
            case "stop":
                dpg.stop_dearpygui()
            case _:
                self.event(event)

    def _update(self):
        try:
            event = self.channel.inbox.get(False)
            self._handle_event(event)
        except queue.Empty:
            pass
        self.update()

    def after_show(self):
        """Runs after dialog is displayed..."""

    @classmethod
    def show(cls, **kwargs):
        """Run the event_loop for this Window in the main thread."""

        kwargs.setdefault("channel", Channel())

        window = cls(**kwargs)
        event_loop(window)

        return window

    @classmethod
    def detach(cls, *, wait=False, **kwargs):

        kwargs.setdefault("channel", Channel())

        proc = mp.Process(target=event_loop, args=[cls], kwargs=kwargs)
        proc.start()

        win = cls(**kwargs)
        state["child_windows"].append(win)

        if wait:
            proc.join()

        return cls(**kwargs)


def alignment_handler(sender, app_data):
    for item, (alignment, offset) in list(state["item_alignments"].items()):
        if not dpg.does_item_exist(item):
            state["item_alignments"].pop(item)
            continue

        parent = dpg.get_item_parent(item)
        parent_rect = dpg.get_item_rect_size(parent)
        child_rect = dpg.get_item_rect_size(item)

        x = max(0, (parent_rect[0] // 2) - (child_rect[0] // 2))
        if alignment == TOP:
            y = 0
        elif alignment == CENTER:
            y = (parent_rect[1] // 2) - (child_rect[1] // 2)
        else:
            y = parent_rect[1] - child_rect[1]
        y = max(0, min(y + offset, parent_rect[1] - child_rect[1]))

        dpg.set_item_pos(item, [x, y])


def event_loop(wcls, **kwargs):
    """Start the event_loop for the specified Window class.

    Arguments:
        wcls: The window class.
    """

    dpg.create_context()

    load_resources()

    dpg.create_viewport(
        title=wcls.title,
        width=px(wcls.width),
        height=px(wcls.height),
        large_icon=const.ICON_FILE,
    )

    state["primary_window"] = wcls.primary_window
    if isclass(wcls):
        window = wcls(**kwargs)
    else:
        window = wcls
    window.setup()

    # Install the alignment handler
    with dpg.item_handler_registry(tag="alignment_registry"):
        dpg.add_item_resize_handler(callback=alignment_handler)

    dpg.bind_item_handler_registry(wcls.primary_window, "alignment_registry")

    dpg.bind_theme(get_theme("main"))
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(wcls.primary_window, True)

    window.after_show()

    while dpg.is_dearpygui_running():
        window._update()
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


def load_resources():
    # Load Font
    with dpg.font_registry():
        fonts["base"] = dpg.add_font(file=const.FONT_FILE, size=px(14))
        fonts["small"] = dpg.add_font(file=const.FONT_FILE, size=px(8))

    dpg.bind_font(fonts["base"])

    # Load Textures
    with dpg.texture_registry():
        for img in resources.ls("png"):
            width, height, channels, data = dpg.load_image(img.as_posix())
            dpg.add_static_texture(
                width=width, height=height, default_value=data, tag=f"img_{img.stem}"
            )


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


def px(value: int, cache={}) -> int:
    """Scale a pixel value by the screens dpi scaling factor."""

    if "dpi" not in cache:
        import tkinter

        cache["dpi"] = int(tkinter.Tk().winfo_fpixels("96p"))
        cache["factor"] = cache["dpi"] / 96.0

    return int(value * cache["factor"])


@contextlib.contextmanager
def parent(item):
    try:
        dpg.push_container_stack(item)
        yield item
    finally:
        dpg.pop_container_stack()


def unique_tag(tag):
    return f"{tag}_{uuid4().hex[:4]}"


def get_primary_window():
    return state["primary_window"]


@contextlib.contextmanager
def valign(alignment: int = 0, offset: int = 0):
    tag = unique_tag("vbox")
    state["item_alignments"][tag] = (alignment, offset)
    with dpg.child_window(
        tag=tag,
        autosize_x=True,
        autosize_y=False,
        auto_resize_x=False,
        auto_resize_y=True,
        border=False,
        show=True,
    ):
        yield


@contextlib.contextmanager
def halign(alignment: int = 0):
    tag = unique_tag("hbox")

    with dpg.table(
        tag=tag,
        header_row=False,
        borders_innerH=False,
        borders_outerH=False,
        borders_innerV=False,
        borders_outerV=False,
        scrollY=False,
        scrollX=False,
    ):
        for i in range(3):
            stretch = alignment == i
            if stretch:
                dpg.add_table_column(width_fixed=True)
            else:
                dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)

        with dpg.table_row():
            if alignment == LEFT:
                yield
                dpg.add_table_cell()
                dpg.add_table_cell()
            elif alignment == MIDDLE:
                dpg.add_table_cell()
                yield
                dpg.add_table_cell()
            else:
                dpg.add_table_cell()
                dpg.add_table_cell()
                yield
