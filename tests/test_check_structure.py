import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import shutil
import tempfile
import unittest

from convert_all import check_structure

class TestCheckStructure(unittest.TestCase):
    def setUp(self):
        # Temporäres Verzeichnis für jeden Test
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Aufräumen nach jedem Test
        shutil.rmtree(self.test_dir)

    def make_file(self, path):
        with open(path, "w") as f:
            f.write("dummy")

    def test_valid_structure_with_mp3(self):
        # A/Author/Book/file.mp3
        os.makedirs(os.path.join(self.test_dir, "A", "AuthorA", "Book1"))
        self.make_file(os.path.join(self.test_dir, "A", "AuthorA", "Book1", "track1.mp3"))
        errors = check_structure(self.test_dir)
        self.assertEqual(errors, [])

    def test_valid_structure_with_cd_dirs(self):
        # B/Ben/Book2/cd1/track1.mp3
        book_dir = os.path.join(self.test_dir, "B", "Ben", "Book2", "CD1")
        os.makedirs(book_dir)
        self.make_file(os.path.join(book_dir, "track1.mp3"))
        errors = check_structure(self.test_dir)
        self.assertEqual(errors, [])

    def test_invalid_letter_dir(self):
        # "AA" ist kein einzelner Buchstabe
        os.makedirs(os.path.join(self.test_dir, "AA"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("kein einzelner Buchstabe" in e for e in errors))

    def test_author_does_not_start_with_letter(self):
        # C/Ben/Book3
        os.makedirs(os.path.join(self.test_dir, "C", "Ben", "Book3"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("beginnt nicht mit 'C'" in e for e in errors))

    def test_book_dir_contains_both_mp3_and_cd(self):
        # D/Dan/Book4/track1.mp3 und D/Dan/Book4/cd1/track2.mp3
        book_dir = os.path.join(self.test_dir, "D", "Dan", "Book4")
        os.makedirs(os.path.join(book_dir, "cd1"))
        self.make_file(os.path.join(book_dir, "track1.mp3"))
        self.make_file(os.path.join(book_dir, "cd1", "track2.mp3"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("sowohl mp3-Dateien als auch CD-Verzeichnisse" in e for e in errors))

    def test_cd_dir_without_mp3(self):
        # E/Eva/Book5/cd1/ (leer)
        cd_dir = os.path.join(self.test_dir, "E", "Eva", "Book5", "cd1")
        os.makedirs(cd_dir)
        errors = check_structure(self.test_dir)
        self.assertTrue(any("enthält keine mp3-Dateien" in e for e in errors))

    def test_book_dir_without_mp3_or_cd(self):
        # F/Felix/Book6/ (leer)
        os.makedirs(os.path.join(self.test_dir, "F", "Felix", "Book6"))
        errors = check_structure(self.test_dir)
        self.assertTrue(any("weder mp3-Dateien noch CD-Verzeichnisse" in e for e in errors))

if __name__ == "__main__":
    unittest.main()