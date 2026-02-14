import queue

import dearpygui.dearpygui as dpg

from ftl import const
from ftl.ui.base import Window, center_viewport, px


class FileSelector(Window):
    title = "FTL / Select a Folder..."
    width = 700
    height = 420

    def __init__(self, options, **kwargs):
        self.options = {
            "modal": True,
            "show": True,
            "directory_selector": True,
        }
        self.options.update(options)
        super().__init__(**kwargs)

    def setup(self):
        dpg.create_viewport(
            title=self.title,
            width=px(self.width),
            height=px(self.height),
            large_icon=const.ICON_FILE,
        )
        with dpg.window(tag="primary"):
            dpg.add_file_dialog(tag="dialog", callback=self.callback, **self.options)

        dpg.set_viewport_resize_callback(self.resize_callback)
        self.resize_callback()

        # Always on top...
        dpg.set_viewport_always_top(True)

        # Centered on screen.
        center_viewport(px(self.width), px(self.height))

    def callback(self, sender, app_data):
        self.channel.outbox.put(app_data["file_path_name"])
        dpg.stop_dearpygui()

    def resize_callback(self):
        dpg.set_item_width("dialog", dpg.get_viewport_width() - px(20))
        dpg.set_item_height("dialog", dpg.get_viewport_height() - px(40))

    @classmethod
    def get_directory(cls):
        options = dict(modal=True, show=True, directory_selector=True)
        dialog = cls.detach(wait=True, options=options)
        try:
            return dialog.channel.outbox.get(False)
        except queue.Empty:
            pass
