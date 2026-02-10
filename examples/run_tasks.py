from pathlib import Path

from ftl import tasks
from ftl.settings import get_settings

# fmt: off
sources = [
    Path("data/quadtrees_v19.quadtrees_var1_30_4/quadtrees_v19.quadtrees_var1_30_4.%04d.png"),
    Path("data/quadtrees_v20.quadtrees_var3_10_10/quadtrees_v20.quadtrees_var3_10_10.%04d.png"),
    Path("data/strokes_square/strokes_square.%04d.exr"),
    Path("data/strokes_169/strokes_169.%04d.exr"),
    Path("data/strokes_916/strokes_916.%04d.exr"),
    Path("data/quadtrees_square/quadtrees_square.%04d.png"),
    Path("data/quadtrees_169/quadtrees_169.%04d.png"),
    Path("data/quadtrees_916/quadtrees_916.%04d.png"),
]
# fmt: on

# src = sources[4]
# dst = Path(".") / (src.stem.split(".")[0] + ".mov")
# print(src, dst)


# tasks.EncodeMov(src, dst, fps=24, max_size=720)()
# tasks.EncodeMp4(src, dst.with_suffix(".mp4"), fps=24, max_size=720)()
# tasks.EncodeGif(src, dst.with_suffix(".gif"), fps=24, max_size=512, max_colors=256)()

src = sources[-1]
for path in Path("data").iterdir():
    if path.is_file():
        continue

    task = tasks.EncodeFolder(path, get_settings())
    task()
    print(task.status)
    print(task.result)
    print(task.error)
