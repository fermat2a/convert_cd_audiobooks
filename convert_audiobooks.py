import os
import sys
import re
import time
import ffmpeg
import argparse
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import mutagen
from mutagen.id3 import ID3, TIT2, TPE1, ID3NoHeaderError

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
                    codec_types = []
                    for stream in probe['streams']:
                        codec_types.append(stream['codec_type'])
                        if stream['codec_type'] == 'audio':
                            codec_types.append(stream.get('codec_name', ''))
                    errors.append(f"{mp3}: Keine Audiospur gefunden. codec_types: {codec_types}")
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
            self.channel_layout = channel_layouts.pop() if channel_layouts else 'UNDEFINED'
        return errors

    def convert(self, output_path):
        """
        Konvertiert das gesamte Hörbuch zu einer einzelnen MP3-Datei mit variabler Bitrate (~64 kBit/s).
        Stereomodus: joint stereo falls channel_layout auf stereo schließen lässt, sonst mono.
        Falls avg_bitrate < 70, werden die Daten nur konkateniert, aber nicht neu enkodiert.
        Fügt ID3-Tags für Author und Titel hinzu und übernimmt weitere Tags aus der ersten Quelldatei.
        """
        if not self.mp3_files:
            return ["Keine MP3-Dateien zum Konvertieren gefunden."]

        # Bestimme Stereomodus
        stereo_keywords = {"stereo", "joint_stereo", "stereo_left", "stereo_right"}
        if any(kw in (self.channel_layout or "") for kw in stereo_keywords):
            ac = 2
        else:
            ac = 1

        # Erzeuge temporäre Datei mit allen Inputs als Liste für concat demuxer
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
            for mp3 in self.mp3_files:
                f.write(f"file '{os.path.abspath(mp3)}'\n")
            concat_list = f.name

        try:
            if self.avg_bitrate < 70:
                print(f"Durchschnittliche Bitrate {self.avg_bitrate} kBit/s ist unter 70 kBit/s, daher werden die Dateien nur zusammengefügt, ohne neu zu enkodieren.")
                # Nur zusammenfügen, nicht neu enkodieren
                (
                    ffmpeg
                    .input(concat_list, format='concat', safe=0)
                    .output(
                        output_path,
                        acodec='copy'
                    )
                    .run(overwrite_output=True, quiet=True)
                )
            else:
                print(f"Durchschnittliche Bitrate {self.avg_bitrate} kBit/s ist über 70 kBit/s, daher werden die Dateien neu enkodiert mit ca. 64 kBit/s.")
                # Neu enkodieren mit ca. 64 kBit/s
                (
                    ffmpeg
                    .input(concat_list, format='concat', safe=0)
                    .output(
                        output_path,
                        acodec='libmp3lame',
                        audio_bitrate='64k',
                        ac=ac
                    )
                    .run(overwrite_output=True, quiet=True)
                )
            # ID3-Tags übernehmen und setzen
            merge_id3_tags_from_first_mp3(output_path, self.mp3_files[0], self.author, self.title)
        except Exception as e:
            return [f"Fehler bei der Konvertierung: {e}"]   
        finally:
            os.remove(concat_list)
        return []

def copy_id3_tags(src_file, dst_file, author, title):
    try:
        tags = ID3(src_file)
    except ID3NoHeaderError:
        tags = ID3()
    # Setze/überschreibe Author und Titel
    tags["TPE1"] = TPE1(encoding=3, text=author)
    tags["TIT2"] = TIT2(encoding=3, text=title)
    tags.save(dst_file)

def merge_id3_tags_from_first_mp3(output_path, first_mp3, author, title):
    try:
        tags = ID3(first_mp3)
    except ID3NoHeaderError:
        tags = ID3()
    tags["TPE1"] = TPE1(encoding=3, text=author)
    tags["TIT2"] = TIT2(encoding=3, text=title)
    tags.save(output_path)

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

def parse_args():
    parser = argparse.ArgumentParser(
        description="Werkzeug zur Überprüfung und Konvertierung von MP3-Hörbüchern.\n"
                    "Standardmäßig werden alle Hörbücher im angegebenen Wurzelverzeichnis geprüft.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "wurzelverzeichnis",
        help="Wurzelverzeichnis, in dem die Hörbuch-Ordnerstruktur liegt"
    )
    parser.add_argument(
        "-j", type=int, help="Anzahl paralleler Jobs für die Verarbeitung, wenn nichts angegeben wird, dann wird versucht die Anzahl der CPU Kerne zu ermitteln und dieser Wert +1 verwendet. Kann die Anzahl der Kerne nicht ermittelt werden, dann wird 2 verwendet."
    )
    parser.add_argument(
        "--nocheck", action="store_true",
        help="MP3-Prüfungen überspringen"
    )
    parser.add_argument(
        "--convert-to", type=str,
        help="Konvertiere alle Hörbücher in das angegebene Zielverzeichnis (Dateien werden in einzelne MP3 exportiert, ca. 64 kBit/s)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    root = args.wurzelverzeichnis
    if not os.path.isdir(root):
        print(f"{root} ist kein Verzeichnis!")
        sys.exit(1)
    hoerbuecher = finde_alle_hoerbuecher(root)
    print(f"Gefundene Hörbücher: {len(hoerbuecher)}")

    # Bestimme Anzahl der Jobs
    if args.j is not None:
        num_jobs = args.j
    else:
        try:
            num_jobs = os.cpu_count() + 1
        except Exception:
            num_jobs = 2

    results = []
    if not args.nocheck:
        def job_check(h):
            start = time.time()
            errors = h.check_mp3_properties()
            end = time.time()
            elapsed_ms = int((end - start) * 1000)
            print(f"[Done] Author: {h.author}, Titel: {h.title}, Needed: {elapsed_ms} ms")
            return (h, errors)

        # Parallel ausführen
        with ThreadPoolExecutor(max_workers=num_jobs) as executor:
            futures = {executor.submit(job_check, h): h for h in hoerbuecher}
            for future in as_completed(futures):
                h, errors = future.result()
                results.append((h, errors))

        print("Found errors:")
        found_errors = False
        for result in results:
            h = result[0]
            errors = result[1]
            if errors:
                found_errors = True
                print(f"- Author: {h.author}, Titel: {h.title}, Average Bitrate: {h.avg_bitrate}, Stereo: {h.channel_layout}")
                print("    Fehler bei MP3-Prüfung:")
                for err in errors:
                    print(f"     - {err}")
        if found_errors:
            sys.exit(1)
    
    results = []
    if args.convert_to:
        if not os.path.isdir(args.convert_to):
            print(f"{args.convert_to} ist kein Verzeichnis!")
            sys.exit(1)

        def job_run(h):
            start = time.time()
            authorpath = os.path.join(args.convert_to, f"{h.normalized_author()}")
            os.makedirs(authorpath, exist_ok=True)
            filepath = os.path.join(authorpath, f"{h.normalized_title()}.mp3")
            if os.path.exists(filepath):
                print(f"Skipping conversion for {h.author} - {h.title} into {filepath}, file already exists.")
                return (h, filepath, [f"Skipping conversion for {h.author} - {h.title} into {filepath}, file already exists."])
            errors = h.convert(filepath)
            end = time.time()
            elapsed_ms = int((end - start) * 1000)
            print(f"[Done] Converting Author: {h.author}, Titel: {h.title}, into {filepath}, Needed: {elapsed_ms} ms")
            return (h, filepath, errors)
        
        with ThreadPoolExecutor(max_workers=num_jobs) as executor:
            futures = {executor.submit(job_run, h): h for h in hoerbuecher}
            for future in as_completed(futures):
                h, filepath, errors = future.result()
                results.append((h, filepath, errors))


        for h, filepath, errors in results:
            if errors:
                print(f"Skipping conversion for {h.author} - {h.title} into {filepath} due to errors:")
                for err in errors:
                    print(f"     - {err}")

if __name__ == "__main__":
    main()