import tkinter
from typing import Literal

import dearpygui.dearpygui as dpg

from ftl import resources

ui_scale = -1
themes = {}
fonts = {}
font_weight_map = {
    "light": resources.get("CommitMono.ttf").as_posix(),
    "regular": resources.get("CommitMono-400-Regular.otf").as_posix(),
    "bold": resources.get("CommitMono-400-Regular.otf").as_posix(),
    "italic": resources.get("CommitMono-400-Italic.otf").as_posix(),
    "bold_italic": resources.get("CommitMono-400-Italic.otf").as_posix(),
}
font_style_map = {
    "h1": 24,
    "h2": 20,
    "h3": 16,
    "p": 14,
    "s": 12,
}


def load_resources():
    """Load all resources into dearpygui context.

    See also: `ftl.base.event_loop`
    """

    # Load Fonts
    with dpg.font_registry():
        for style_name, size in font_style_map.items():
            for weight_name, font_file in font_weight_map.items():
                fonts[f"{style_name}-{weight_name}"] = dpg.add_font(
                    file=font_file,
                    size=px(size),
                )

    dpg.bind_font(fonts["p-light"])

    # Load Textures
    with dpg.texture_registry():
        for img in resources.ls("png"):
            width, height, channels, data = dpg.load_image(img.as_posix())
            dpg.add_static_texture(
                width=width, height=height, default_value=data, tag=f"img_{img.stem}"
            )


def px(value: int) -> int:
    """Scale a pixel value by the screens dpi scaling factor."""

    global ui_scale
    if ui_scale < 0:
        ui_scale = int(tkinter.Tk().winfo_fpixels("96p")) / 96.0

    return int(value * ui_scale)


def set_font(
    item,
    style: Literal["h1", "h2", "h3", "p", "s"],
    weight: Literal["light", "regular", "bold", "italic", "bold_italic"] = "regular",
):
    """Set the font for an item."""

    dpg.bind_item_font(item, fonts[f"{style}-{weight}"])


def set_theme(item, name):
    """Set the theme for an item."""

    dpg.bind_item_theme(item, get_theme(name))


def get_theme(name="main"):
    """Get a theme by name."""

    # return dpg.add_theme()

    if name in themes:
        return themes[name]

    corner_radius = px(1)

    if name == "main":
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(
                    dpg.mvStyleVar_WindowBorderSize,
                    0,
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_WindowRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_WindowPadding,
                    px(10),
                    px(10),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_FramePadding,
                    px(4),
                    px(4),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_FrameRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_CellPadding,
                    px(5),
                    px(2),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_ItemSpacing,
                    px(8),
                    px(3),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_ChildRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_ScrollbarSize,
                    px(4),
                    category=dpg.mvThemeCat_Core,
                )
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(
                    dpg.mvStyleVar_FrameRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
                # dpg.add_theme_color(
                #     dpg.mvThemeCol_Button,
                #     (52, 103, 179),
                #     category=dpg.mvThemeCat_Core,
                # )
                # dpg.add_theme_color(
                #     dpg.mvThemeCol_ButtonHovered,
                #     (44, 89, 156),
                #     category=dpg.mvThemeCat_Core,
                # )
            with dpg.theme_component(dpg.mvInputInt):
                dpg.add_theme_style(
                    dpg.mvStyleVar_FrameRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
            with dpg.theme_component(dpg.mvCheckbox):
                dpg.add_theme_style(
                    dpg.mvStyleVar_FrameRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBg,
                    (47, 47, 47),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBgHovered,
                    (57, 57, 57),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBgActive,
                    (50, 50, 50),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_CheckMark,
                    (255, 255, 255, 100),
                    category=dpg.mvThemeCat_Core,
                )
        themes[name] = theme

    if name == "modal":
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(
                    dpg.mvStyleVar_WindowBorderSize,
                    1,
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_WindowRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
        themes[name] = theme

    if name == "rules_list":
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(
                    dpg.mvStyleVar_FramePadding,
                    px(3),
                    px(3),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_ChildRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_FrameRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_ItemSpacing,
                    px(8),
                    px(6),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_CellPadding,
                    px(4),
                    px(2),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_HeaderHovered,
                    (51, 51, 55),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_HeaderActive,
                    (55, 55, 59),
                    category=dpg.mvThemeCat_Core,
                )
            with dpg.theme_component(dpg.mvInputInt):
                dpg.add_theme_style(
                    dpg.mvStyleVar_FrameRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
            with dpg.theme_component(dpg.mvCheckbox):
                dpg.add_theme_style(
                    dpg.mvStyleVar_FrameRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBg,
                    (47, 47, 47),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBgHovered,
                    (57, 57, 57),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBgActive,
                    (50, 50, 50),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_CheckMark,
                    (255, 255, 255, 100),
                    category=dpg.mvThemeCat_Core,
                )
        themes[name] = theme

    if name == "primary_button":
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(
                    dpg.mvStyleVar_FrameRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_Button,
                    (52, 103, 179),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered,
                    (44, 89, 156),
                    category=dpg.mvThemeCat_Core,
                )
        themes[name] = theme

    if name == "reject_button":
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(
                    dpg.mvStyleVar_FrameRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_Button,
                    (51, 51, 55),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered,
                    (156, 35, 27, 103),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonActive,
                    (156, 35, 27, 153),
                    category=dpg.mvThemeCat_Core,
                )
        themes[name] = theme

    if name == "red_button":
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(
                    dpg.mvStyleVar_FrameRounding,
                    corner_radius,
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_Button,
                    (179, 52, 45),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered,
                    (156, 35, 27),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonActive,
                    (146, 25, 17),
                    category=dpg.mvThemeCat_Core,
                )
        themes[name] = theme

    return themes[name]
