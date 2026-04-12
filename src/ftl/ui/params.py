from pathlib import Path
from typing import Any, Callable, Literal, get_args, get_origin

import dearpygui.dearpygui as dpg

from ftl.ui import core
from ftl.ui.core import px


def PathParameter(
    tag,
    label: str,
    user_data: Any,
    callback: Callable,
    default_value: str = ".",
):
    group = dpg.add_group(horizontal=True, horizontal_spacing=px(2))

    def browse_for_folder():
        from ftl.ui.file_selector import FileSelector

        path = FileSelector.get_directory()
        if path:
            dpg.set_value(tag, path)
            callback(group, path, user_data)

    def set_path(path):
        dpg.set_value(tag, path)
        callback(group, path, user_data)

    with core.parent(group):
        dpg.add_input_text(
            label="",
            tag=tag,
            default_value=default_value,
        )
        dpg.add_button(
            label=".",
            tag=f"{tag}_cwd_button",
            callback=lambda: set_path("."),
            width=px(30),
        )
        dpg.add_button(
            label="..",
            tag=f"{tag}_parent_button",
            callback=lambda: set_path(".."),
            width=px(30),
        )
        dpg.add_button(
            label=label.title(),
            tag=f"{tag}_folder_button",
            callback=browse_for_folder,
            width=-1,
        )

    return group


def ComboParameter(
    tag,
    cast: type,
    label: str,
    user_data: Any,
    callback: Callable,
    default_value: str | None = None,
    items: list[Any] | None = None,
):
    items = [str(item) for item in items] if items else []
    default_value = str(default_value) if default_value else ""

    def value_changed(sender, app_data, user_data):
        # Cast value back to original type
        app_data = cast(app_data)
        callback(sender, app_data, user_data)

    param = dpg.add_combo(
        items=items,
        label=label,
        tag=tag,
        default_value=default_value,
        user_data=user_data,
        callback=value_changed,
    )
    return param


def ColorParameter(
    tag,
    label: str,
    user_data: Any,
    callback: Callable,
    default_value: str | None = None,
):
    default_enabled = bool(default_value)
    default_value = "#" + (default_value or "000000").lstrip("#")
    group = dpg.add_group(horizontal=True, horizontal_spacing=px(4))

    def rgb_to_hex(r, g, b):
        return "#{:02x}{:02x}{:02x}".format(int(255 * r), int(255 * g), int(255 * b))

    def hex_to_rgb(hex):
        if hex.startswith("#"):
            hex = hex[1:]
        return tuple(int(hex[i : i + 2], 16) for i in (0, 2, 4))

    def checkbox_changed(sender, app_data, user_data):
        if app_data:
            dpg.configure_item(tag, enabled=True)
            callback(sender, dpg.get_value(tag), user_data)
        else:
            dpg.configure_item(tag, enabled=False)
            callback(sender, "", user_data)

    def value_changed(sender, app_data, user_data):
        app_data = rgb_to_hex(*app_data[:-1])
        callback(sender, app_data, user_data)

    with core.parent(group):
        dpg.add_checkbox(
            tag=tag + "_enabled",
            user_data=user_data,
            callback=checkbox_changed,
            default_value=default_enabled,
        )
        dpg.add_color_edit(
            label=label,
            tag=tag,
            default_value=hex_to_rgb(default_value),
            display_mode=dpg.mvColorEdit_hex,
            no_alpha=True,
            user_data=user_data,
            callback=value_changed,
            enabled=default_enabled,
        )

    return group


parameters_by_name = {
    "path": PathParameter,
    "combo": ComboParameter,
    "color": ColorParameter,
}


def parameter_from_type_name(param_type_name: str, **item_kwargs):
    param_type = parameters_by_name.get(param_type_name)
    if param_type:
        return param_type(**item_kwargs)


def parameter_from_field_type(field_type: Any, **item_kwargs):
    hint = get_origin(field_type)
    args = get_args(field_type)

    if hint == Literal:
        item_kwargs["cast"] = type(args[0])
        item_kwargs["items"] = args
        return parameter_from_type_name("combo", **item_kwargs)

    if Path in args:
        return parameter_from_type_name("path", **item_kwargs)

    if field_type is str:
        return dpg.add_input_text(**item_kwargs)
