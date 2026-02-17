from dataclasses import _MISSING_TYPE, dataclass, field
from logging import warning
from typing import Callable, Literal, get_args, get_origin

import dearpygui.dearpygui as dpg

from ftl.rules import Rule
from ftl.tasks import EncodeMp4, parameterize
from ftl.tasks.base import ParameterizedTask
from ftl.ui import base
from ftl.ui.theme import get_theme, px, set_font, set_theme

rule = Rule(
    name="Encode File",
    file_type="FileSequence",
    file_patterns=["*"],
    tasks=[
        parameterize(
            EncodeMp4,
            input_colorspace="linear",
            max_size=1920,
            fps=24,
            vcodec="h264",
        )
    ],
)


@dataclass
class RuleItem:
    row: int | str
    box: int | str
    label: int | str
    rule: Rule


class RuleEditor(base.Window):
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
        with base.parent(self.frame):
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
        base.center_viewport(px(self.width), px(self.height))

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
        return dpg.get_item_configuration(base.get_primary_window())["unsaved_document"]

    @unsaved_changes.setter
    def unsaved_changes(self, value):
        if value:
            dpg.configure_viewport(0, title=f"{self.title} *")
            dpg.configure_item(base.get_primary_window(), unsaved_document=True)
            dpg.configure_item(self.save_button, show=True)
            base.refresh_alignments()
        else:
            dpg.configure_viewport(0, title=f"{self.title}")
            dpg.configure_item(base.get_primary_window(), unsaved_document=False)
            dpg.configure_item(self.save_button, show=False)

    def setup_welcome_screen(self):
        self.clear_body()
        with base.parent(self.right):
            with dpg.child_window(tag="body", width=-1, border=False):
                with base.valign(base.CENTER, -48):
                    with base.halign(base.CENTER):
                        dpg.add_image("img_ftl")
                    with base.halign(base.CENTER):
                        set_font(dpg.add_text("Welcome to FTL!"), "h1", "bold_italic")
                    with base.halign(base.CENTER):
                        dpg.add_text("Select or Add an Encoding Rule...")
        base.refresh_alignments()

    def setup_rules_list(self):
        with base.parent(self.left):
            with dpg.group(tag="rules_header", horizontal=True):
                dpg.add_text("Rules")
                with base.halign(base.RIGHT):
                    dpg.add_button(label="Add Rule", callback=self.on_add_rule)

            base.add_separator()

            with dpg.child_window(border=False, autosize_y=True, auto_resize_y=True):
                self.rules_list = dpg.add_table(
                    tag="rules_table", header_row=False, resizable=False
                )
                set_theme(self.rules_list, "rules_list")
                with base.parent(self.rules_list):
                    dpg.add_table_column(width_fixed=True)
                    dpg.add_table_column(width_stretch=True, init_width_or_weight=0.0)

        with base.parent(self.primary_window):
            with base.absolute(base.LEFT, base.BOTTOM, offset=[px(118), -px(24)]):
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
        with base.parent(self.right):
            with dpg.child_window(tag="body", width=-1, border=False):
                with dpg.group(tag="edit_rules_header", horizontal=True, width=-1):
                    dpg.add_text("Editing")
                    dpg.add_text(tag="edit_rules_label", label="")
                    set_font("edit_rules_label", "p", "bold_italic")
                    with base.halign(base.RIGHT):
                        button = dpg.add_button(
                            label="Delete", callback=self.confirm_delete.show
                        )
                        dpg.bind_item_theme(button, get_theme("red_button"))

                base.add_separator()

                with dpg.group(tag="edit_rules_options", width=-1):
                    dpg.add_checkbox(
                        tag="enabled",
                        label="Enabled",
                        callback=self.on_rule_changed,
                    )
                    dpg.add_input_text(
                        tag="name", label="Name", callback=self.on_rule_changed
                    )
                    dpg.add_input_text(
                        tag="description",
                        label="Description",
                        callback=self.on_rule_changed,
                    )
                    dpg.add_combo(
                        tag="file_type",
                        label="File Type",
                        items=["FileSequence", "File"],
                        default_value="FileSequence",
                        callback=self.on_rule_changed,
                    )
                    with dpg.tooltip("file_type", delay=0.4):
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
                    with dpg.tooltip("file_patterns", delay=0.4):
                        dpg.add_text(
                            "Space-separated list of patterns to match names.",
                            wrap=px(300) - px(20),
                        )
                        dpg.add_text("Match All: *")
                        dpg.add_text("Match EXR: *.exr")
                        dpg.add_text("Match Video: *.mov *.mp4 *.avi")
                        dpg.add_text("Match ACEScg files: *acescg*")

                    self.tasks_list = TasksList(tag="editor_tasks_list", label="Tasks")

                set_font("edit_rules_options", "s", "light")
                set_font(self.tasks_list.tag, "p", "light")

    def clear_body(self):
        if dpg.does_item_exist("body"):
            dpg.delete_item("body")

        if self.tasks_list and dpg.does_item_exist(self.tasks_list.tag):
            dpg.delete_item(self.tasks_list.tag)
            self.tasks_list = None

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
        with base.parent(self.rules_list):
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

    def add_rules(self, rules: list[Rule]):
        for rule in rules:
            self.add_rule(rule)

    def add_rule(self, rule: Rule, select: bool = False):
        self.rules.append(rule)
        self.add_rule_to_list(rule)
        if select:
            self.set_rule(rule)

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
        # TODO Save rules to disk
        ...

    def after_show(self): ...


@dataclass
class TaskItem:
    task: ParameterizedTask
    row: int | str


@dataclass
class TasksList:
    tag: int | str
    label: str
    callback: Callable | None = field(default=None)

    def __post_init__(self):
        self.setup()
        self.items = []
        self.rule = None

    def setup(self):
        with dpg.group(tag=self.tag):
            dpg.add_spacer(height=px(20))
            with dpg.group(tag=f"{self.tag}_header", horizontal=True):
                dpg.add_text(self.label)
                with base.halign(base.RIGHT):
                    dpg.add_button(label="Add Task")
                    add_tasks_menu("add_task_menu", self.on_add_task)
            base.add_separator()
            # self.body = dpg.add_child_window(
            #     tag=f"{self.tag}_body",
            #     parent=self.tag,
            #     horizontal_scrollbar=False,
            #     autosize_x=True,
            #     autosize_y=False,
            #     auto_resize_y=True,
            #     border=False,
            # )
            self.list = dpg.add_table(
                header_row=False,
                borders_innerH=False,
                borders_outerH=False,
                borders_innerV=False,
                borders_outerV=False,
            )
            with base.parent(self.list):
                dpg.add_table_column(width_fixed=True)
                dpg.add_table_column(width_stretch=True, init_width_or_weight=0.0)
                dpg.add_table_column(width_fixed=True)

    def set_parent(self, tag, after):
        dpg.configure_item(self.tag, parent=tag, after=after, show=True)

    def set_rule(self, rule):
        self.clear()
        self.rule = rule
        for task in rule.tasks:
            self.add_task(task)

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

    def remove_task(self, sender, app_data, user_data):
        for item in list(self.items):
            if item.task == user_data:
                self.items.remove(item)
                dpg.delete_item(item.row)

        if user_data in self.rule.tasks:
            self.rule.tasks.remove(user_data)

    def add_task(self, task):
        parameters = task.get_parameters()
        tag = f"task_{task.name}"

        with base.parent(self.list):
            row = dpg.add_table_row(tag=f"{tag}_row", user_data=task)

            with base.parent(row):
                dpg.add_checkbox(tag=f"{tag}_enabled", label="")
                with dpg.collapsing_header(
                    tag=f"{tag}_parameters",
                    label=task.name,
                    default_open=False,
                    user_data=task,
                ):
                    with dpg.group():
                        for name, param in parameters.items():
                            default = None
                            if param.default != _MISSING_TYPE:
                                default = param.default
                            hint = get_origin(param.type)

                            if name == "enabled":
                                dpg.set_value(f"{tag}_enabled", default)
                                continue

                            id = None
                            if hint == Literal:
                                options = get_args(param.type)
                                id = dpg.add_combo(
                                    tag=f"{tag}_{name}",
                                    label=name,
                                    items=options,
                                    default_value=default,
                                )
                            elif param.type is str:
                                id = dpg.add_input_text(
                                    tag=f"{tag}_{name}",
                                    label=name,
                                    default_value=default,
                                )
                            else:
                                warning(f"Unsupported Parameter type: {param.type}")

                            if id:
                                set_font(id, "s", "light")
                dpg.add_button(label="delete", callback=self.remove_task, user_data=task)

        self.items.append(TaskItem(task, row))

    def on_add_task(self, sender, app_data, user_data):
        task = parameterize(user_data)
        if task.name in [t.name for t in self.rule.tasks]:
            return

        self.rule.tasks.append(task)
        self.add_task(task)


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

            with base.halign(base.RIGHT):
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
        base.set_alignment(self.tag, base.CENTER, base.CENTER, (0, 0))

    def show(self):
        if self.do_not_ask_again:
            self.accept()
            return

        self.accepted = False
        dpg.configure_item(self.tag, show=True)
        base.refresh_alignments()

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


def main(style_editor=False):
    import sys

    if sys.argv[-1] == "--style_editor":
        RuleEditor.after_show = lambda _: dpg.show_style_editor()
    RuleEditor.show()


if __name__ == "__main__":
    main()
