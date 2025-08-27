import sys
import os
import shutil
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from convert_all import (
    check_structure,
    check_author_dir,
    check_book_dir,
    flatten_single_subdirs,
    check_cd_dirs,
    check_cd_mp3s,
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

    def test_check_book_dir_invalid(self):
        # Testet, dass ein ungültiger Buchname erkannt wird
        test_dir = tempfile.mkdtemp()
        try:
            author = "Max Mustermann"
            book = "Mein!Buch"
            book_path = os.path.join(test_dir, author[0], author, book)
            os.makedirs(book_path)
            errors = []
            check_book_dir(book, book_path, author, test_dir, errors, try_fix=False)
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

if __name__ == "__main__":
    unittest.main()