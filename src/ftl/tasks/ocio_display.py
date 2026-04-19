import re
from dataclasses import dataclass, field
from typing import ClassVar

from ftl import tools
from ftl.files import File, FileSequence, as_temp
from ftl.tasks.core import Task
from ftl.tasks.generic import RemoveFile


@dataclass
class OCIODisplay(Task):
    hidden: ClassVar[bool] = True
    input_transform: str = field(
        default_factory=tools.get_ocio_default_input_transform,
        metadata={
            "help": "OCIO Input Transform.",
        },
    )
    display_device: str = field(
        default_factory=tools.get_ocio_default_display_device,
        metadata={
            "help": "OCIO Display Device.",
        },
    )
    view_transform: str = field(
        default_factory=tools.get_ocio_default_view_transform,
        metadata={
            "help": "OCIO View Transform.",
        },
    )

    def __post_init__(self):
        super().__post_init__()

        self.output = as_temp(self.input, suffix=".png")
        self.temp_folder = self.output.path.parent

    def cleanup_task(self) -> RemoveFile:
        return RemoveFile(
            input=self.output,
            include_parent=True,
        )

    def _format_file_for_oiio(self, file: File | FileSequence) -> str:
        if isinstance(file, FileSequence):
            return str(file.path).replace(
                file.padding_str, f"{file.frame_start}-{file.frame_end}{file.padding_str}"
            )
        else:
            return str(file.path)

    def frame_to_progress(self, frame):
        if isinstance(self.input, FileSequence):
            return (frame - self.input.frame_start) / (
                self.input.frame_end - self.input.frame_start
            )
        return self.progress

    def parse_stdout(self, line: str):
        print(line)

        match = re.search(r"\.(\d+)\.", line)
        if match:
            frame = int(match.group(1))
            self.set_progress(self.frame_to_progress(frame))

    def command(self) -> list[str]:

        input_file = self._format_file_for_oiio(self.input)
        output_file = self._format_file_for_oiio(self.output)

        # fmt: off
        cmd = [
            tools.get_oiiotool(),
            "-i", input_file,
            "--iscolorspace", self.input_transform,
            "--ociodisplay", self.display_device, self.view_transform,
            "-o", output_file,
        ]
        # fmt: on
        return cmd

    def run(self) -> File | FileSequence:
        # Ensure destination directory exists...
        self.output.path.parent.mkdir(parents=True, exist_ok=True)

        self.log.info(f"{self.input.name} -> {self.output.name}")
        self.log.info("Applying OCIO Output Transform")
        self.log.info(f"Input Transform: {self.input_transform}")
        self.log.info(f"Display Device: {self.display_device}")
        self.log.info(f"View Transform: {self.view_transform}")

        nframes = len(self.output.files)
        framestep = 100.0 / len(self.output.files)
        for i, (input, output) in enumerate(zip(self.input.files, self.output.files)):
            try:
                tools.ocio_display(
                    input,
                    output,
                    self.input_transform,
                    self.display_device,
                    self.view_transform,
                )
                self.set_progress(
                    int(framestep * i),
                    f"Writing frame {i + 1} of {nframes}",
                )
            except Exception as e:
                raise RuntimeError(f"OIIO failed to convert {input}") from e

        return self.output
