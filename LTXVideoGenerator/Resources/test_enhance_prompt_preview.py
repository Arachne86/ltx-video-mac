import unittest
import re
import sys
import os

# Add the current directory to sys.path to allow importing enhance_prompt_preview
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhance_prompt_preview import _clean_response

class TestCleanResponse(unittest.TestCase):
    def test_normal_string(self):
        """Test that a normal string is returned as-is."""
        self.assertEqual(_clean_response("A beautiful sunset over the ocean"), "A beautiful sunset over the ocean")

    def test_whitespace(self):
        """Test that leading and trailing whitespace are removed."""
        self.assertEqual(_clean_response("  A beautiful sunset  "), "A beautiful sunset")
        self.assertEqual(_clean_response("\nA beautiful sunset\t"), "A beautiful sunset")

    def test_leading_special_characters(self):
        """Test that leading special characters are removed."""
        self.assertEqual(_clean_response("!!!A beautiful sunset"), "A beautiful sunset")
        self.assertEqual(_clean_response("...A beautiful sunset"), "A beautiful sunset")
        # Improved: space after special characters should be removed
        self.assertEqual(_clean_response("### A beautiful sunset"), "A beautiful sunset")

    def test_only_special_characters(self):
        """Test that a string of only special characters returns an empty string."""
        self.assertEqual(_clean_response("!!!"), "")
        self.assertEqual(_clean_response("..."), "")
        self.assertEqual(_clean_response("###"), "")

    def test_empty_and_whitespace_only(self):
        """Test that empty or whitespace-only strings return an empty string."""
        self.assertEqual(_clean_response(""), "")
        self.assertEqual(_clean_response("   "), "")
        self.assertEqual(_clean_response("\n\n"), "")

    def test_unicode_emojis(self):
        """Test how Unicode emojis at the start are handled."""
        # Improved: space after emoji should be removed
        self.assertEqual(_clean_response("✨ A beautiful sunset"), "A beautiful sunset")

        # Emojis in the middle should be preserved
        self.assertEqual(_clean_response("A beautiful ✨ sunset"), "A beautiful ✨ sunset")

    def test_combinations(self):
        """Test combinations of whitespace and special characters."""
        # Improved: " !!!  Hello " -> "Hello"
        self.assertEqual(_clean_response(" !!!  Hello "), "Hello")

        # " ...   " -> strip() -> "..." -> re.sub -> ""
        self.assertEqual(_clean_response(" ...   "), "")

if __name__ == "__main__":
    unittest.main()
