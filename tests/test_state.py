import unittest
import tempfile
import os
from src.state import StateManager


class TestStateManager(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.state_manager = StateManager(self.temp_file.name)
    
    def tearDown(self):
        # Clean up the temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_initial_empty_state(self):
        # Test that initial state is empty
        self.assertEqual(self.state_manager.state_data, {})
    
    def test_update_and_get_latest_chapter(self):
        # Test updating and retrieving chapter
        manga_name = "Test Manga"
        chapter = "第1話"
        url = "http://example.com"
        
        self.state_manager.update_manga(manga_name, chapter, url)
        
        retrieved = self.state_manager.get_latest_chapter(manga_name)
        self.assertEqual(retrieved, chapter)
    
    def test_has_updated_first_time(self):
        # Test first-time check (should not be considered an update)
        manga_name = "Test Manga"
        current_chapter = "第1話"
        
        has_updated, previous = self.state_manager.has_updated(manga_name, current_chapter)
        self.assertFalse(has_updated)
        self.assertIsNone(previous)
    
    def test_has_updated_with_change(self):
        # Test actual update detection
        manga_name = "Test Manga"
        old_chapter = "第1話"
        new_chapter = "第2話"
        
        # First, record the old chapter (simulating first run)
        self.state_manager.update_manga(manga_name, old_chapter, "http://example.com")
        
        # Then check with new chapter
        has_updated, previous = self.state_manager.has_updated(manga_name, new_chapter)
        
        self.assertTrue(has_updated)
        self.assertEqual(previous, old_chapter)
    
    def test_has_updated_no_change(self):
        # Test when there's no update
        manga_name = "Test Manga"
        chapter = "第1話"
        
        # Record the chapter
        self.state_manager.update_manga(manga_name, chapter, "http://example.com")
        
        # Check with same chapter
        has_updated, previous = self.state_manager.has_updated(manga_name, chapter)
        
        self.assertFalse(has_updated)
        self.assertEqual(previous, chapter)


if __name__ == '__main__':
    unittest.main()