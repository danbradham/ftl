from pathlib import Path

from ftl import tasks

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

sequences = tasks.get_sequences("data/strokes_square")
for sequence in sequences:
    print(sequence)
