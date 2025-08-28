import sys
import os
import shutil
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from check_structure import (
    check_structure,
    check_author_dir,
    check_book_dir,
    flatten_single_subdirs,
    check_cd_dirs,
    check_cd_mp3s,
    author_valid_re,
    book_valid_re,
)

class TestCheckStructure(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def make_file(self, path):
        with open(path, "w") as f:
            f.write("dummy")

    def test_author_name_with_invalid_characters(self):
        cases = [
            ("L!sa Maier", "Mein_Buch12"),
            ("Lisa", "Mein_Buch12"),                # Kein Leerzeichen
            # (" Lisa Maier", "Mein_Buch12"),       # Leerzeichen am Anfang - entfällt, da auf Ebene 1 Fehler
            ("Lisa Maier ", "Mein_Buch12"),         # Leerzeichen am Ende
        ]
        for author, book in cases:
            with self.subTest(author=author):
                test_dir = tempfile.mkdtemp()
                try:
                    os.makedirs(os.path.join(test_dir, author[0], author, book))
                    errors = check_structure(test_dir)
                    self.assertTrue(
                        any("Authorenverzeichnisname enthält ungültige Zeichen" in e or "kein Leerzeichen in der Mitte" in e for e in errors),
                        msg=f"Kein Fehler für ungültigen Authorenverzeichnisnamen '{author}'. Fehlerliste: {errors}"
                    )
                finally:
                    shutil.rmtree(test_dir)

    def test_author_name_with_valid_characters(self):
        cases = [
            ("Max Mustermann", "Mein_Buch13"),
            ("Max-Heinz Mustermann", "Mein_Buch13"),
            ("M. Mustermann", "Mein_Buch13"),
            ("Mäx Müstermann", "Mein_Buch13"),
            ("Özil Götze", "Mein_Buch13"),
            ("Groß Übel", "Mein_Buch13"),
        ]
        for author, book in cases:
            with self.subTest(author=author):
                test_dir = tempfile.mkdtemp()
                try:
                    os.makedirs(os.path.join(test_dir, author[0], author, book))
                    errors = check_structure(test_dir)
                    self.assertFalse(
                        any("Authorenverzeichnisname enthält ungültige Zeichen" in e or "kein Leerzeichen in der Mitte" in e for e in errors),
                        msg=f"Fälschlicher Fehler für gültigen Authorenverzeichnisnamen '{author}'. Fehlerliste: {errors}"
                    )
                finally:
                    shutil.rmtree(test_dir)

    def test_book_dir_single_subdir_flattening(self):
        author = "Max Mustermann"
        book = "Mein_Buch15"
        test_dir = tempfile.mkdtemp()
        try:
            book_dir = os.path.join(test_dir, author[0], author, book)
            os.makedirs(book_dir)
            deep_dir = os.path.join(book_dir, "1", "2", "3")
            os.makedirs(deep_dir)
            self.make_file(os.path.join(deep_dir, "track1.mp3"))
            self.assertFalse(os.path.exists(os.path.join(book_dir, "track1.mp3")))
            flatten_single_subdirs(book_dir, try_fix=True)
            self.assertTrue(os.path.exists(os.path.join(book_dir, "track1.mp3")))
            self.assertFalse(any(os.path.isdir(os.path.join(book_dir, d)) for d in os.listdir(book_dir)))
        finally:
            shutil.rmtree(test_dir)

    def test_check_author_dir_invalid(self):
        # Testet, dass ein ungültiger Author erkannt wird
        test_dir = tempfile.mkdtemp()
        try:
            letter = "L"
            author = "Lisa"
            author_path = os.path.join(test_dir, letter, author)
            os.makedirs(author_path)
            errors = []
            check_author_dir(author, author_path, letter, test_dir, errors, try_fix=False)
            self.assertTrue(
                any("Authorenverzeichnisname enthält ungültige Zeichen" in e or "kein Leerzeichen in der Mitte" in e for e in errors),
                msg=f"Kein Fehler für ungültigen Authorenverzeichnisnamen '{author}'. Fehlerliste: {errors}"
            )
        finally:
            shutil.rmtree(test_dir)

    def test_check_author_dir_tryfix(self):
        # Testet, dass bei --tryFix der Authorname automatisch repariert wird
        test_dir = tempfile.mkdtemp()
        try:
            letter = "A"
            author = "Max_Mustermann"
            author_path = os.path.join(test_dir, letter, author)
            os.makedirs(author_path)
            errors = check_structure(test_dir, try_fix=True)
            fixed_path = os.path.join(test_dir, letter, "Max Mustermann")
            self.assertTrue(
                os.path.isdir(fixed_path),
                msg=f"Authorenverzeichnis '{author}' wurde nicht korrekt repariert zu 'Max Mustermann'."
            )
        finally:
            shutil.rmtree(test_dir)

    def test_check_book_dir_tryfix(self):
        # Testet, dass bei --tryFix der Buchname automatisch repariert wird
        test_dir = tempfile.mkdtemp()
        try:
            author = "Max Mustermann"
            book = "Mein_Buch_17"
            author_dir = os.path.join(test_dir, author[0], author)
            os.makedirs(author_dir)
            book_path = os.path.join(author_dir, book)
            os.makedirs(book_path)
            errors = check_structure(test_dir, try_fix=True)
            fixed_path = os.path.join(author_dir, "Mein Buch 17")
            self.assertTrue(
                os.path.isdir(fixed_path),
                msg=f"Buchverzeichnis '{book}' wurde nicht korrekt repariert zu 'Mein Buch 17'. Erhaltene Fehler: {errors}"
            )
        finally:
            shutil.rmtree(test_dir)

    def test_check_book_dir_invalid(self):
        # Testet, dass ein ungültiger Buchname erkannt wird
        test_dir = tempfile.mkdtemp()
        try:
            author = "Max Mustermann"
            author_path = os.path.join(test_dir, author[0], author)
            book = "Mein!Buch"
            book_path = os.path.join(author_path, book)
            os.makedirs(book_path)
            errors = []
            # KORREKTUR: Argumente anpassen!
            check_book_dir(book, book_path, author, author_path, test_dir, errors, try_fix=False)
            self.assertTrue(any("Hörbuchverzeichnisname enthält ungültige Zeichen" in e for e in errors))
        finally:
            shutil.rmtree(test_dir)

    def test_check_cd_dirs_and_mp3s(self):
        # Testet die CD-Prüfung und das Verschieben von mp3s aus Unterverzeichnissen
        test_dir = tempfile.mkdtemp()
        try:
            author = "Max Mustermann"
            book = "Mein_Buch16"
            book_dir = os.path.join(test_dir, author[0], author, book)
            cd_dir = os.path.join(book_dir, "CD01")
            os.makedirs(cd_dir)
            subdir = os.path.join(cd_dir, "sub")
            os.makedirs(subdir)
            mp3_file = os.path.join(subdir, "track1.mp3")
            self.make_file(mp3_file)
            errors = []
            check_cd_mp3s(cd_dir, test_dir, errors, try_fix=True)
            self.assertTrue(os.path.exists(os.path.join(cd_dir, "track1.mp3")))
            self.assertFalse(os.path.exists(subdir))
        finally:
            shutil.rmtree(test_dir)

    def test_author_and_book_name_containment_error(self):
        # Testet, dass ein Fehler ausgegeben wird, wenn ein beliebiges Wort des Authoren im Buchtitel vorkommt oder umgekehrt
        cases = [
            ("Max Mustermann", "Max Mustermann", True),
            ("Sabine Maier", "Das neue Hörbuch von Sabine Maier", True),
            ("Ralf Richter", "Ralf123 Richter", True),  # "Ralf" und "Richter" kommen als Wortbestandteile vor
            ("Tina Turner", "Das Buch", False),         # Kein Konflikt
            ("Anna Schmidt", "Schmidt Anna", True),     # Beide Wörter gegenseitig enthalten
            ("Peter Lustig", "Peter und der Wolf", True), # "Peter" kommt im Buchtitel vor
            ("Peter Lustig", "Lustige Abenteuer", False),  # "Lustig" als Wortbestandteil im Buchtitel
            ("Karl May", "Winnetou", False),            # Kein Konflikt
        ]
        for author, book, expect_error in cases:
            with self.subTest(author=author, book=book):
                test_dir = tempfile.mkdtemp()
                try:
                    author_dir = os.path.join(test_dir, author[0], author)
                    os.makedirs(author_dir)
                    book_dir = os.path.join(author_dir, book)
                    os.makedirs(book_dir)
                    self.make_file(os.path.join(book_dir, "track1.mp3"))
                    errors = check_structure(test_dir)
                    relevant_error = any(
                        "Name des Authors und des Hörbuchs dürfen sich nicht gegenseitig enthalten" in e
                        for e in errors
                    )
                    if expect_error:
                        self.assertTrue(
                            relevant_error,
                            msg=f"Fehler erwartet für Author='{author}', Buch='{book}', aber nicht gefunden. Fehlerliste: {errors}"
                        )
                    else:
                        self.assertFalse(
                            relevant_error,
                            msg=f"Kein Fehler erwartet für Author='{author}', Buch='{book}', aber gefunden. Fehlerliste: {errors}"
                        )
                finally:
                    shutil.rmtree(test_dir)

    def test_check_cd_dirs(self):
        # Testet verschiedene Fehlerfälle für CD-Verzeichnisse
        test_dir = tempfile.mkdtemp()
        try:
            author = "Max Mustermann"
            book = "Mein_Buch_CD"
            book_dir = os.path.join(test_dir, author[0], author, book)
            os.makedirs(book_dir)

            # Fall 1: CD-Verzeichnis ohne Zahl im Namen
            cd_dir1 = os.path.join(book_dir, "DiscA")
            os.makedirs(cd_dir1)
            errors = []
            check_cd_dirs(book_dir, test_dir, errors, ["DiscA"], try_fix=False)
            self.assertTrue(
                any("CD-Verzeichnisname enthält keine Zahl" in e for e in errors),
                msg=f"Fehler für fehlende Zahl im CD-Verzeichnisnamen nicht erkannt: {errors}"
            )

            # Fall 2: CD-Verzeichnis mit nicht fortlaufenden Nummern
            shutil.rmtree(book_dir)
            os.makedirs(book_dir)
            os.makedirs(os.path.join(book_dir, "CD01"))
            os.makedirs(os.path.join(book_dir, "CD03"))
            errors = []
            check_cd_dirs(book_dir, test_dir, errors, ["CD01", "CD03"], try_fix=False)
            self.assertTrue(
                any("CD-Verzeichnisnummern sind nicht fortlaufend ab 1" in e for e in errors),
                msg=f"Fehler für nicht fortlaufende Nummern nicht erkannt: {errors}"
            )

            # Fall 3: CD-Verzeichnisnamen unterscheiden sich abgesehen von der Zahl
            shutil.rmtree(book_dir)
            os.makedirs(book_dir)
            os.makedirs(os.path.join(book_dir, "CD01"))
            os.makedirs(os.path.join(book_dir, "Disk02"))
            errors = []
            check_cd_dirs(book_dir, test_dir, errors, ["CD01", "Disk02"], try_fix=False)
            self.assertTrue(
                any("CD-Verzeichnisnamen unterscheiden sich abgesehen von der Zahl" in e for e in errors),
                msg=f"Fehler für unterschiedliche Basen nicht erkannt: {errors}"
            )

            # Fall 4: CD-Verzeichnis mit gültigen fortlaufenden Nummern und gleichem Basenamen
            shutil.rmtree(book_dir)
            os.makedirs(book_dir)
            os.makedirs(os.path.join(book_dir, "CD01"))
            os.makedirs(os.path.join(book_dir, "CD02"))
            errors = []
            check_cd_dirs(book_dir, test_dir, errors, ["CD01", "CD02"], try_fix=False)
            self.assertFalse(
                any("CD-Verzeichnisname enthält keine Zahl" in e or
                    "CD-Verzeichnisnummern sind nicht fortlaufend ab 1" in e or
                    "CD-Verzeichnisnamen unterscheiden sich abgesehen von der Zahl" in e
                    for e in errors),
                msg=f"Fälschlicher Fehler für gültige CD-Verzeichnisse: {errors}"
            )
        finally:
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    unittest.main()