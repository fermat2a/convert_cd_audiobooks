import sys
import os
import shutil
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from convert_audiobooks import Hoerbuch, finde_alle_hoerbuecher

class TestHoerbuch(unittest.TestCase):
    def setUp(self):
        # Temporäres Verzeichnis für jedes Test-Hörbuch
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def make_mp3(self, path):
        with open(path, "w") as f:
            f.write("dummy")

    def test_find_mp3_files_no_cd(self):
        author = "Max Mustermann"
        title = "Mein Buch"
        book_dir = os.path.join(self.temp_dir, author, title)
        os.makedirs(book_dir)
        files = ["a.mp3", "b.mp3", "c.mp3"]
        for f in files:
            self.make_mp3(os.path.join(book_dir, f))
        h = Hoerbuch(author, title, book_dir)
        expected = [os.path.join(book_dir, f) for f in sorted(files)]
        self.assertEqual(h.mp3_files, expected)

    def test_find_mp3_files_with_cd(self):
        author = "Max Mustermann"
        title = "Mein Buch"
        book_dir = os.path.join(self.temp_dir, author, title)
        cd1 = os.path.join(book_dir, "CD01")
        cd2 = os.path.join(book_dir, "CD02")
        os.makedirs(cd1)
        os.makedirs(cd2)
        files_cd1 = ["a1.mp3", "a2.mp3"]
        files_cd2 = ["b1.mp3", "b2.mp3"]
        for f in files_cd1:
            self.make_mp3(os.path.join(cd1, f))
        for f in files_cd2:
            self.make_mp3(os.path.join(cd2, f))
        h = Hoerbuch(author, title, book_dir)
        expected = [os.path.join(cd1, f) for f in sorted(files_cd1)] + [os.path.join(cd2, f) for f in sorted(files_cd2)]
        # Da CDs lexikographisch sortiert werden, CD01 kommt vor CD02
        self.assertEqual(h.mp3_files, expected)

    def test_normalized_author_and_title(self):
        author = "Jörg Übel. Groß"
        title = "Das große Hörbuch. Teil 1"
        book_dir = os.path.join(self.temp_dir, author, title)
        os.makedirs(book_dir)
        h = Hoerbuch(author, title, book_dir)
        self.assertEqual(h.normalized_author(), "Joerg_Uebel_Gross")
        self.assertEqual(h.normalized_title(), "Das_grosse_Hoerbuch_Teil_1")

    def test_finde_alle_hoerbuecher_sortierung(self):
        # Erzeuge mehrere Autoren und Bücher
        os.makedirs(os.path.join(self.temp_dir, "A", "Anna Autorin", "Buch Z"))
        os.makedirs(os.path.join(self.temp_dir, "A", "Anna Autorin", "Buch A"))
        os.makedirs(os.path.join(self.temp_dir, "B", "Bernd Beispiel", "Alpha"))
        os.makedirs(os.path.join(self.temp_dir, "B", "Bernd Beispiel", "Beta"))
        result = finde_alle_hoerbuecher(self.temp_dir)
        # Erwartete Reihenfolge: Anna Autorin Buch A, Anna Autorin Buch Z, Bernd Beispiel Alpha, Bernd Beispiel Beta
        expected = [
            ("Anna Autorin", "Buch A"),
            ("Anna Autorin", "Buch Z"),
            ("Bernd Beispiel", "Alpha"),
            ("Bernd Beispiel", "Beta"),
        ]
        result_tuples = [(h.author, h.title) for h in result]
        self.assertEqual(result_tuples, expected)

if __name__ == "__main__":
    unittest.main()