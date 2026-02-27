from dataclasses import dataclass, field
from typing import Callable

import dearpygui.dearpygui as dpg

from ftl.ui import core
from ftl.ui.theme import px, set_theme


@dataclass
class ConfirmDialog:
    tag: int | str
    label: str
    message: str
    callback: Callable | None = field(default=None)
    memoize: bool = field(default=False)
    width: int = field(default=px(300))

    def __post_init__(self):
        self.accepted = False
        self.do_not_ask_again = False
        self.setup()

    def setup(self):
        with dpg.window(
            tag=self.tag,
            label=self.label,
            modal=True,
            show=False,
            no_title_bar=True,
            width=self.width,
            height=-1,
        ):
            dpg.add_text(self.message, wrap=self.width - px(20))
            if self.memoize:
                dpg.add_checkbox(
                    label="Don't ask again",
                    tag=f"{self.tag}_memo",
                    callback=lambda: setattr(self, "do_not_ask_again", True),
                )

            with core.halign(core.RIGHT):
                with dpg.group(horizontal=True):
                    yes_button = dpg.add_button(
                        label="Yes",
                        width=px(75),
                        callback=self.accept,
                    )
                    set_theme(yes_button, "primary_button")
                    no_button = dpg.add_button(
                        label="No",
                        width=px(75),
                        callback=self.reject,
                    )
                    set_theme(no_button, "reject_button")

        set_theme(self.tag, "modal")
        core.set_alignment(self.tag, core.CENTER, core.CENTER, (0, 0))

    def show(self):
        if self.do_not_ask_again:
            self.accept()
            return

        self.accepted = False
        dpg.configure_item(self.tag, show=True)
        core.refresh_alignments()

    def hide(self, *args):
        dpg.configure_item(self.tag, show=False)

    def accept(self, *args):
        self.accepted = True
        if self.callback:
            self.callback(self)
        self.hide()

    def reject(self, *args):
        self.accepted = False
        if self.callback:
            self.callback(self)
        self.hide()
