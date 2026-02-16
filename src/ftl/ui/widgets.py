import dearpygui.dearpygui as dpg

from ftl.rules import Rule
from ftl.tasks import EncodeMp4, parameterize
from ftl.ui import base
from ftl.ui.base import px

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


class RuleEditor(base.Window):
    primary_window = "rule_editor_frame"
    width = 700
    height = 500

    def setup(self):
        self.rule = None
        self.rules = []
        self.rule_items = []
        self.frame = dpg.add_window(tag=self.primary_window, label="Rules Editor")
        with base.parent(self.frame):
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
                    self.right = dpg.add_child_window(tag="right_column", label="Body")

        self.setup_rules_list()
        self.setup_welcome_screen()

    def on_rules_list_selected(self, sender, app_data, user_data):
        for row, box, label in self.rule_items:
            if label != sender:
                dpg.set_value(label, False)

        if app_data:
            self.set_rule(user_data)
        else:
            self.set_rule(None)

    def setup_rules_list(self):
        with base.parent(self.left):
            with dpg.group(tag="rules_header", horizontal=True):
                dpg.add_text("Rules")
                with base.halign(base.RIGHT):
                    dpg.add_button(label="Add Rule", callback=self.add_rule)

            with dpg.child_window(border=False, autosize_y=True, auto_resize_y=True):
                self.rules_list = dpg.add_table(
                    tag="rules_table", header_row=False, resizable=False
                )
                dpg.bind_item_theme(self.rules_list, base.get_theme("rules_list"))
                with base.parent(self.rules_list):
                    dpg.add_table_column(width_fixed=True)
                    dpg.add_table_column(width_stretch=True, init_width_or_weight=0.0)

    def add_rule_to_list(self, rule: Rule):
        with base.parent(self.rules_list):
            with dpg.table_row(tag=f"rulelist_{rule.name}", user_data=rule) as rule_row:
                rule_box = dpg.add_checkbox(
                    label="",
                    default_value=rule.enabled,
                    user_data=rule,
                )
                rule_label = dpg.add_selectable(
                    label=rule.name,
                    user_data=rule,
                    callback=self.on_rules_list_selected,
                )
            self.rule_items.append((rule_row, rule_box, rule_label))

    def setup_welcome_screen(self):
        self.clear_body()
        with base.parent(self.right):
            with dpg.child_window(tag="body", width=-1, border=False):
                with base.valign(base.CENTER, -48):
                    with base.halign(base.CENTER):
                        dpg.add_image("img_ftl")
                    with base.halign(base.CENTER):
                        dpg.add_text("Welcome to FTL!")
                    with base.halign(base.CENTER):
                        dpg.add_text("Select or Add a Rule...")
        base.alignment_handler(None, None)

    def setup_editor(self):
        self.clear_body()
        with base.parent(self.right):
            with dpg.child_window(tag="body", width=-1, border=False):
                with dpg.group(tag="edit_rules_header", horizontal=True):
                    dpg.add_text("Editing Rule")
                    with base.halign(base.RIGHT):
                        button = dpg.add_button(label="Delete", callback=self.del_rule)
                        dpg.bind_item_theme(button, base.get_theme("red_button"))

                dpg.add_spacer(height=1)
                dpg.add_input_text(tag="name", label="Name")
                dpg.add_input_text(tag="description", label="Description")
                dpg.add_input_text(tag="file_type", label="File Type")
                dpg.add_input_text(tag="file_patterns", label="File Patterns")

    def clear_body(self):
        if dpg.does_item_exist("body"):
            dpg.delete_item("body")

    def editor_for_rule(self, rule: Rule):
        dpg.set_value("name", rule.name)
        dpg.set_value("description", rule.description)
        dpg.set_value("file_type", rule.file_type)
        dpg.set_value("file_patterns", " ".join(rule.file_patterns))

    def set_rule(self, rule: Rule | None):
        if rule is None:
            self.setup_welcome_screen()
        else:
            self.rule = rule
            self.setup_editor()
            self.editor_for_rule(rule)

    def del_rule(self, sender, app_data, user_data): ...

    def add_rule(self, sender, app_data, user_data):
        for i in range(100):
            rule_name = f"Rule {len(self.rule_items) + 1 + i}"
            if dpg.does_item_exist(f"rulelist_{rule_name}"):
                continue
            break

        rule = Rule(
            name=rule_name,
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
        self.set_rule(rule)
        self.add_rule_to_list(rule)

    def save_rule(self): ...

    def reset_rule(self):
        # Close the rule editor window
        dpg.delete_item("rule_editor_frame")


def main():
    RuleEditor.show()


if __name__ == "__main__":
    main()
