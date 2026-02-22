#!/bin/bash

# Aktivierungsskript für die virtuelle Umgebung

# Verzeichnis des Skripts ermitteln
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Fehler: Virtuelle Umgebung nicht gefunden."
    echo "Führen Sie zuerst ./setup.sh aus, um die Umgebung zu erstellen."
    exit 1
fi

echo "Aktiviere virtuelle Umgebung für Audiobook-Konverter..."
source "$VENV_DIR/bin/activate"

echo "✓ Virtuelle Umgebung aktiviert"
echo
echo "Verfügbare Programme:"
echo "  - python convert_audiobooks.py [Optionen]"  
echo "  - python check_structure.py [Optionen]"
echo "  - pytest tests/"
echo
echo "Zum Deaktivieren: deactivate"