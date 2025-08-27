import os
import sys
import re
import shutil


in_path = "/media/fermat/Seagate Portable Drive/Hörspiele_grosse_Dateien"
out_path = "/media/fermat/Seagate Portable Drive/Hörspiele_converted"


def print_help():
    print("""
Verwendung: python convert_all.py <Pfad> [--tryFix] [-h]

Parameter:
  <Pfad>      Wurzelverzeichnis, das geprüft werden soll.
  --tryFix    Versucht, bestimmte Strukturfehler automatisch zu beheben:
              Wenn in einem CD-Verzeichnis keine mp3-Dateien, aber genau ein Unterverzeichnis mit mp3-Dateien existiert,
              werden die mp3-Dateien in das CD-Verzeichnis verschoben und das Unterverzeichnis ggf. gelöscht.
  -h, --help  Zeigt diese Hilfe an.
""")


def relpath(path, root_path):
    return os.path.relpath(path, root_path)


author_valid_re = re.compile(r'^(?! )[A-Za-zÄÖÜäöüß_\-.]+( [A-Za-zÄÖÜäöüß_\-.]+)+(?! )$')
book_valid_re = re.compile(r'^[A-Za-zÄÖÜäöüß0-9 _\-.]+$')

def check_structure(root_path, try_fix=False):
    errors = []
    for letter in os.listdir(root_path):
        letter_path = os.path.join(root_path, letter)
        if not os.path.isdir(letter_path):
            errors.append(f"{relpath(letter_path, root_path)} ist kein Verzeichnis (Ebene 1)")
            continue
        if not (len(letter) == 1 and letter.isalpha()):
            errors.append(f"{relpath(letter_path, root_path)} Name ist kein einzelner Buchstabe (Ebene 1)")
            continue

        for author in os.listdir(letter_path):
            author_path = os.path.join(letter_path, author)
            check_author_dir(author, author_path, letter, root_path, errors, try_fix)

    return errors

def check_author_dir(author, author_path, letter, root_path, errors, try_fix):
    found_files_in_author = False
    if not os.path.isdir(author_path):
        errors.append(f"{relpath(author_path, root_path)} ist kein Verzeichnis (Ebene 2)")
        return
    if not author.lower().startswith(letter.lower()):
        errors.append(f"{relpath(author_path, root_path)} beginnt nicht mit '{letter}' (Ebene 2)")
        return
    if not author_valid_re.match(author):
        errors.append(f"{relpath(author_path, root_path)} Authorenverzeichnisname enthält ungültige Zeichen oder kein Leerzeichen in der Mitte (Ebene 2)")
        return

    for book in os.listdir(author_path):
        book_path = os.path.join(author_path, book)
        if not os.path.isdir(book_path):
            if not found_files_in_author:
                found_files_in_author = True
                errors.append(f"{relpath(author_path, root_path)} enthält Dateien (Ebene 3)")
            continue
        check_book_dir(book, book_path, author, root_path, errors, try_fix)

def check_book_dir(book, book_path, author, root_path, errors, try_fix):
    if not book_valid_re.match(book):
        errors.append(f"{relpath(book_path, root_path)} Hörbuchverzeichnisname enthält ungültige Zeichen (Ebene 3)")
        return
    if author.lower() in book.lower() or book.lower() in author.lower():
        errors.append(f"{relpath(book_path, root_path)} Name des Authors und des Hörbuchs dürfen sich nicht gegenseitig enthalten (Ebene 3)")
        return

    flatten_single_subdirs(book_path, try_fix)

    entries = os.listdir(book_path)
    mp3s = [f for f in entries if f.lower().endswith('.mp3')]
    cds = [f for f in entries if os.path.isdir(os.path.join(book_path, f))]

    if mp3s and cds:
        errors.append(f"{relpath(book_path, root_path)} enthält sowohl mp3-Dateien als auch CD-Verzeichnisse (Ebene 4)")
    elif not mp3s and not cds:
        errors.append(f"{relpath(book_path, root_path)} enthält weder mp3-Dateien noch CD-Verzeichnisse (Ebene 4)")

    if cds:
        check_cd_dirs(book_path, root_path, errors, cds, try_fix)

def flatten_single_subdirs(book_path, try_fix):
    if not try_fix:
        return
    changed = True
    while changed:
        entries = os.listdir(book_path)
        subdirs = [d for d in entries if os.path.isdir(os.path.join(book_path, d))]
        files = [f for f in entries if os.path.isfile(os.path.join(book_path, f))]
        if len(subdirs) == 1 and not files:
            only_subdir = os.path.join(book_path, subdirs[0])
            for entry in os.listdir(only_subdir):
                src = os.path.join(only_subdir, entry)
                dst = os.path.join(book_path, entry)
                if os.path.exists(dst):
                    continue
                shutil.move(src, dst)
            os.rmdir(only_subdir)
            changed = True
        else:
            changed = False

def check_cd_dirs(book_path, root_path, errors, cds, try_fix):
    cd_numbers = []
    cd_name_bases = set()
    for cd in cds:
        match = re.search(r"(\d+)", cd)
        if not match:
            errors.append(f"{relpath(os.path.join(book_path, cd), root_path)} CD-Verzeichnisname enthält keine Zahl (Ebene 4)")
            continue
        num = match.group(1)
        base = cd[:match.start(1)] + cd[match.end(1):]
        cd_name_bases.add(base.strip().lower())
        try:
            num_int = int(num)
            cd_numbers.append((cd, num_int))
        except ValueError:
            errors.append(f"{relpath(os.path.join(book_path, cd), root_path)} CD-Verzeichnisnummer ist keine gültige Zahl (Ebene 4)")
    if len(cd_name_bases) > 1:
        errors.append(f"{relpath(book_path, root_path)} CD-Verzeichnisnamen unterscheiden sich abgesehen von der Zahl (Ebene 4)")
    if cd_numbers:
        nums = sorted([n for _, n in cd_numbers])
        if nums != list(range(1, len(nums)+1)):
            errors.append(f"{relpath(book_path, root_path)} CD-Verzeichnisnummern sind nicht fortlaufend ab 1 (Ebene 4)")

    for cd in cds:
        cd_path = os.path.join(book_path, cd)
        check_cd_mp3s(cd_path, root_path, errors, try_fix)

def check_cd_mp3s(cd_path, root_path, errors, try_fix):
    cd_mp3s = [f for f in os.listdir(cd_path) if f.lower().endswith('.mp3')]
    if not cd_mp3s:
        subdirs = [d for d in os.listdir(cd_path) if os.path.isdir(os.path.join(cd_path, d))]
        mp3_subdirs = []
        for subdir in subdirs:
            subdir_path = os.path.join(cd_path, subdir)
            subdir_mp3s = [f for f in os.listdir(subdir_path) if f.lower().endswith('.mp3')]
            if subdir_mp3s:
                mp3_subdirs.append((subdir_path, subdir_mp3s))
        if len(mp3_subdirs) == 1 and try_fix:
            subdir_path, subdir_mp3s = mp3_subdirs[0]
            for mp3_file in subdir_mp3s:
                src = os.path.join(subdir_path, mp3_file)
                dst = os.path.join(cd_path, mp3_file)
                shutil.move(src, dst)
            if not os.listdir(subdir_path):
                os.rmdir(subdir_path)
            cd_mp3s = [f for f in os.listdir(cd_path) if f.lower().endswith('.mp3')]
            if not cd_mp3s:
                errors.append(f"{relpath(cd_path, root_path)} enthält nach Fix immer noch keine mp3-Dateien (Ebene 5)")
        elif len(mp3_subdirs) == 1:
            errors.append(f"{relpath(cd_path, root_path)} enthält keine mp3-Dateien, aber ein Unterverzeichnis mit mp3-Dateien (Ebene 5). Mit --tryFix können diese verschoben werden.")
        else:
            errors.append(f"{relpath(cd_path, root_path)} enthält keine mp3-Dateien (Ebene 5)")

    return errors


if __name__ == "__main__":
    try_fix = False
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        print_help()
        sys.exit(0)
    if "--tryFix" in args:
        try_fix = True
        args.remove("--tryFix")
    if len(args) != 1:
        print_help()
        sys.exit(1)
    root = args[0]
    if not os.path.isdir(root):
        print(f"{root} ist kein Verzeichnis!")
        sys.exit(1)
    violations = check_structure(root, try_fix=try_fix)
    if violations:
        print("Verletzungen der Strukturregeln gefunden:")
        for v in sorted(violations):
            print(" -", v)
    else:
        print("Keine Regelverletzungen gefunden.")
