import sys
import os
import shutil
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from convert_all import check_structure

class TestCheckStructure(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def make_file(self, path):
        with open(path, "w") as f:
            f.write("dummy")

    def test_valid_structure_with_mp3(self):
        os.makedirs(os.path.join(self.test_dir, "M", "Max Mustermann", "Mein_Buch1"))
        self.make_file(os.path.join(self.test_dir, "M", "Max Mustermann", "Mein_Buch1", "track1.mp3"))
        errors = check_structure(self.test_dir)
        self.assertEqual(errors, [])

    def test_valid_structure_with_cd_dirs_various_number_positions(self):
        # B/Ben Becker/Mein-Buch.2/01Disk, B/Ben Becker/Mein-Buch.2/Disk02, B/Ben Becker/Mein-Buch.2/Disk 03
        book_dir = os.path.join(self.test_dir, "B", "Ben Becker", "Mein-Buch.2")
        os.makedirs(os.path.join(book_dir, "01Disk"))
        os.makedirs(os.path.join(book_dir, "Disk02"))
        os.makedirs(os.path.join(book_dir, "Disk 03"))
        self.make_file(os.path.join(book_dir, "01Disk", "track1.mp3"))
        self.make_file(os.path.join(book_dir, "Disk02", "track2.mp3"))
        self.make_file(os.path.join(book_dir, "Disk 03", "track3.mp3"))
        errors = check_structure(self.test_dir)
        self.assertEqual(errors, [])

    def test_invalid_letter_dir(self):
        os.makedirs(os.path.join(self.test_dir, "AA"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("kein einzelner Buchstabe" in e for e in errors))

    def test_author_does_not_start_with_letter(self):
        os.makedirs(os.path.join(self.test_dir, "C", "Ben Becker", "Mein_Buch1"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("beginnt nicht mit 'C'" in e for e in errors))

    def test_book_dir_contains_both_mp3_and_cd(self):
        book_dir = os.path.join(self.test_dir, "D", "Dan Brown", "Mein_Buch-4")
        os.makedirs(os.path.join(book_dir, "Disc1"))
        self.make_file(os.path.join(book_dir, "track1.mp3"))
        self.make_file(os.path.join(book_dir, "Disc1", "track2.mp3"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("sowohl mp3-Dateien als auch CD-Verzeichnisse" in e for e in errors))

    def test_cd_dir_without_mp3(self):
        cd_dir = os.path.join(self.test_dir, "E", "Eva Musterfrau", "Mein_Buch5", "1")
        os.makedirs(cd_dir)
        errors = check_structure(self.test_dir)
        self.assertTrue(any("enthält keine mp3-Dateien" in e for e in errors))

    def test_book_dir_without_mp3_or_cd(self):
        os.makedirs(os.path.join(self.test_dir, "F", "Felix Müller", "Mein_Buch6"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("weder mp3-Dateien noch CD-Verzeichnisse" in e for e in errors))

    def test_cd_dir_with_one_subdir_with_mp3(self):
        cd_subdir = os.path.join(self.test_dir, "G", "Gregor Gysi", "Mein_Buch7", "Disc1", "sub")
        os.makedirs(cd_subdir)
        self.make_file(os.path.join(cd_subdir, "track1.mp3"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("aber ein Unterverzeichnis mit mp3-Dateien" in e for e in errors))
        cd_dir = os.path.join(self.test_dir, "G", "Gregor Gysi", "Mein_Buch7", "Disc1")
        book_dir = os.path.join(self.test_dir, "G", "Gregor Gysi", "Mein_Buch7")
        errors = check_structure(self.test_dir, try_fix=True)
        self.assertFalse(any("enthält keine mp3-Dateien" in e for e in errors))
        self.assertTrue(os.path.isfile(os.path.join(book_dir, "track1.mp3")))
        self.assertFalse(os.path.exists(cd_subdir))
        self.assertFalse(os.path.exists(cd_dir))

    def test_cd_dir_with_multiple_subdirs_with_mp3(self):
        cd1_dir = os.path.join(self.test_dir, "H", "Hugo Boss", "Mein_Buch8", "1")
        cd2_dir = os.path.join(self.test_dir, "H", "Hugo Boss", "Mein_Buch8", "2")
        os.makedirs(os.path.join(cd1_dir, "sub1"))
        os.makedirs(os.path.join(cd1_dir, "sub2"))
        os.makedirs(os.path.join(cd2_dir, "sub1"))
        self.make_file(os.path.join(cd1_dir, "sub1", "track1.mp3"))
        self.make_file(os.path.join(cd1_dir, "sub2", "track2.mp3"))
        self.make_file(os.path.join(cd2_dir, "sub1", "track1.mp3"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("enthält keine mp3-Dateien" in e for e in errors))
        errors = check_structure(self.test_dir, try_fix=True)
        self.assertTrue(any("enthält keine mp3-Dateien" in e for e in errors))
        self.assertTrue(os.path.isfile(os.path.join(cd1_dir, "sub1", "track1.mp3")))
        self.assertTrue(os.path.isfile(os.path.join(cd1_dir, "sub2", "track2.mp3")))

    def test_cd_dirs_must_have_number_and_same_base(self):
        # I/Ingo Meier/Mein_Buch9/01Disk, 02Disk, DiskA
        book_dir = os.path.join(self.test_dir, "I", "Ingo Meier", "Mein_Buch9")
        os.makedirs(os.path.join(book_dir, "01Disk"))
        os.makedirs(os.path.join(book_dir, "02Disk"))
        os.makedirs(os.path.join(book_dir, "DiskA"))
        self.make_file(os.path.join(book_dir, "01Disk", "track1.mp3"))
        self.make_file(os.path.join(book_dir, "02Disk", "track2.mp3"))
        self.make_file(os.path.join(book_dir, "DiskA", "trackA.mp3"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("CD-Verzeichnisname enthält keine Zahl" in e for e in errors))

    def test_cd_dirs_numbers_must_be_consecutive(self):
        # J/Jana Müller/Mein_Buch10/Part1, Part3
        book_dir = os.path.join(self.test_dir, "J", "Jana Müller", "Mein_Buch10")
        os.makedirs(os.path.join(book_dir, "Part1"))
        os.makedirs(os.path.join(book_dir, "Part3"))
        self.make_file(os.path.join(book_dir, "Part1", "track1.mp3"))
        self.make_file(os.path.join(book_dir, "Part3", "track3.mp3"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("CD-Verzeichnisnummern sind nicht fortlaufend ab 1" in e for e in errors))

    def test_cd_dirs_bases_must_be_identical(self):
        # K/Karl Heinz/Mein_Buch11/01CD, 02Disk
        book_dir = os.path.join(self.test_dir, "K", "Karl Heinz", "Mein_Buch11")
        os.makedirs(os.path.join(book_dir, "01CD"))
        os.makedirs(os.path.join(book_dir, "02Disk"))
        self.make_file(os.path.join(book_dir, "01CD", "track1.mp3"))
        self.make_file(os.path.join(book_dir, "02Disk", "track2.mp3"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("CD-Verzeichnisnamen unterscheiden sich abgesehen von der Zahl" in e for e in errors))

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
        # Testet das rekursive Entpacken von Einzelverzeichnissen im Hörbuchverzeichnis mit --tryFix
        author = "Max Mustermann"
        book = "Mein_Buch15"
        test_dir = tempfile.mkdtemp()
        try:
            book_dir = os.path.join(test_dir, author[0], author, book)
            os.makedirs(book_dir)
            # Erzeuge verschachtelte Einzelverzeichnisse: .../book/1/2/3/track1.mp3
            deep_dir = os.path.join(book_dir, "1", "2", "3")
            os.makedirs(deep_dir)
            self.make_file(os.path.join(deep_dir, "track1.mp3"))
            # Vor dem Fix: track1.mp3 ist tief verschachtelt
            self.assertFalse(os.path.exists(os.path.join(book_dir, "track1.mp3")))
            check_structure(test_dir, try_fix=True)
            # Nach dem Fix: track1.mp3 sollte direkt im book_dir liegen, alle Zwischenverzeichnisse entfernt
            self.assertTrue(os.path.exists(os.path.join(book_dir, "track1.mp3")))
            # Es sollte keine weiteren Unterverzeichnisse mehr geben
            self.assertFalse(any(os.path.isdir(os.path.join(book_dir, d)) for d in os.listdir(book_dir)))
        finally:
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    unittest.main()