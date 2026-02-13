from pathlib import Path

from ftl.files import FileSequence, PathType, ls
from ftl.settings import default_settings
from ftl.tasks.encode_gif import EncodeGif
from ftl.tasks.encode_mov import EncodeMov
from ftl.tasks.encode_mp4 import EncodeMp4


class EncodeFolder(Task):
    def __init__(self, folder: PathType, settings: Settings) -> None:
        super().__init__()
        self.folder = Path(folder)
        self.sequences = [f for f in ls(folder) if isinstance(f, FileSequence)]
        self.settings = default_settings()
        self.settings.update(settings)
        self.prepare_tasks()

    def prepare_tasks(self):
        if not self.sequences:
            raise ValueError(f"No sequences found in '{self.folder}' ...")

        mov_folder = (self.folder / self.settings["mov_folder"]).resolve()
        mp4_folder = (self.folder / self.settings["mp4_folder"]).resolve()
        gif_folder = (self.folder / self.settings["gif_folder"]).resolve()

        task_count = 0
        task_groups = []
        for seq in self.sequences:
            task_group = []
            if self.settings["mov_enabled"]:
                mov_task = EncodeMov(
                    src=seq.path,
                    dst=mov_folder / (seq.stem + ".mov"),
                    fps=self.settings["mov_fps"],
                    max_size=self.settings["mov_size"],
                )
                task_group.append(mov_task)
                task_count += 1
            if self.settings["mp4_enabled"]:
                mp4_task = EncodeMp4(
                    src=seq.path,
                    dst=mp4_folder / (seq.stem + ".mp4"),
                    fps=self.settings["mp4_fps"],
                    max_size=self.settings["mp4_size"],
                )
                task_group.append(mp4_task)
                task_count += 1
            if self.settings["gif_enabled"]:
                gif_task = EncodeGif(
                    src=seq.path,
                    dst=gif_folder / (seq.stem + ".gif"),
                    fps=self.settings["gif_fps"],
                    max_size=self.settings["gif_size"],
                    max_colors=self.settings["gif_colors"],
                )
                task_group.append(gif_task)
                task_count += 1

            task_groups.append(task_group)

        self.task_groups = task_groups
        self.task_count = task_count
        self.log.total = task_count
        self.log(
            f"Found {len(self.task_groups)} file sequences. Prepared {self.task_count} tasks."
        )

    def run(self) -> list[PathType]:

        results = []
        for i, task_group in enumerate(self.task_groups):
            self.log(f"Sequence {i + 1} of {len(self.task_groups)}")
            for task in task_group:
                self.log.step(1)
                task()
                results.append(task.result)

        return results
