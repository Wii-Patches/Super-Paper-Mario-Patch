#!/bin/zsh
# Build the standalone GUI patcher app with PyInstaller.
# Output: tools/dist/Super-Paper-Mario-Patcher.app (macOS) or dist/Super-Paper-Mario-Patcher/ (other OSes).
# `wit` is not bundled here -- put it on PATH, or use the CI workflow, which bundles it.
set -eu
cd "${0:a:h}"
command -v pyinstaller >/dev/null || { echo "pyinstaller not found (pip install pyinstaller tkinterdnd2)"; exit 1; }
pyinstaller --noconfirm Super-Paper-Mario-Patcher.spec
echo "built: tools/dist/Super-Paper-Mario-Patcher"
