#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$project_dir"

if ! ldconfig -p 2>/dev/null | grep 'libxcb-cursor.so.0' >/dev/null; then
    echo "Falta la dependencia gráfica libxcb-cursor0. Instálala con:"
    echo "  sudo apt update && sudo apt install libxcb-cursor0"
    exit 1
fi

python3 -m venv .venv-build
source .venv-build/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --clean --noconfirm WeapoGames.spec

echo "Ejecutable creado en: $project_dir/dist/WeapoGames"
