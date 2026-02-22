# Convert CD Audiobooks

Some scripts to integrate audiobooks I got into my collection.

## Features

- Check organization of audiofiles
- Can also repair some problems, e.g. with directory names
- Reencode audio files from MP3 into MP3 with my preffered settings
- Organize and tag audiobook files

## Installation

### Automatische Installation (Empfohlen)

1. **Systemvoraussetzungen installieren:**
   ```bash
   sudo apt update
   sudo apt install lame ffmpeg python3 python3-pip python3-venv
   ```

2. **Repository klonen:**
   ```bash
   git clone https://github.com/yourusername/convert_cd_audiobooks.git
   cd convert_cd_audiobooks
   ```

3. **Virtuelle Umgebung automatisch einrichten:**
   ```bash
   ./setup.sh
   ```

Das Setup-Skript erstellt automatisch eine virtuelle Python-Umgebung und installiert alle benötigten Abhängigkeiten.

### Manuelle Installation (Legacy)

Falls Sie die manuelle Installation bevorzugen:

1. **Abhängigkeiten installieren:**
   ```bash
   sudo apt update
   sudo apt install lame ffmpeg python3 python3-pip
   ```

2. **Repository klonen und Python-Pakete installieren:**
   ```bash
   git clone https://github.com/yourusername/convert_cd_audiobooks.git
   cd convert_cd_audiobooks
   pip3 install mutagen ffmpeg-python
   ```

## Verwendung

### Mit den bereitgestellten Skripten (Empfohlen)

Nach dem automatischen Setup können Sie die Programme auf drei Arten verwenden:

1. **Direkte Ausführung mit run.sh:**
   ```bash
   ./run.sh convert --help
   ./run.sh convert /pfad/zu/hoerbuecher
   ./run.sh check /pfad/zu/struktur --tryFix
   ./run.sh test
   ```

2. **Aktivierung der virtuellen Umgebung:**
   ```bash
   ./activate.sh
   python convert_audiobooks.py --help
   python check_structure.py --help
   pytest tests/
   deactivate
   ```

3. **Manuelle Aktivierung:**
   ```bash
   source venv/bin/activate
   python convert_audiobooks.py --help
   python check_structure.py --help
   deactivate
   ```

### Manuelle Verwendung (Legacy)

```bash
python3 check_structure.py -h
python3 convert_audiobooks.py -h
```

## Verfügbare Skripte

- [`setup.sh`](setup.sh) - Erstellt die virtuelle Umgebung und installiert Abhängigkeiten
- [`activate.sh`](activate.sh) - Aktiviert die virtuelle Umgebung
- [`run.sh`](run.sh) - Führt Programme direkt mit aktivierter Umgebung aus
- [`convert_audiobooks.py`](convert_audiobooks.py) - Hauptprogramm für die Audiobook-Konvertierung
- [`check_structure.py`](check_structure.py) - Überprüft und repariert die Ordnerstruktur
## Notes

- Make sure you have permission to convert and use the audiobooks.
- See individual script files for advanced options and customization.
