# Convert CD Audiobooks

Some scripts to integrate audiobooks I got into my collection.

## Features

- Check organization of audiofiles
- Can also repair some problems, e.g. with directory names
- Reencode audio files from MP3 into MP3 with my preffered settings
- Organize and tag audiobook files

## Installation

1. **Install dependencies:**

    On Ubuntu/Debian:
    ```bash
    sudo apt update
    sudo apt install lame ffmpeg python3 python3-pip
    ```

2. **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/convert_cd_audiobooks.git
    cd convert_cd_audiobooks
    ```

## Usage

First you can use the virtual environment coming with the code:

    ```bash
    source .venv/bin/activate
    ```

Then you need some libs
    ```bash
    pip3 install mutagen
    pip3 install ffmpeg-python
    ```

You can call the scripts
    ```bash
    python3 chsck_structure.py -h
    python3 convert_cd.py -h
    ```
## Notes

- Make sure you have permission to convert and use the audiobooks.
- See individual script files for advanced options and customization.
