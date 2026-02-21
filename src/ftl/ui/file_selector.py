import queue

import dearpygui.dearpygui as dpg

from ftl.ui.core import Window, center_viewport
from ftl.ui.theme import px


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
        dpg.set_item_width("dialog", dpg.get_viewport_width() - px(10))
        dpg.set_item_height("dialog", dpg.get_viewport_height() - px(24))

    @classmethod
    def get_directory(cls):
        options = dict(modal=True, show=True, directory_selector=True)
        dialog = cls.detach(wait=True, options=options)
        try:
            return dialog.channel.outbox.get(False)
        except queue.Empty:
            pass


if __name__ == "__main__":
    result = FileSelector.get_directory()
