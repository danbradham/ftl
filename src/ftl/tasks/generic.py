import shutil
from dataclasses import dataclass, field
from typing import ClassVar

from ftl.tasks.core import Task


@dataclass
class Delete(Task):
    hidden: ClassVar[bool] = True
    include_parent: bool = field(
        default=False,
        metadata={
            "help": "If True, the parent directory of the input will also be removed.",
        },
    )

    def run(self) -> None:
        if self.include_parent:
            self.log.info(f"Deleting folder: {self.input.path.parent.name}")
        else:
            self.log.info(f"Deleting file: {self.input.name}")

        try:
            if self.include_parent:
                parent = self.input.path.parent
                if parent.exists():
                    shutil.rmtree(parent)
                    self.log.debug("Removed parent directory.")
                else:
                    self.log.warning(
                        "Parent directory does not exist, nothing to remove."
                    )
                return

            if self.input.is_sequence:
                for file in self.input.files:
                    file.unlink(missing_ok=True)
            else:
                self.input.path.unlink(missing_ok=True)

        except Exception as e:
            raise RuntimeError(f"Failed to clean up files: {e}") from e
