import os
import json
import shutil
import unittest
import itertools
from unittest.mock import patch
from generator import main

class TestBwellSchedulegen(unittest.TestCase):
    def setUp(self):
        self.output_dir = "test_output"
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    @patch("generator.prompt")
    def test_2_4_excl_theater_butterfly(self, mock_prompt):
        """Test 2 of 4 scenarios, excluding theater and butterfly."""
        mock_prompt.side_effect = [
            {"scenarios": ["mole", "lab", "theater", "butterfly"]},
            {"length": 2},
            {"duration": 120.0},
            {"exclusions": ["theater, butterfly"]},
            {"dir": self.output_dir, "basename": "schedule"},
        ]

        main()

        files = os.listdir(self.output_dir)
        self.assertEqual(len(files), 10)

        expected_permutations = {
            ("mole", "lab"), ("lab", "mole"),
            ("mole", "theater"), ("theater", "mole"),
            ("mole", "butterfly"), ("butterfly", "mole"),
            ("lab", "theater"), ("theater", "lab"),
            ("lab", "butterfly"), ("butterfly", "lab"),
        }

        expected_filenames = {f"schedule_{''.join(p)}.json" for p in expected_permutations}
        self.assertEqual(set(files), expected_filenames)

    @patch("generator.prompt")
    def test_all_permutations_of_3(self, mock_prompt):
        """Test generating all permutations of 3 scenarios."""
        mock_prompt.side_effect = [
            {"scenarios": ["mole", "lab", "theater"]},
            {"length": 3},
            {"duration": 60.0},
            {"exclusions": []},
            {"dir": self.output_dir, "basename": "test"},
        ]

        main()

        files = os.listdir(self.output_dir)
        self.assertEqual(len(files), 6)

        scenarios = ["mole", "lab", "theater"]
        expected_permutations = set(itertools.permutations(scenarios, 3))
        expected_filenames = {f"test_{''.join(p)}.json" for p in expected_permutations}
        self.assertEqual(set(files), expected_filenames)

    @patch("generator.prompt")
    def test_no_exclusions(self, mock_prompt):
        """Test with no exclusions."""
        mock_prompt.side_effect = [
            {"scenarios": ["mole", "lab"]},
            {"length": 2},
            {"duration": 10.0},
            {"exclusions": []},
            {"dir": self.output_dir, "basename": "no_exclusions"},
        ]

        main()

        files = os.listdir(self.output_dir)
        self.assertEqual(len(files), 2)

        scenarios = ["mole", "lab"]
        expected_permutations = set(itertools.permutations(scenarios, 2))
        expected_filenames = {f"no_exclusions_{''.join(p)}.json" for p in expected_permutations}
        self.assertEqual(set(files), expected_filenames)


if __name__ == "__main__":
    unittest.main() 
