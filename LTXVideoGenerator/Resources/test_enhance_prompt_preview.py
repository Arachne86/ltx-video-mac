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

from enhance_prompt_preview import _sanitize_prompt, _merge_back

class TestSanitizePrompt(unittest.TestCase):
    def test_sanitize_and_merge(self):
        prompt = "The dead body was covered in blood and gore, but it wasn't naked. Blood was everywhere, and someone was vomiting. More blood. Dead body. Sex."
        sanitized, replacements = _sanitize_prompt(prompt)

        # Check that offensive words are gone
        self.assertNotIn("blood", sanitized.lower())
        self.assertNotIn("gore", sanitized.lower())
        self.assertNotIn("dead body", sanitized.lower())
        self.assertNotIn("naked", sanitized.lower())
        self.assertNotIn("vomiting", sanitized.lower())
        self.assertNotIn("sex", sanitized.lower())

        # Check that placeholders are present
        self.assertTrue(any(ph in sanitized for ph in replacements))

        # Check that merging back restores original prompt
        merged = _merge_back(sanitized, replacements)
        self.assertEqual(prompt, merged)

    def test_no_matches(self):
        prompt = "A beautiful sunset over the ocean."
        sanitized, replacements = _sanitize_prompt(prompt)

        self.assertEqual(prompt, sanitized)
        self.assertEqual(len(replacements), 0)

    def test_partial_word_match(self):
        # "urine" is a target, but "murine" shouldn't be matched
        prompt = "The murine model showed results."
        sanitized, replacements = _sanitize_prompt(prompt)

        self.assertEqual(prompt, sanitized)
        self.assertEqual(len(replacements), 0)

if __name__ == "__main__":
    unittest.main()
