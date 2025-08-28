import os
import sys
import re

class Hoerbuch:
    def __init__(self, author, title, path):
        self.author = author
        self.title = title
        self.path = path
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
    for h in hoerbuecher:
        print(f"Author: {h.author} -> {h.normalized_author()}, Titel: {h.title} -> {h.normalized_title()}, Pfad: {h.path}")
        for mp3 in h.mp3_files:
            print(f"  {mp3}")