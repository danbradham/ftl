import OpenImageIO as oiio
from rich import print

config = oiio.ColorConfig()

print("# Color Space Names")
print(config.getColorSpaceNames())

print("# View Names")
print(config.getViewNames())

print("# Displays")
print(config.getDisplayNames())

print("# Roles")
print(config.getRoles())

print("# Views by Display")
for display in config.getDisplayNames():
    print(f"{display}: {config.getViewNames(display)}")
