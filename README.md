
<p align="center">
    <img src="src/flt/resources/ftl.png"/>
</p>

# ftl
FTL automates the process of converting image sequences into high-quality video formats (mov, mp4, gif) using best practices with minimal configuration. FTL is mainly concerned with streamlining common encoding workflows, rather than providing unlimited flexibility.

<p align="center">
    <img src="media/ftl_demo.gif"/>
</p>

## Latest Release
[![Release](https://img.shields.io/github/release/username/ftl.svg)](https://github.com/username/ftl/releases/latest) v0.1.0

## Key Features
- 🚀 **FFMPEG-powered**: Convert image sequences to mov/mp4/gif with optimal settings
- 🖼️ **Image sequence automation**: Batch process multiple image sequences with a single command
- 📦 **Minimal configuration**: Predefined best practices reduce manual option selection
- 🧰 **CLI & Library**: Use as a command-line tool or integrate into your Python projects
- 🖥️ **GUI**: Provides a graphical user interface for configuring your encoding options
- 🪟 **Windows Integration**: Right-click on a folder containing image sequences and select "Encode Folder" to encode them

## Install
From a terminal:
1. Install [FFMPEG](https://www.ffmpeg.org/download.html).
2. Install [UV](https://docs.astral.sh/uv/getting-started/installation/).
3. Install FTL: `uv tool install [git](git+https://github.com/danbradham/ftl)`
4. Install FTL context menu: (Currently Windows only...)
  `ftl install`

## Workflow (Context Menu)
1. Configure the Encoding Pipline by right clicking on a Folder and opening the Settings dialog. `FTL > Settings`
2. Right click on or in a Folder and encode everything in it! `FTL > Encode Folder`
3. That's it!

## Workflow (CLI)
1. Launch the settings editor `ftl editor`.
2. Encode a folder using `ftl encode`.
3. Encode a folder recursively using `ftl encode --recursive --max-depth=2`
4. Encode a folder by path `ftl encode --path="/path/to/imagesequences"`
5. Yeeehawwww!!

```
❯ ftl --help

 Usage: ftl [OPTIONS] COMMAND [ARGS]...

╭─ Options ──────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                    │
│ --show-completion             Show completion for the current shell, to copy it or         │
│                               customize the installation.                                  │
│ --help                        Show this message and exit.                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────╮
│ set        Set the value of a Setting...                                                   │
│ reset      Reset to defaults...                                                            │
│ settings   Show current settings...                                                        │
│ editor     Launch the Settings Editor...                                                   │
│ encode     Encode a folder of sequences.                                                   │
│ ls         List sequences in a folder.                                                     │
│ install    Install System-Wide context menu commands...                                    │
│ uninstall  Uninstall System-Wide context menu commands...                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
```

## A Loose Roadmap
### Near Term
- Add logging and progress reporting.
- Improve exception handling.
- Expose support for non-image sequences.
  - Convert between video formats
  - Convert to image sequence
### Longer Term
- Add support for OCIO allowing users to specify input and output transforms.

## Contributing
1. Fork the repository and set up the development environment
2. Install dependencies using `uv sync`.
3. Run the test suite with `pytest` to ensure everything works
4. Submit a pull request with your changes
5. Participate in discussions and help improve the project

## References
- [FFmpeg VFX Encoding Guide](https://trac.ffmpeg.org/wiki/Encode/VFX)
- [Encoding Guidelines](https://academysoftwarefoundation.github.io/EncodingGuidelines/Quickstart.html)
- [High-Quality GIF with FFmpeg](https://blog.pkh.me/p/21-high-quality-gif-with-ffmpeg.html)
