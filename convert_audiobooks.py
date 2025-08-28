import os
import sys
import re
import ffmpeg

class Hoerbuch:
    def __init__(self, author, title, path):
        self.author = author
        self.title = title
        self.path = path
        self.avg_bitrate = 0
        self.min_bitrate = 0
        self.max_bitrate = 0
        self.channel_layout = 'UNDEFINED'
        self.mp3_files = self._find_mp3_files()

    def _find_mp3_files(self):
        mp3_files = []
        cd_dirs = []
        # Suche nach CD-Verzeichnissen (nur direkte Unterverzeichnisse)
        for entry in os.listdir(self.path):
            full_path = os.path.join(self.path, entry)
            if os.path.isdir(full_path):
                cd_dirs.append(entry)
            elif entry.lower().endswith('.mp3'):
                mp3_files.append((None, entry))

        # Wenn CD-Verzeichnisse existieren, berücksichtige nur mp3s in diesen
        if cd_dirs:
            cd_dirs_sorted = sorted(cd_dirs)
            for cd in cd_dirs_sorted:
                cd_path = os.path.join(self.path, cd)
                files = [f for f in os.listdir(cd_path) if f.lower().endswith('.mp3')]
                for f in sorted(files):
                    mp3_files.append((cd, f))
        else:
            # Nur mp3s im Hauptverzeichnis
            mp3_files = [(None, f) for _, f in sorted(mp3_files, key=lambda x: x[1])]

        # Sortiere: erst nach CD-Verzeichnis (None < alles andere), dann nach Dateiname
        mp3_files_sorted = sorted(
            mp3_files,
            key=lambda x: (x[0] if x[0] is not None else '', x[1])
        )
        # Erzeuge vollständige Pfade
        result = []
        for cd, fname in mp3_files_sorted:
            if cd:
                result.append(os.path.join(self.path, cd, fname))
            else:
                result.append(os.path.join(self.path, fname))
        return result

    @staticmethod
    def _normalize_string(s):
        # Ersetze Umlaute und ß
        replacements = {
            'ä': 'ae', 'ö': 'oe', 'ü': 'ue',
            'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
            'ß': 'ss', '.': '_'
        }
        for orig, repl in replacements.items():
            s = s.replace(orig, repl)
        # Ersetze Leerzeichen durch Unterstriche
        s = re.sub(r'\s+', '_', s)
        # Ersetze Punkte durch Unterstriche (falls noch vorhanden)
        s = s.replace('.', '_')
        # Mehrere Unterstriche zu einem Unterstrich
        s = re.sub(r'_+', '_', s)
        return s

    def normalized_title(self):
        return self._normalize_string(self.title)

    def normalized_author(self):
        return self._normalize_string(self.author)

    def check_mp3_properties(self):
        """
        Prüft für alle mp3-Dateien:
        - Sind es wirklich mp3-Dateien?
        - Haben alle die gleiche Bitrate und Kanalanzahl?
        - Liegt die Bitrate unter 96 kbit/s?
        - Sind sie stereo, mono oder joint stereo kodiert?
        Gibt eine Liste von Fehlern und eine Zusammenfassung der Modi zurück.
        """
        errors = []
        channels = set()
        channel_layouts = set()
        sum_bitrates = 0
        checked_files = 0
        max_bitrate = 0
        min_bitrate = 10000

        for mp3 in self.mp3_files:
            try:
                probe = ffmpeg.probe(mp3)
                audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
                if not audio_stream:
                    errors.append(f"{mp3}: Keine Audiospur gefunden.")
                    continue
                codec = audio_stream.get('codec_name', '')
                if codec != "mp3":
                    errors.append(f"{mp3}: ist kein MP3-Stream (gefunden: {codec})")
                bitrate = int(audio_stream.get('bit_rate', 0))
                channel_count = int(audio_stream.get('channels', 0))
                layout = audio_stream.get('channel_layout', '').lower()
                # joint stereo wird meist als "joint_stereo" oder "stereo" kodiert, aber joint stereo ist ein MP3-Feature
                # ffmpeg gibt "joint_stereo" als channel_layout aus, falls erkannt
                kbs = bitrate // 1000 if bitrate else 0
                if max_bitrate < kbs:
                    max_bitrate = kbs
                if min_bitrate > kbs and kbs > 0:
                    min_bitrate = kbs
                sum_bitrates += kbs
                channels.add(channel_count)
                channel_layouts.add(layout)
                checked_files += 1
            except Exception as e:
                errors.append(f"{mp3}: Fehler beim Prüfen: {e}")

        if len(channels) > 1:
            errors.append(f"Unterschiedliche Kanalanzahlen gefunden: {sorted(channels)}")
        if len(channel_layouts) > 1:
            errors.append(f"Unterschiedliche Kanal-Modi gefunden: {sorted(channel_layouts)}")
        
        if len(errors) == 0 and checked_files > 0:
            self.avg_bitrate = sum_bitrates // checked_files
            self.min_bitrate = min_bitrate
            self.max_bitrate = max_bitrate
            self.channel_layout = channel_layouts.pop()
        return errors, channel_layouts

def finde_alle_hoerbuecher(root_path):
    hoerbuecher = []
    for letter in os.listdir(root_path):
        letter_path = os.path.join(root_path, letter)
        if not os.path.isdir(letter_path):
            continue
        for author in os.listdir(letter_path):
            author_path = os.path.join(letter_path, author)
            if not os.path.isdir(author_path):
                continue
            for book in os.listdir(author_path):
                book_path = os.path.join(author_path, book)
                if not os.path.isdir(book_path):
                    continue
                hoerbuecher.append(Hoerbuch(author, book, book_path))
    # Sortiere zuerst nach Author, dann nach Titel (beides lexikographisch)
    hoerbuecher.sort(key=lambda h: (h.author, h.title))
    return hoerbuecher

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Aufruf: python convert_audiobooks.py <Wurzelverzeichnis>")
        sys.exit(1)
    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"{root} ist kein Verzeichnis!")
        sys.exit(1)
    hoerbuecher = finde_alle_hoerbuecher(root)
    print(f"Gefundene Hörbücher: {len(hoerbuecher)}")
    h = hoerbuecher[0]
    for h in hoerbuecher:
        
        #for mp3 in h.mp3_files:
        #    print(f"  {mp3}")
        errors, channel_layouts = h.check_mp3_properties()
        if errors:
            print("  Fehler bei MP3-Prüfung:")
            for err in errors:
                print(f"    {err}")
            sys,exit(1)
        print(f"Author: {h.author}, Titel: {h.title}, Average Bitrate: {h.avg_bitrate}, Stero: {h.channel_layout}")