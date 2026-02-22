#!/bin/bash

# Direktausführung der Programme mit aktivierter virtueller Umgebung

# Verzeichnis des Skripts ermitteln
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
cd "$SCRIPT_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "Fehler: Virtuelle Umgebung nicht gefunden."
    echo "Führen Sie zuerst ./setup.sh aus, um die Umgebung zu erstellen."
    exit 1
fi

# Aktiviere virtuelle Umgebung
source "$VENV_DIR/bin/activate"

# Hilfsfunktion
show_usage() {
    echo "Verwendung: ./run.sh <Programm> [Argumente]"
    echo
    echo "Verfügbare Programme:"
    echo "  convert        - Startet convert_audiobooks.py"
    echo "  check          - Startet check_structure.py"
    echo "  test           - Führt Tests mit pytest aus"
    echo "  help           - Zeigt diese Hilfe"
    echo
    echo "Beispiele:"
    echo "  ./run.sh convert --help"
    echo "  ./run.sh convert /pfad/zu/hoerbuecher"
    echo "  ./run.sh check /pfad/zu/struktur --tryFix"
    echo "  ./run.sh test"
    echo "  ./run.sh test tests/test_convert_audiobooks.py"
}

# Prüfe Parameter
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

PROGRAM="$1"
shift  # Entferne erstes Argument, Rest sind Parameter für das Programm

case "$PROGRAM" in
    "convert")
        echo "Starte convert_audiobooks.py..."
        python convert_audiobooks.py "$@"
        ;;
    "check")
        echo "Starte check_structure.py..."
        python check_structure.py "$@"
        ;;
    "test")
        echo "Führe Tests aus..."
        if [ $# -eq 0 ]; then
            pytest tests/ -v
        else
            pytest "$@" -v
        fi
        ;;
    "help")
        show_usage
        ;;
    *)
        echo "Unbekanntes Programm: $PROGRAM"
        echo
        show_usage
        exit 1
        ;;
esac