# 👾 MyriFetch

MyriFetch is a modern, high-performance ROM manager and downloader designed specifically for the Myrient (Erista) repository. It replaces manual browser downloads with a sleek, dark-mode GUI capable of browsing, queuing, and accelerating downloads via multi-threading.

## ✨ Features

* 🚀 **"Hydra" Download Engine**: Splits files into 4 parallel chunks (threads) to maximize bandwidth and bypass single-stream speed limits.
* 📦 **Bulk Queue System**: Select multiple games, add them to a 100-item batch queue, and let it run in the background.
* 🏆 **RetroAchievements Integration**: Connect your RA account to view your profile stats, points, and rank directly within the app.
* 🎨 **IGDB Metadata & Box Art**: Integrated with Twitch/IGDB API to automatically fetch high-quality box art, descriptions, genres, and release dates for your library.
* 💾 **Smart Resume & Integrity**: Checks file sizes and stitches parts automatically. Includes "Pause," "Resume," and "Stop" features for safe download management.
* 📂 **Library Manager**: Scan your local folders to view your collection, see what you're missing, and open file locations directly from the app.
* 🛠️ **BIOS Downloader**: One-click downloads for essential RetroArch and emulator BIOS packs.
* 🐧 **Cross-Platform**: Runs natively on Windows, Linux, and macOS.

## 🎮 Supported Platforms

* Sony PlayStation 1, 2, 3 & PSP
* Nintendo GameCube, Wii, 3DS, DS, GBA, SNES
* Sega Dreamcast
* Microsoft Xbox
* And more via the custom folder browser...

<img width="1102" height="882" alt="Screenshot 2026-02-14 163818" src="https://github.com/user-attachments/assets/7dfea677-7204-4ffe-bdfb-9f9e58d4e487" />
<img width="1102" height="882" alt="Screenshot 2026-02-14 163849" src="https://github.com/user-attachments/assets/cc7948ba-8a59-4765-9c18-576fe383f4b2" />
<img width="1102" height="882" alt="Screenshot 2026-02-14 164026" src="https://github.com/user-attachments/assets/9f3029d6-f60d-4804-a5cc-b354d0aa7b1e" />
<img width="1102" height="882" alt="Screenshot 2026-02-14 164130" src="https://github.com/user-attachments/assets/944dfa55-5d21-43cb-b7b6-e2f69548f068" />
<img width="1102" height="882" alt="Screenshot 2026-02-14 164141" src="https://github.com/user-attachments/assets/e1d6be2b-4417-4d70-851b-ab6554f05199" />
<img width="1102" height="882" alt="Screenshot 2026-02-14 164207" src="https://github.com/user-attachments/assets/f7ab9403-26c5-490c-9b6e-44087a6d0363" />
<img width="1102" height="882" alt="Screenshot 2026-02-14 164214" src="https://github.com/user-attachments/assets/13a07311-a4d2-4652-bf7c-9353fe42ec32" />

## 🛠️ Installation & Usage

### Windows

1. Download the latest `MyriFetch-Windows.exe` from the [Releases] page.
2. Run the executable.
3. **Setup**: Go to **Settings** to map your console folders and enter your Twitch/RA API keys for the full experience.

### Linux

1. Download `MyriFetch-Linux-Appimage.AppImage`.
2. Make it executable: `chmod +x MyriFetch-Linux-Appimage.AppImage`.
3. Run `MyriFetch-Linux-Appimage.AppImage`.
4. **Setup**: Go to **Settings** to map your console folders and enter your Twitch/RA API keys for the full experience.

### macOS

1. Download `MyriFetch-macOS`.
2. Open your terminal and navigate to the download location.
3. Make the script executable: `chmod +x MyriFetch-macOS`.
4. Run the script: `./MyriFetch-macOS`.
5. **Setup**: Go to **Settings** to map your console folders and enter your Twitch/RA API keys for the full experience.

## 🏗️ Building from Source

**Requirements**: Python 3.10+, pip

```bash
# Clone the repo
git clone https://github.com/CrabbieMike/MyriFetch.git
cd MyriFetch

# Install dependencies
pip install -r requirements.txt

# Run
python MyriFetch.py

```

## ⚙️ Advanced Customization

The **Settings** menu allows you to:

* **Theme Switching**: Choose between Cyber Dark, Nord, Gruvbox, and Matrix themes.
* **Browser Text Size**: Adjust the UI font size for better readability on high-resolution displays.
* **Content Filters**: Toggle filters for Demos and Revision files to keep your search results clean.
* **Storage Monitoring**: Real-time tracking of free space on your mapped drives.

## ⚠️ Disclaimer

This software is for archival and preservation purposes only. The developer is not affiliated with Myrient/Erista or RetroAchievements. Please support the original hardware and developers when possible.
