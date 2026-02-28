import atexit
import contextlib
import multiprocessing as mp
import queue
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from inspect import isclass
from logging import warning
from typing import Callable
from uuid import uuid4

import dearpygui.dearpygui as dpg
import pyautogui

from ftl import resources
from ftl.ui.theme import get_theme, load_resources, px

# Setup some global state so we can track child processes
# and gracefully clean them up on exit.
state = {
    "child_windows": [],
    "primary_window": -1,
    "item_alignments": {},
}
fonts = {}
timers = []


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
        try:
            win.stop()
        except Exception as e:
            warning(e)
            continue

    # Join to allow them time to stop on their own.
    for proc in mp.active_children():
        try:
            proc.join()
        except FileNotFoundError:
            pass


atexit.register(on_exit)


@dataclass
class Timer:
    time: float
    callback: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)


@dataclass
class Event:
    type: str
    payload: dict = field(default_factory=dict)


@dataclass
class Channel:
    inbox: mp.Queue = field(default_factory=mp.Queue)
    outbox: mp.Queue = field(default_factory=mp.Queue)


def on(event_type: str):
    """Decorate a Window method to receive specific events..."""

    def describe_method(meth):
        handlers = meth.__class__.event_handlers.setdefault(event_type, [])
        handlers.append(meth)
        return meth

    return describe_method


def broadcast(event: Event | None):
    for win in state["windows"]:
        win.channel.inbox.put(event)


class Window(ABC):
    title = "FTL"
    width = 800
    height = 600
    primary_window = "primary"
    horizontal_scrollbar = False
    vertical_scrollbar = True
    event_handlers = {}

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
            for handler in self.event_handlers.get(event.type, []):
                handler(self, event)
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


def refresh_alignments():
    delay(0.02, alignment_handler, (None, None))


def set_alignment(tag, halignment: int, valignment: int, offset: tuple):
    state["item_alignments"][tag] = ((halignment, valignment), offset)


def alignment_handler(sender, app_data):
    for item, (alignment, offset) in list(state["item_alignments"].items()):
        if not dpg.does_item_exist(item):
            state["item_alignments"].pop(item)
            continue

        if not dpg.get_item_configuration(item)["show"]:
            continue

        if item.startswith("abs") or isinstance(alignment, tuple):
            parent = None
            parent_rect = (
                dpg.get_viewport_client_width(),
                dpg.get_viewport_client_height(),
            )
        else:
            parent = dpg.get_item_parent(item)
            parent_rect = dpg.get_item_rect_size(parent)

        child_rect = dpg.get_item_rect_size(item)

        if isinstance(alignment, tuple):
            halignment, valignment = alignment
            hoffset, voffset = offset
        else:
            halignment, valignment = CENTER, alignment
            hoffset, voffset = 0, offset

        if valignment == TOP:
            y = 0
        elif valignment == CENTER:
            y = (parent_rect[1] // 2) - (child_rect[1] // 2)
        else:
            y = parent_rect[1] - child_rect[1]
        if halignment == LEFT:
            x = 0
        elif halignment == CENTER:
            x = max(0, (parent_rect[0] // 2) - (child_rect[0] // 2))
        else:
            x = parent_rect[0] - child_rect[0]

        x = max(0, min(x + hoffset, parent_rect[0] - child_rect[0]))
        y = max(0, min(y + voffset, parent_rect[1] - child_rect[1]))

        dpg.set_item_pos(item, [x, y])


def delay(
    sec: float,
    callback: Callable,
    args: tuple | None = None,
    kwargs: dict | None = None,
):
    args = args or ()
    kwargs = kwargs or {}
    timers.append(Timer(dpg.get_total_time() + sec, callback, args, kwargs))


def check_timers():
    for timer in list(timers):
        if timer.time <= dpg.get_total_time():
            timer.callback(*timer.args, **timer.kwargs)
            timers.remove(timer)


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
        large_icon=resources.get("ftl.ico").as_posix(),
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
    dpg.configure_item(
        wcls.primary_window,
        horizontal_scrollbar=wcls.horizontal_scrollbar,
        no_scrollbar=not wcls.vertical_scrollbar,
        no_scroll_with_mouse=not wcls.vertical_scrollbar,
    )

    while dpg.is_dearpygui_running():
        check_timers()
        window._update()
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


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
def absolute(halignment: int = 0, valignment: int = 0, offset: list[int] = [0, 0]):
    tag = unique_tag("abs")
    state["item_alignments"][tag] = ((halignment, valignment), offset)
    with dpg.child_window(
        tag=tag,
        autosize_x=False,
        autosize_y=False,
        auto_resize_x=True,
        auto_resize_y=True,
        border=False,
        show=True,
    ):
        yield


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


def add_separator():
    dpg.add_spacer(height=px(5))
    dpg.add_separator()
    dpg.add_spacer(height=px(5))
