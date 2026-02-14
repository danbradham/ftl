import dearpygui.dearpygui as dpg

if __name__ == "__main__":
    dpg.create_context()
    dpg.create_viewport()
    dpg.setup_dearpygui()
    dpg.show_style_editor()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
