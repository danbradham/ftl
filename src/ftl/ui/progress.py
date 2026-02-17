import dearpygui.dearpygui as dpg

from ftl.ui.base import Event, Window, center_viewport, px
from ftl.ui.theme import set_theme


class ProgressDialog(Window):
    title = "Progress"
    width = 400
    height = 100

    def setup(self):
        self.exit_after = None

        dpg.configure_viewport(
            item=self.primary_window,
            resizable=False,
            decorated=False,
        )
        with dpg.window(tag="primary", width=px(self.width), height=px(self.height)):
            dpg.add_text("Perparing Tasks", tag="label")
            dpg.add_spacer(height=px(10))
            dpg.add_progress_bar(tag="progress", default_value=-1, width=-1)
            dpg.add_spacer(height=px(10))

        # Always on top...
        dpg.set_viewport_always_top(True)

        # Centered on screen.
        center_viewport(px(self.width), px(self.height))

    def after_show(self):
        set_theme(self.primary_window, "modal")

    def close(self, delay=1):
        self.exit_after = dpg.get_total_time() + delay

    def cancel(self):
        self.channel.outbox.put(Event("cancel"))

    def event(self, event):
        match event.type:
            case "start":
                dpg.set_value("progress", 0.0)
            case "step":
                dpg.set_value("progress", event.payload.get("t", 0.5))
            case "finished":
                dpg.set_value("progress", 1.0)
                self.close()
            case _:
                dpg.set_value("label", f"Unknown event type: {event.type}")

        if label := event.payload.get("label"):
            dpg.set_value("label", label)

    def update(self):
        if self.exit_after and dpg.get_total_time() > self.exit_after:
            dpg.stop_dearpygui()

    @classmethod
    def from_tasks(cls, tasks):
        window = cls.detach(wait=False)
        total_tasks = len(tasks)

        def log_handler(event):
            """Converts Task log records to UI Events."""

            task = event.get("task")
            type = event.get("type")
            if type != "progress":
                return

            t = float(sum([t.log.t for t in tasks])) / float(total_tasks)
            label = f"Encoding {tasks.index(task) + 1} of {total_tasks}"
            new_event = Event(event["event"], {"label": label, "t": t})
            if t < 1.0:
                new_event.type = "step"

            window.channel.inbox.put(new_event)

        for task in tasks:
            task.add_handler(log_handler)

        return window
