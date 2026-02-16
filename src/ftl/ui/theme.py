import dearpygui.dearpygui as dpg


def get_theme(name="main", cache={}):
    """Get a theme by name."""
    from ftl.ui.base import px

    if name in cache:
        return cache[name]

    if name == "main":
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(
                    dpg.mvStyleVar_FramePadding,
                    px(5),
                    px(5),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(
                    dpg.mvStyleVar_ItemSpacing,
                    px(8),
                    px(3),
                    category=dpg.mvThemeCat_Core,
                )
            with dpg.theme_component(dpg.mvButton):
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
        cache[name] = theme

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
            with dpg.theme_component(dpg.mvCheckbox):
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBg,
                    (47, 47, 47),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBgHovered,
                    (40, 40, 40),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBgActive,
                    (30, 30, 30),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_CheckMark,
                    (200, 200, 200),
                    category=dpg.mvThemeCat_Core,
                )
        cache[name] = theme

    if name == "primary_button":
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
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
        cache[name] = theme

    if name == "red_button":
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
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
        cache[name] = theme

    return cache[name]
