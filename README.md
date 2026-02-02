👾 MyriFetch

MyriFetch is a modern, high-performance ROM manager and downloader designed specifically for the Myrient (Erista) repository. It replaces manual browser downloads with a sleek, dark-mode GUI capable of browsing, queuing, and accelerating downloads via multi-threading.

✨ Features

    🚀 "Hydra" Download Engine: Splits files into 4 parallel chunks (threads) to maximize bandwidth and bypass single-stream speed limits.

    📦 Bulk Queue System: Select multiple games, add them to the queue, and let it run in the background.

    💾 Smart Resume & Integrity: Checks file sizes and stitches parts automatically. Includes a "Cancel" feature for safe stopping.

    🐧 Cross-Platform: Runs natively on Windows (.exe) and Linux (.AppImage).

    🎨 Modern UI: Built with CustomTkinter for a clean, dark-themed interface.

🎮 Supported Platforms

    Sony PlayStation 1, 2, & PSP

    Nintendo GameCube, Wii, 3DS, DS, GBA, SNES

    Sega Dreamcast

    Microsoft Xbox

    And more via the folder browser...

🛠️ Installation & Usage

    Windows

        Download the latest MyriFetch.exe from the [Releases] page.

        Run the executable.

        Select a console, browse, and click Download Selected.

    Linux

        Download the MyriFetch-x86_64.AppImage.

        Make it executable: chmod +x MyriFetch-x86_64.AppImage

        Run ./MyriFetch-x86_64.AppImage.

🏗️ Building from Source

    Requirements: Python 3.10+, pip

    # Clone the repo
    git clone [https://github.com/CrabbieMike/MyriFetch.git](https://github.com/CrabbieMike/MyriFetch.git)
    cd MyriFetch

    # Install dependencies
    pip install -r requirements.txt

    # Run
    python MyriFetch.py


⚠️ Disclaimer

    This software is for archival and preservation purposes only. The developer is not affiliated with Myrient/Erista. Please support the original hardware and developers when possible.
