import sys
from dataclasses import dataclass, field
from typing import Callable

import dearpygui.dearpygui as dpg

from ftl.ui import core
from ftl.ui.theme import px, set_font, set_theme


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


@dataclass
class ErrorDialog:
    tag: int | str
    title: str
    label: str
    message: str
    callback: Callable | None = field(default=None)
    width: int = field(default=px(400))

    def __post_init__(self):
        self.accepted = False
        self.setup()

    def setup(self):
        with dpg.window(
            tag=self.tag,
            modal=True,
            show=False,
            no_title_bar=True,
            width=self.width,
            height=-1,
        ):
            dpg.add_text(self.label)
            dpg.add_input_text(
                default_value=self.message,
                multiline=True,
                readonly=True,
                height=px(200),
            )

            with core.halign(core.RIGHT):
                with dpg.group(horizontal=True):
                    close_button = dpg.add_button(
                        label="Close",
                        width=px(75),
                        callback=self.accept,
                    )
                    set_theme(close_button, "primary_button")

        set_theme(self.tag, "modal")

        core.center_viewport()

    def show(self):
        self.accepted = False
        dpg.configure_item(self.tag, show=True)

    def hide(self, *args):
        dpg.configure_item(self.tag, show=False)

    def accept(self, *args):
        self.accepted = True
        if self.callback:
            self.callback(self)
        self.hide()


class ErrorMessageBox(core.Window):
    title = "Error"
    width = 400
    height = 260

    def __init__(self, *, title: str, label: str, message: str, **kwargs):
        self.exit_after = None
        self.kwargs = {
            "title": title,
            "label": label,
            "message": message,
        }
        super().__init__(**kwargs)

    @classmethod
    def create(
        cls,
        title: str | None = None,
        label: str | None = None,
        message: str | None = None,
    ):
        window = cls.detach(wait=True, title=title, label=label, message=message)
        return window

    def setup(self):
        with dpg.window(
            tag=self.primary_window,
            label=self.title,
            no_title_bar=False,
            width=px(self.width),
            height=px(self.height),
        ):
            with core.valign(core.CENTER):
                label = dpg.add_text("An error occurred!", tag="label")
                set_font(label, "h3", "bold_italic")
                message = dpg.add_input_text(
                    default_value="Error details will appear here.",
                    multiline=True,
                    readonly=True,
                    height=px(150),
                    width=-1,
                    tag="message",
                )
                set_font(message, "s", "regular")

                with core.halign(core.RIGHT):
                    with dpg.group(horizontal=True):
                        close_button = dpg.add_button(
                            label="OK",
                            width=px(100),
                            callback=self.accept,
                        )
                        set_theme(close_button, "reject_button")

        set_theme(self.primary_window, "modal")
        core.center_viewport()

        if title := self.kwargs.get("title"):
            self.title = title
            dpg.configure_item(self.primary_window, label=title)
        if label := self.kwargs.get("label"):
            dpg.configure_item("label", default_value=label)
        if message := self.kwargs.get("message"):
            dpg.configure_item("message", default_value=message)

    def accept(self, *args):
        self.accepted = True
        self.stop()
        print("fuck you.")
        sys.exit(0)


def main():
    import traceback

    try:
        raise ValueError("Test error")
    except Exception as e:
        ErrorMessageBox.create("Error", str(e), traceback.format_exc())


if __name__ == "__main__":
    main()
