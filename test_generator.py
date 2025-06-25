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

    @patch("builtins.input")
    def test_2_4_excl_theater_butterfly(self, mock_input):
        """Test 2 of 4 scenarios, excluding theater and butterfly."""
        mock_input.side_effect = [
            "mole, lab, theater, butterfly", # scenarios
            "2", # length
            "120.0", # duration
            "theater,butterfly", # exclusions
            self.output_dir, # output dir
            "schedule" # base name
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

        expected_filenames = {f"schedule_{p[0]}_{p[1]}.json" for p in expected_permutations}
        self.assertEqual(set(files), expected_filenames)

    @patch("builtins.input")
    def test_all_permutations_of_3(self, mock_input):
        """Test generating all permutations of 3 scenarios."""
        mock_input.side_effect = [
            "mole, lab, theater", # scenarios
            "3", # length
            "60.0", # duration
            "", # exclusions
            self.output_dir, # output dir
            "test" # base name
        ]

        main()

        files = os.listdir(self.output_dir)
        self.assertEqual(len(files), 6)

        scenarios = ["mole", "lab", "theater"]
        expected_permutations = set(itertools.permutations(scenarios, 3))
        expected_filenames = {f"test_{p[0]}_{p[1]}_{p[2]}.json" for p in expected_permutations}
        self.assertEqual(set(files), expected_filenames)

    @patch("builtins.input")
    def test_no_exclusions(self, mock_input):
        """Test with no exclusions."""
        mock_input.side_effect = [
            "mole, lab", # scenarios
            "2", # length
            "10.0", # duration
            "", # exclusions
            self.output_dir, # output dir
            "no_exclusions" # base name
        ]

        main()

        files = os.listdir(self.output_dir)
        self.assertEqual(len(files), 2)

        scenarios = ["mole", "lab"]
        expected_permutations = set(itertools.permutations(scenarios, 2))
        expected_filenames = {f"no_exclusions_{p[0]}_{p[1]}.json" for p in expected_permutations}
        self.assertEqual(set(files), expected_filenames)


if __name__ == "__main__":
    unittest.main() 
