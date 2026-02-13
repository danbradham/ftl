from ftl import resources

FONT_FILE = resources.get("CommitMono.ttf").as_posix()
ICON_FILE = resources.get("ftl.ico").as_posix()
ICON_ENCODE_FILE = resources.get("encode.ico").as_posix()
SIZE_ITEMS = [-1, 256, 512, 768, 1024, 1280, 1920, 2048, 2160, 3840, 4096, 6144]
FPS_ITEMS = [-1, 8, 12, 15, 24, 25, 30, 48, 50, 60]
GIF_SIZE_ITEMS = [-1, 256, 512, 768, 1024, 1280, 1920, 2048, 2160, 3840, 4096, 6144]
GIF_MAXCOLORS_ITEMS = [4, 8, 16, 32, 64, 128, 256]
