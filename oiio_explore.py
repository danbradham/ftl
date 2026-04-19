from rich import print

from ftl import files, tasks

file = files.ls("D:/dev/projects/ftl/data/replit_logo_A_v01sm")[0]
task = tasks.OCIODisplay(
    input=file,
    input_transform="Linear Rec.709 (sRGB)",
    display_device="sRGB - Display",
    view_transform="ACES 2.0 - SDR 100 nits (Rec.709)",
)
print(task.input)
print(task.output)
print(task.command())
task()
