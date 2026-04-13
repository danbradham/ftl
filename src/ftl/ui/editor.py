from dataclasses import _MISSING_TYPE, dataclass
from logging import warning
from typing import Callable

import dearpygui.dearpygui as dpg

from ftl import tools
from ftl.rules import Rule
from ftl.settings import get_settings, save_settings
from ftl.tasks import parameterize
from ftl.tasks.core import ParameterizedTask
from ftl.ui import core
from ftl.ui.dialogs import ConfirmDialog
from ftl.ui.params import parameter_from_field_type, parameter_from_type_name
from ftl.ui.theme import get_theme, px, set_font, set_theme


@dataclass
class RuleItem:
    row: int | str
    box: int | str
    label: int | str
    rule: Rule


class RuleEditor(core.Window):
    title = "FTL / Rules Editor"
    primary_window = "rule_editor_frame"
    horizontal_scrollbar = False
    vertical_scrollbar = False
    width = 700
    height = 700

    def setup(self):
        self.rule: Rule = None
        self.rules = []
        self.rule_items = []
        self._unsaved_changes = False
        self.frame = dpg.add_window(tag=self.primary_window, label="Rules Editor")
        self.tasks_list = None
        self.ocio_control = None
        with core.parent(self.frame):
            self.confirm_delete = ConfirmDialog(
                tag="confirm_delete",
                label="Confirm",
                message="Are you sure you want to delete this Rule?",
                memoize=True,
                callback=self.on_del_rule,
            )
            self.confirm_unsaved_changes = ConfirmDialog(
                tag="confirm_exit_no_save",
                label="Confirm",
                message="You have unsaved changes to your rules. Would you like to save before exiting?",
                callback=self.on_unsaved_changes,
            )
            with dpg.table(
                tag="columns",
                header_row=False,
                borders_innerH=False,
                borders_outerH=False,
                borders_innerV=False,
                borders_outerV=False,
                scrollY=False,
                scrollX=False,
            ):
                dpg.add_table_column(width_fixed=True)
                dpg.add_table_column(width_stretch=True, init_width_or_weight=0.0)
                with dpg.table_row():
                    self.left = dpg.add_child_window(
                        tag="left_column",
                        label="Rules",
                        width=px(200),
                        height=-1,
                    )
                    self.right = dpg.add_child_window(
                        tag="right_column", label="Body", height=-1, width=-1
                    )

        self.setup_rules_list()
        self.setup_welcome_screen()
        self.setup_exit_callback()
        core.center_viewport()
        self.load_rules()

    def load_rules(self):
        settings = get_settings()
        self.add_rules(settings.get("rules", []))

    def setup_exit_callback(self):
        dpg.configure_viewport(0, disable_close=True)
        dpg.set_exit_callback(self.on_exit)

    def on_exit(self):
        if self.unsaved_changes:
            self.confirm_unsaved_changes.show()
        else:
            dpg.stop_dearpygui()

    def on_unsaved_changes(self, confirm):
        if confirm.accepted:
            self.save_rules()
        dpg.stop_dearpygui()

    @property
    def unsaved_changes(self):
        return dpg.get_item_configuration(core.get_primary_window())["unsaved_document"]

    @unsaved_changes.setter
    def unsaved_changes(self, value):
        if value:
            dpg.configure_viewport(0, title=f"{self.title} *")
            dpg.configure_item(core.get_primary_window(), unsaved_document=True)
            dpg.configure_item(self.save_button, show=True)
            core.refresh_alignments()
        else:
            dpg.configure_viewport(0, title=f"{self.title}")
            dpg.configure_item(core.get_primary_window(), unsaved_document=False)
            dpg.configure_item(self.save_button, show=False)

    def setup_welcome_screen(self):
        self.clear_body()
        with core.parent(self.right):
            with dpg.child_window(tag="body", width=-1, border=False):
                with core.valign(core.CENTER, -48):
                    with core.halign(core.CENTER):
                        dpg.add_image("img_ftl")
                    with core.halign(core.CENTER):
                        set_font(dpg.add_text("Welcome to FTL!"), "h1", "bold_italic")
                    with core.halign(core.CENTER):
                        dpg.add_text("Select or Add an Encoding Rule...")
        core.refresh_alignments()

    def setup_rules_list(self):
        with core.parent(self.left):
            with dpg.group(tag="rules_header", horizontal=True):
                dpg.add_text("Rules")
                with core.halign(core.RIGHT):
                    dpg.add_button(label="Add Rule", callback=self.on_add_rule)

            core.add_separator()

            with dpg.child_window(border=False, autosize_y=True, auto_resize_y=True):
                self.rules_list = dpg.add_table(
                    tag="rules_table", header_row=False, resizable=False
                )
                set_theme(self.rules_list, "rules_list")
                with core.parent(self.rules_list):
                    dpg.add_table_column(width_fixed=True)
                    dpg.add_table_column(width_stretch=True, init_width_or_weight=0.0)

        with core.parent(self.primary_window):
            with core.absolute(core.LEFT, core.BOTTOM, offset=[px(118), -px(24)]):
                self.save_button = dpg.add_button(
                    tag="save_button",
                    label="Save Rules",
                    show=False,
                    callback=self.save_rules,
                )

    def setup_editor(self):
        if dpg.does_item_exist("edit_rules_header"):
            return

        self.clear_body()
        with core.parent(self.right):
            with dpg.child_window(tag="body", width=-1, border=False):
                with dpg.group(tag="edit_rules_header", horizontal=True, width=-1):
                    dpg.add_text("Editing")
                    dpg.add_text(tag="edit_rules_label", label="")
                    set_font("edit_rules_label", "p", "bold_italic")
                    with core.halign(core.RIGHT):
                        button = dpg.add_button(
                            label="Delete", callback=self.confirm_delete.show
                        )
                        dpg.bind_item_theme(button, get_theme("red_button"))

                core.add_separator()

                with dpg.group(tag="edit_rules_options"):
                    dpg.add_checkbox(
                        tag="enabled",
                        label="Enabled",
                        callback=self.on_rule_changed,
                    )
                    dpg.add_input_text(
                        tag="name",
                        label="Name",
                        callback=self.on_rule_changed,
                        hint="enter a name",
                    )
                    with dpg.tooltip("name", delay=0.5):
                        dpg.add_text(
                            "The name of this Rule!",
                        )
                    dpg.add_input_text(
                        tag="description",
                        label="Description",
                        hint="enter a description",
                        callback=self.on_rule_changed,
                    )
                    with dpg.tooltip("description", delay=0.5):
                        dpg.add_text(
                            "Describe this Rule's pattern and tasks.",
                        )
                    dpg.add_combo(
                        tag="file_type",
                        label="File Type",
                        items=["FileSequence", "File"],
                        default_value="FileSequence",
                        callback=self.on_rule_changed,
                    )
                    with dpg.tooltip("file_type", delay=0.5):
                        dpg.add_text(
                            "Choose a File Type to match.",
                        )
                        dpg.add_text("FileSequence: Match image sequences")
                        dpg.add_text("File: Match video files")
                    dpg.add_input_text(
                        tag="file_patterns",
                        label="File Patterns",
                        callback=self.on_rule_changed,
                    )
                    with dpg.tooltip("file_patterns", delay=0.5):
                        dpg.add_text(
                            "Space-separated list of patterns to match names.",
                            wrap=px(300) - px(20),
                        )
                        dpg.add_text("Match All: *")
                        dpg.add_text("Match EXR: *.exr")
                        dpg.add_text("Match Video: *.mov *.mp4 *.avi")
                        dpg.add_text("Match ACEScg files: *acescg*")

                    dpg.add_spacer(height=px(8))
                    self.ocio_control = OcioControl(
                        tag="editor_ocio",
                        callback=lambda: setattr(self, "unsaved_changes", True),
                    )

                    self.tasks_list = TasksList(
                        tag="editor_tasks_list",
                        label="Tasks",
                        callback=lambda: setattr(self, "unsaved_changes", True),
                    )

                set_font("edit_rules_options", "s", "light")
                set_font(self.tasks_list.tag, "s", "light")

    def clear_body(self):
        if dpg.does_item_exist("body"):
            dpg.delete_item("body")

        if self.tasks_list and dpg.does_item_exist(self.tasks_list.tag):
            dpg.delete_item(self.tasks_list.tag)
            self.tasks_list = None

        if self.ocio_control and dpg.does_item_exist(self.ocio_control.tag):
            dpg.delete_item(self.ocio_control.tag)
            self.ocio_control = None

    def set_rule(self, rule: Rule | None):
        if rule is None:
            self.setup_welcome_screen()
        else:
            self.rule = rule
            self.setup_editor()
            self.editor_for_rule(rule)
            self.select_rule(rule)

    def select_rule(self, rule):
        for item in self.rule_items:
            dpg.set_value(item.label, item.rule == rule)

    def editor_for_rule(self, rule: Rule):
        dpg.set_value("edit_rules_label", rule.name)
        dpg.set_value("enabled", rule.enabled)
        dpg.set_value("name", rule.name)
        dpg.set_value("description", rule.description)
        dpg.set_value("file_type", rule.file_type)
        dpg.set_value("file_patterns", " ".join(rule.file_patterns))

        # Update tasks list
        self.ocio_control.set_rule(rule)
        self.tasks_list.set_rule(rule)

    def on_rule_changed(self, sender, app_data, user_data):
        if not self.rule:
            raise ValueError("Rule not set.")

        match sender:
            case "enabled":
                self.rule.enabled = app_data
            case "name":
                self.rule.name = app_data
            case "description":
                self.rule.description = app_data
            case "file_type":
                self.rule.file_type = app_data
            case "file_patterns":
                self.rule.file_patterns = app_data.split()

        self.on_rule_updated(self.rule)
        self.unsaved_changes = True

    def on_rule_updated(self, rule):
        if rule == self.rule:
            self.editor_for_rule(rule)

        for item in self.rule_items:
            if item.rule == rule:
                dpg.set_value(item.box, rule.enabled)
                dpg.set_item_label(item.label, rule.name)

    def add_rule_to_list(self, rule: Rule):
        with core.parent(self.rules_list):
            with dpg.table_row(tag=f"rulelist_{rule.name}", user_data=rule) as rule_row:
                rule_box = dpg.add_checkbox(
                    label="",
                    default_value=rule.enabled,
                    user_data=rule,
                    callback=self.on_rules_list_enabled,
                )
                rule_label = dpg.add_selectable(
                    label=rule.name,
                    user_data=rule,
                    callback=self.on_rules_list_selected,
                )
            self.rule_items.append(RuleItem(rule_row, rule_box, rule_label, rule))

    def on_rules_list_selected(self, sender, app_data, user_data):
        for item in self.rule_items:
            if item.label != sender:
                dpg.set_value(item.label, False)

        if app_data:
            self.set_rule(user_data)
        else:
            self.set_rule(None)

    def on_rules_list_enabled(self, sender, app_data, user_data):
        rule = user_data
        rule.enabled = app_data
        self.on_rule_updated(rule)
        self.unsaved_changes = True

    def on_add_rule(self, sender, app_data, user_data):
        for i in range(100):
            rule_name = f"Rule {len(self.rule_items) + 1 + i}"
            if dpg.does_item_exist(f"rulelist_{rule_name}"):
                continue
            break

        rule = Rule(
            enabled=False,
            name=rule_name,
            file_type="FileSequence",
            file_patterns=["*"],
            tasks=[],
        )
        self.add_rule(rule, select=True)
        self.unsaved_changes = True

    def on_del_rule(self, confirm):
        if confirm.accepted:
            self.remove_rule(self.rule)
        self.unsaved_changes = True

    def add_rules(self, rules: list[Rule]):
        for rule in rules:
            self.add_rule(rule)

    def add_rule(self, rule: Rule, select: bool = False):
        self.rules.append(rule)
        self.add_rule_to_list(rule)
        if select:
            self.set_rule(rule)
            dpg.focus_item("name")

    def remove_rule(self, rule):
        for item in list(self.rule_items):
            if item.rule == rule:
                self.rules.remove(rule)
                self.rule_items.remove(item)
                dpg.delete_item(item.row)
                self.set_rule(None)
                return

    def save_rules(self, *args):
        self.unsaved_changes = False

        # Merge rules from dialog with settings and save...
        settings = get_settings()
        settings["rules"] = self.rules
        save_settings(settings)

    def after_show(self): ...


@dataclass
class OcioControl:
    tag: int | str
    callback: Callable

    def __post_init__(self):
        self.setup()
        self.rule: Rule = None
        self.body = f"{self.tag}_body"

    def setup(self):
        self.checkbox = dpg.add_checkbox(
            label="Enable OCIO",
            tag=f"{self.tag}_enabled",
            callback=self.on_enabled,
        )
        self.group = dpg.add_group(tag=f"{self.tag}_group")

    def show(self):
        if not dpg.does_item_exist(self.body):
            with core.parent(self.group):
                with dpg.child_window(tag=self.body, height=90, border=False):
                    self.input_transform = dpg.add_combo(
                        label="Input Transform",
                        items=tools.get_ocio_input_transforms(),
                        tag=f"{self.tag}_input_transform",
                        callback=self.on_input_changed,
                    )
                    self.display_device = dpg.add_combo(
                        label="Display Device",
                        items=tools.get_ocio_display_devices(),
                        tag=f"{self.tag}_display_device",
                        callback=self.on_display_changed,
                    )
                    self.view_transform = dpg.add_combo(
                        label="View Transform",
                        tag=f"{self.tag}_view_transform",
                        callback=self.on_view_changed,
                    )

        if self.rule:
            dpg.configure_item(
                self.view_transform,
                items=tools.get_ocio_view_transforms(self.rule.ocio_display_device),
            )
            dpg.set_value(self.input_transform, self.rule.ocio_input_transform)
            dpg.set_value(self.display_device, self.rule.ocio_display_device)
            dpg.set_value(self.view_transform, self.rule.ocio_view_transform)

    def hide(self):
        if dpg.does_item_exist(self.body):
            dpg.delete_item(self.body)

    def set_rule(self, rule: Rule):
        if rule != self.rule:
            self.rule = rule
            dpg.set_value(self.checkbox, self.rule.ocio_enabled)
            if self.rule.ocio_enabled:
                self.show()
            else:
                self.hide()

    def on_enabled(self, sender, app_data, user_data):
        self.rule.ocio_enabled = app_data
        if app_data:
            self.show()
        else:
            self.hide()
        self.callback()

    def on_input_changed(self, sender, app_data, user_data):
        self.rule.ocio_input_transform = app_data
        self.callback()

    def on_display_changed(self, sender, app_data, user_data):
        self.rule.ocio_display_device = app_data
        views = tools.get_ocio_view_transforms(app_data)
        dpg.configure_item(self.view_transform, items=views)
        dpg.set_value(self.view_transform, value=views[0])
        self.callback()

    def on_view_changed(self, sender, app_data, user_data):
        self.rule.ocio_view_transform = app_data
        self.callback()


@dataclass
class TaskItem:
    task: ParameterizedTask
    row: int | str
    parameters: dict[str, int | str]


@dataclass
class TasksList:
    tag: int | str
    label: str
    callback: Callable

    def __post_init__(self):
        self.setup()
        self.items = []
        self.rule: Rule = None

    def setup(self):
        with dpg.group(tag=self.tag):
            dpg.add_spacer(height=px(20))
            with dpg.group(tag=f"{self.tag}_header", horizontal=True):
                tag_label = dpg.add_text(self.label)
                set_font(tag_label, "p", "light")
                with core.halign(core.RIGHT):
                    dpg.add_button(label="Add Task")
                    add_tasks_menu("add_task_menu", self.on_add_task)
            core.add_separator()
            self.list = dpg.add_table(
                header_row=False,
                borders_innerH=False,
                borders_outerH=False,
                borders_innerV=False,
                borders_outerV=False,
            )
            with core.parent(self.list):
                dpg.add_table_column(width_fixed=True)
                dpg.add_table_column(width_stretch=True, init_width_or_weight=0.0)
                dpg.add_table_column(width_fixed=True)

    def set_parent(self, tag, after):
        dpg.configure_item(self.tag, parent=tag, after=after, show=True)

    def set_rule(self, rule: Rule):
        if rule != self.rule:
            self.clear()
            self.rule = rule
            for task in rule.tasks:
                self.add_task(task)
        else:
            for task in rule.tasks:
                self.update_task(task)

    def show(self):
        dpg.configure_item(self.tag, show=True)

    def hide(self):
        dpg.configure_item(self.tag, show=False)

    def clear(self):
        for item in list(self.items):
            self.items.remove(item)
            dpg.delete_item(item.row)
        if self.rule:
            self.rule = None

    def update_task(self, task):
        item = self.get_task_item(task)
        if not item:
            warning(f"No Item for task: {task}")
            return
        for name, value in task.parameters.items():
            try:
                dpg.set_value(item.parameters[name], value)
            except KeyError:
                continue

    def remove_task(self, sender, app_data, user_data):
        for item in list(self.items):
            if item.task == user_data:
                self.items.remove(item)
                dpg.delete_item(item.row)

        if user_data in self.rule.tasks:
            self.rule.tasks.remove(user_data)

        if self.callback:
            self.callback()

    def get_task_item(self, task):
        for item in self.items:
            if item.task == task:
                return item

    def add_task(self, task):
        tag = f"task_{task.name}"
        parameter_items = {}

        with core.parent(self.list):
            row = dpg.add_table_row(tag=f"{tag}_row", user_data=task)

            with core.parent(row):
                enabled = dpg.add_checkbox(
                    tag=f"{tag}_enabled",
                    label="",
                    user_data=(task, "enabled"),
                    callback=self.on_parameter_changed,
                )
                parameter_items["enabled"] = enabled
                with dpg.collapsing_header(
                    tag=f"{tag}_parameters",
                    label=task.name,
                    default_open=False,
                    user_data=task,
                ):
                    with dpg.group():
                        for name, param in task.get_parameters().items():
                            # Get value from parameter
                            # or default from dataclass field
                            value = task.parameters.get(name)
                            if value is None and param.default != _MISSING_TYPE:
                                value = param.default

                            # We already made the enabled widget
                            # since we want it to be first
                            if name == "enabled":
                                dpg.set_value(f"{tag}_enabled", value)
                                continue

                            # Setup item kwargs
                            item_tag = f"{tag}_{name}"
                            item_kwargs = dict(
                                tag=item_tag,
                                label=name,
                                user_data=(task, name),
                                callback=self.on_parameter_changed,
                                default_value=value,
                            )
                            item_tooltip = param.metadata.get("help")
                            item_param_type = param.metadata.get("param_type")
                            item_id = None

                            # Check if param_type explicitly set in metadata
                            if item_param_type:
                                item_id = parameter_from_type_name(
                                    item_param_type, **item_kwargs
                                )

                            # Autodetect param_type based on field attributes
                            if not item_id:
                                item_id = parameter_from_field_type(
                                    param.type, **item_kwargs
                                )

                            if not item_id:
                                warning(
                                    f"Unsupported Parameter type: {param.name} -> {param.type}"
                                )
                                continue

                            parameter_items[name] = item_id
                            set_font(item_id, "s", "light")

                            if item_tooltip:
                                with dpg.tooltip(item_id, delay=0.5):
                                    dpg.add_text(item_tooltip)

                    dpg.add_spacer(height=px(8))
                dpg.add_button(
                    label="Delete",
                    callback=self.remove_task,
                    user_data=task,
                )

        self.items.append(TaskItem(task, row, parameter_items))

    def on_add_task(self, sender, app_data, user_data):
        task = parameterize(user_data)
        if task.name in [t.name for t in self.rule.tasks]:
            return

        self.rule.tasks.append(task)
        self.add_task(task)
        self.callback()

    def on_parameter_changed(self, sender, app_data, user_data):
        task, name = user_data
        value = app_data
        task.parameters[name] = value
        self.callback()


def add_tasks_menu(tag: int | str, callback: Callable):
    from ftl import registry

    def _callback(sender, app_data, user_data):
        dpg.set_value(sender, value=False)
        callback(sender, app_data, user_data)

    with dpg.popup(
        dpg.last_item(),
        mousebutton=dpg.mvMouseButton_Left,
    ):
        for name, task in registry.tasks.items():
            if task.hidden:
                continue
            dpg.add_selectable(label=name, callback=_callback, user_data=task)


def main(style_editor=False):
    import sys

    if sys.argv[-1] == "--style_editor":
        RuleEditor.after_show = lambda _: dpg.show_style_editor()
    RuleEditor.show()


if __name__ == "__main__":
    main()
