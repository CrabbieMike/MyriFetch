#!/bin/bash

# 0. SAFETY CHECK
if [ ! -f "MyriFetch.py" ]; then
    echo "❌ Error: MyriFetch.py not found in this folder."
    exit 1
fi

# CHANGED: Now checks for MyriFetch.desktop
if [ ! -f "MyriFetch.desktop" ]; then
    echo "❌ Error: MyriFetch.desktop not found in this folder."
    echo "   Please ensure the file is named exactly 'MyriFetch.desktop'"
    exit 1
fi

# 1. SETUP VIRTUAL ENVIRONMENT
echo ">>> 📦 Setting up isolated build environment..."
python3 -m venv build_venv
source build_venv/bin/activate

# 2. INSTALL DEPENDENCIES (Inside venv)
echo ">>> ⬇️  Installing libraries..."
pip install --upgrade pip
pip install pyinstaller pillow requests beautifulsoup4 customtkinter urllib3

# 3. CLEANUP OLD BUILDS
echo ">>> 🧹 Cleaning up old build artifacts..."
rm -rf build dist AppDir *.AppImage

# 4. BUILD EXECUTABLE
echo ">>> 🔨 Compiling with PyInstaller..."
./build_venv/bin/pyinstaller --noconfirm --onedir --windowed --clean \
    --name "MyriFetch" \
    --collect-all customtkinter \
    MyriFetch.py

# 5. PREPARE APPIMAGE STRUCTURE
echo ">>> 📂 Creating AppImage structure..."
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

# Copy the binary folder
cp -r dist/MyriFetch/* AppDir/usr/bin/

# CHANGED: Copies MyriFetch.desktop
cp MyriFetch.desktop AppDir/

# Create a default icon
echo ">>> 🎨 Generating icon..."
convert -size 256x256 xc:#00f2ff AppDir/myrient.png 2>/dev/null || touch AppDir/myrient.png

# Create the AppRun symlink
ln -sr AppDir/usr/bin/MyriFetch AppDir/AppRun

# 6. GET APPIMAGETOOL
if [ ! -f appimagetool-x86_64.AppImage ]; then
    echo ">>> 📥 Downloading AppImageTool..."
    wget -q https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool-x86_64.AppImage
fi

# 7. PACKAGE IT
echo ">>> 📦 Packaging AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir

# 8. CLEANUP VENV
deactivate
rm -rf build_venv

echo ">>> ✅ DONE! Run your app: ./MyriFetch-x86_64.AppImage"
