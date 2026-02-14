import dearpygui.dearpygui as dpg

from ftl import const
from ftl.settings import (
    Settings,
    get_settings,
    int_to_sizeStr,
    save_settings,
    sizeStr_to_int,
)
from ftl.ui.base import Window, center_viewport


class Editor(Window):
    title = "FTL / Settings"
    width = 430
    height = 550

    def setup(self):
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


def main():
    Editor.show()


if __name__ == "__main__":
    main()
