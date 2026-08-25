import unittest
from src.chapter import normalize_chapter_number, compare_chapters, is_newer_chapter


class TestChapter(unittest.TestCase):

    def test_normalize_chapter_number(self):
        # Test various chapter formats
        self.assertEqual(normalize_chapter_number("第120話"), 120.0)
        self.assertEqual(normalize_chapter_number("第01話"), 1.0)
        self.assertEqual(normalize_chapter_number("第001話"), 1.0)
        self.assertEqual(normalize_chapter_number("Chapter 12"), 12.0)
        self.assertEqual(normalize_chapter_number("chapter 13"), 13.0)
        self.assertEqual(normalize_chapter_number("12.5話"), 12.5)
        self.assertEqual(normalize_chapter_number("第12話＋番外篇"), 12.0)
        self.assertEqual(normalize_chapter_number("第12話 更新"), 12.0)
        self.assertEqual(normalize_chapter_number("chap 5"), 5.0)
        self.assertEqual(normalize_chapter_number("話100"), 100.0)
        self.assertIsNone(normalize_chapter_number(""))
        self.assertIsNone(normalize_chapter_number("invalid"))

    def test_compare_chapters(self):
        # Test chapter comparisons, including 9 < 10 issue
        self.assertEqual(compare_chapters("第10話", "第9話"), 1)  # current > previous
        self.assertEqual(compare_chapters("第9話", "第10話"), -1)  # current < previous
        self.assertEqual(compare_chapters("第120話", "第119話"), 1)  # current > previous
        self.assertEqual(compare_chapters("第120話", "第120話"), 0)  # current == previous
        self.assertEqual(compare_chapters("第119話", "第120話"), -1)  # current < previous
        self.assertEqual(compare_chapters("Chapter 12.5", "Chapter 12"), 1)  # decimal comparison
        self.assertEqual(compare_chapters("第02話", "第2話"), 0)  # zero padding is same

    def test_is_newer_chapter(self):
        # Test newer chapter detection
        self.assertTrue(is_newer_chapter("第121話", "第120話"))
        self.assertFalse(is_newer_chapter("第120話", "第120話"))
        self.assertFalse(is_newer_chapter("第119話", "第120話"))
        self.assertTrue(is_newer_chapter("第10話", "第9話"))

    def test_unparseable_chapters_return_none(self):
        self.assertIsNone(compare_chapters("番外篇", "第1話"))
        self.assertIsNone(compare_chapters("第1話", "番外篇"))
        self.assertIsNone(compare_chapters("", "第1話"))


if __name__ == '__main__':
    unittest.main()