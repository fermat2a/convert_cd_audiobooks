#!/bin/bash

# Setup-Skript für die virtuelle Umgebung für Audiobook-Konverter
# Erstellt eine venv und installiert alle Abhängigkeiten

echo "=== Audiobook-Konverter Environment Setup ==="
echo

# Prüfung ob Python3 vorhanden ist
if ! command -v python3 &> /dev/null; then
    echo "Fehler: Python3 ist nicht installiert oder nicht im PATH verfügbar."
    echo "Bitte installieren Sie Python 3.8 oder höher."
    exit 1
fi

echo "Python Version: $(python3 --version)"

# Verzeichnis des Skripts ermitteln
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Virtuelle Umgebung erstellen
echo "Erstelle virtuelle Umgebung..."
VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    echo "Virtuelle Umgebung existiert bereits. Lösche alte Umgebung..."
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "Fehler: Konnte virtuelle Umgebung nicht erstellen."
    exit 1
fi

echo "Aktiviere virtuelle Umgebung..."
source "$VENV_DIR/bin/activate"

# Pip upgraden
echo "Upgrade pip..."
pip install --upgrade pip

# Requirements installieren
echo "Installiere Abhängigkeiten..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warnung: requirements.txt nicht gefunden."
fi

# Prüfung der Installation
echo
echo "=== Installationsprüfung ==="
python3 -c "
try:
    import ffmpeg
    print('✓ ffmpeg-python erfolgreich installiert')
except ImportError:
    print('✗ ffmpeg-python fehlt')

try:
    import mutagen
    print('✓ mutagen erfolgreich installiert')
except ImportError:
    print('✗ mutagen fehlt')

try:
    import pytest
    print('✓ pytest erfolgreich installiert')
except ImportError:
    print('✗ pytest fehlt')
"

echo
echo "==================================="
echo "Setup erfolgreich abgeschlossen!"
echo
echo "Verwendung:"
echo "  1. Virtuelle Umgebung aktivieren: source venv/bin/activate"
echo "  2. Programme ausführen:"
echo "     - python convert_audiobooks.py --help"
echo "     - python check_structure.py --help"
echo "  3. Tests ausführen: pytest tests/"
echo "  4. Umgebung deaktivieren: deactivate"
echo
echo "Oder verwenden Sie die vorgefertigten Skripte:"
echo "  - ./activate.sh    - Aktiviert die Umgebung"
echo "  - ./run.sh         - Führt Programme direkt aus"
echo "==================================="