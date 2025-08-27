import os
import sys
import re


in_path = "/media/fermat/Seagate Portable Drive/Hörspiele_grosse_Dateien"
out_path = "/media/fermat/Seagate Portable Drive/Hörspiele_converted"


def check_structure(root_path):
    errors = []

    # 1. Ebene: Buchstabenverzeichnisse
    for letter in os.listdir(root_path):
        letter_path = os.path.join(root_path, letter)
        if not os.path.isdir(letter_path):
            errors.append(f"{letter_path} ist kein Verzeichnis (Ebene 1)")
            continue
        if not (len(letter) == 1 and letter.isalpha()):
            errors.append(f"{letter_path} Name ist kein einzelner Buchstabe (Ebene 1)")
            continue

        # 2. Ebene: Authorenverzeichnisse
        for author in os.listdir(letter_path):
            author_path = os.path.join(letter_path, author)
            if not os.path.isdir(author_path):
                errors.append(f"{author_path} ist kein Verzeichnis (Ebene 2)")
                continue
            if not author.lower().startswith(letter.lower()):
                errors.append(f"{author_path} beginnt nicht mit '{letter}' (Ebene 2)")
                continue

            # 3. Ebene: Hörbuchverzeichnisse
            for book in os.listdir(author_path):
                book_path = os.path.join(author_path, book)
                if not os.path.isdir(book_path):
                    errors.append(f"{book_path} ist kein Verzeichnis (Ebene 3)")
                    continue

                # 4. Ebene: mp3-Dateien oder CD-Unterverzeichnisse
                entries = os.listdir(book_path)
                mp3s = [f for f in entries if f.lower().endswith('.mp3')]
                cds = [f for f in entries if os.path.isdir(os.path.join(book_path, f)) and f.lower().startswith('cd')]

                if mp3s and cds:
                    errors.append(f"{book_path} enthält sowohl mp3-Dateien als auch CD-Verzeichnisse (Ebene 4)")
                elif not mp3s and not cds:
                    errors.append(f"{book_path} enthält weder mp3-Dateien noch CD-Verzeichnisse (Ebene 4)")

                # Falls CD-Verzeichnisse vorhanden, prüfen ob sie mp3s enthalten
                for cd in cds:
                    cd_path = os.path.join(book_path, cd)
                    cd_mp3s = [f for f in os.listdir(cd_path) if f.lower().endswith('.mp3')]
                    if not cd_mp3s:
                        errors.append(f"{cd_path} enthält keine mp3-Dateien (Ebene 5)")

    return errors


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Aufruf: python check_audiobook_structure.py <Pfad>")
        sys.exit(1)
    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"{root} ist kein Verzeichnis!")
        sys.exit(1)
    violations = check_structure(root)
    if violations:
        print("Verletzungen der Strukturregeln gefunden:")
        for v in violations:
            print(" -", v)
    else:
        print("Keine Regelverletzungen gefunden.")
