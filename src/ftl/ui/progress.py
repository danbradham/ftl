import dearpygui.dearpygui as dpg

from ftl.types import Status
from ftl.ui import core
from ftl.ui.core import Event, center_viewport, delay
from ftl.ui.theme import px, set_theme


class ProgressDialog(core.Window):
    title = "Progress"
    width = 360
    height = 120

    def setup(self):
        self.exit_after = None

        dpg.configure_viewport(
            item=self.primary_window,
            resizable=False,
            decorated=False,
        )
        with dpg.window(tag="primary", width=px(self.width), height=px(self.height)):
            dpg.add_text("Perparing Tasks...", tag="label")
            dpg.add_spacer(height=px(8))
            dpg.add_progress_bar(
                tag="progress", default_value=-1, width=-1, height=px(20)
            )
            dpg.add_spacer(height=px(8))
            with dpg.table(header_row=False):
                dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)
                dpg.add_table_column(width_fixed=True)
                with dpg.table_row():
                    dpg.add_text("", tag="message")
                    dpg.add_button(
                        tag="button", label="Cancel", callback=self.on_cancel_pressed
                    )

        # Always on top...
        dpg.set_viewport_always_top(True)

        # Centered on screen.
        center_viewport()

    def after_show(self):
        set_theme(self.primary_window, "modal")
        delay(0.2, lambda: self.channel.outbox.put(Event("process_started")))

    def close(self, delay=1):
        self.exit_after = dpg.get_total_time() + delay

    def on_cancel_pressed(self):
        self.channel.outbox.put(Event("cancel"))

    def fail(self):
        self.channel.inbox.put(
            Event("failed", {"label": "Error", "message": "Failed to encode..."})
        )

    def cancel(self, label: str | None = None):
        self.channel.inbox.put(Event("cancel", {"label": label}))

    def start(self, label: str | None = None):
        self.channel.inbox.put(Event("start", {"label": label, "message": None}))

    def set_progress(
        self,
        value: int,
        label: str | None = None,
        message: str | None = None,
    ):
        self.channel.inbox.put(
            Event(
                "progress",
                {
                    "value": value,
                    "label": label,
                    "message": message,
                },
            )
        )

    def finish(self, label: str | None = None, message: str | None = None):
        self.channel.inbox.put(Event("finish", {"label": label, "message": message}))

    def event(self, event):
        match event.type:
            case "start":
                dpg.set_value("progress", 0.0)
            case "progress":
                dpg.set_value("progress", event.payload["value"] / 100.0)
            case "finish":
                dpg.set_value("progress", 1.0)
                dpg.configure_item("button", show=False)
                self.close(delay=2)
            case "cancel":
                dpg.configure_item("button", show=True, label="...")
                self.close(delay=2)
            case "failed":
                dpg.configure_item("button", show=True, label="...")
                self.close(delay=2)
            case _:
                dpg.set_value("label", f"Unknown event type: {event.type}")

        if label := event.payload.get("label"):
            dpg.set_value("label", label)

        if message := event.payload.get("message"):
            dpg.set_value("message", message)

    def update(self):
        if self.exit_after and dpg.get_total_time() > self.exit_after:
            dpg.stop_dearpygui()

    @classmethod
    def from_runner(cls, runner):
        window = cls.detach(wait=False)

        def on_runner_status_changed(event):
            status = event.payload["status"]
            match status:
                case Status.RUNNING:
                    window.start(label="Running")
                case Status.SUCCESS:
                    window.finish(label="Done", message="See ya.")
                case Status.CANCELLED:
                    window.cancel(label="Cancelled")
                case Status.PENDING:
                    window.start()
                case Status.FAILED:
                    window.fail()

        def on_runner_progress_changed(event):
            window.set_progress(
                event.payload["progress"],
                event.payload.get("label", None),
                event.payload.get("message", None),
            )

        def check_user_input(event):
            # Process any events received from the ProgressDialog
            if window.channel.outbox.empty():
                return

            ui_event = window.channel.outbox.get()
            if ui_event.type == "cancel":
                runner.request(Status.CANCELLED)

        runner.signals.on("status_changed", on_runner_status_changed)
        runner.signals.on("progress_changed", on_runner_progress_changed)
        runner.signals.on("before_task", check_user_input)
        runner.signals.on("await_task", check_user_input)
        return window
