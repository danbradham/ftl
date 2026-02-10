<p align="center">
    <img src="media/ftl.png"/>
</p>

# FTL
FTL streamlines the process of encoding image sequences into video using best practices. FTL is an exercise in minimalism, seeking to keep workflows simple with *juuust* enough options to get the job done correctly.

<p align="center">
    <img src="media/ftl_demo.gif"/>
</p>

## Features
- 🚀 **FFMPEG-powered**: Convert image sequences to mov/mp4/gif with optimal settings
- 🖼️ **Batch Processing**: Batch encode multiple image sequences with a single command
- 📦 **Minimal configuration**: Best practices reduce complexity
- 🧰 **CLI & Library**: Use as a command-line tool or integrate into your Python projects
- 🖥️ **GUI**: Provides a graphical user interface for configuring your encoding options
- 🪟 **Context Menu**: File Browser context menu integration (Windows only at the moment)

## Install
1. Install [FFMPEG](https://www.ffmpeg.org/download.html).
2. Install [UV](https://docs.astral.sh/uv/getting-started/installation/).
3. Install FTL `uv tool install git+https://github.com/danbradham/ftl`
4. Install context menu
  `ftl install`

## Workflow (Context Menu)
1. Right click on or in a folder to access the context menu.
1. Configure the encoding pipeline using the Settings action to launch the Settings editor.
2. Use the Encode action to compress all the image sequences in your folder.
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
- Add logging and progress reporting.
- Improve exception handling.
- Expose support for non-image sequences.
  - Convert between video formats
  - Convert to image sequence
- Add support for OCIO allowing users to specify input and output transforms.
- Add plugin support to allow users to add custom encodings via Python or Preset json files.

## Contribute
1. Fork the repository and set up the development environment
2. Install dependencies using `uv sync`.
3. Submit a pull request with your changes
4. Participate in discussions and help improve the project

## References
- [FFmpeg VFX Encoding Guide](https://trac.ffmpeg.org/wiki/Encode/VFX)
- [Encoding Guidelines](https://academysoftwarefoundation.github.io/EncodingGuidelines/Quickstart.html)
- [High-Quality GIF with FFmpeg](https://blog.pkh.me/p/21-high-quality-gif-with-ffmpeg.html)
