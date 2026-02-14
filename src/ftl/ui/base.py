import multiprocessing as mp
import queue
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from inspect import isclass
from typing import Any

import dearpygui.dearpygui as dpg
import pyautogui

from ftl import const
from ftl.ui.theme import get_theme


@dataclass
class Event:
    type: str
    payload: dict = field(default_factory=dict)


@dataclass
class Channel:
    inbox: mp.Queue = field(default_factory=mp.Queue)
    outbox: mp.Queue = field(default_factory=mp.Queue)


class Window(ABC):
    def __init__(self, *, channel):
        self.channel = channel

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

        if wait:
            proc.join()

        return cls(**kwargs)


def event_loop(wcls, **kwargs):
    """Start the event_loop for the specified Window class.

    Arguments:
        wcls: The window class.
    """

    dpg.create_context()

    with dpg.font_registry():
        font = dpg.add_font(file=const.FONT_FILE, size=px(14))

    dpg.bind_font(font)

    if isclass(wcls):
        window = wcls(**kwargs)
    else:
        window = wcls
    window.setup()

    dpg.bind_theme(get_theme("main"))
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("primary", True)

    while dpg.is_dearpygui_running():
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


def px(*values, cache={}) -> int:
    if "dpi" not in cache:
        import tkinter

        cache["dpi"] = int(tkinter.Tk().winfo_fpixels("1i"))
        cache["factor"] = cache["dpi"] / 96.0

    return int(values[0] * cache["factor"])
