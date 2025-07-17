"""
Unit tests for the bWell Session Scheduler Generator.

This module contains test cases to verify the correct generation of
schedule files, training plan files, and users list with various configurations.
"""

import json
import os
import shutil
import unittest
from itertools import permutations
from unittest.mock import patch

from generator import main


class TestBwellSchedulegen(unittest.TestCase):
    """Test cases for the bWell session scheduler generator."""

    def setUp(self) -> None:
        """Set up test directories before each test."""
        self.output_dir = "test_output"
        self.schedules_dir = os.path.join(self.output_dir, "schedules")
        self.training_plans_dir = os.path.join(self.output_dir, "training_plans")
        self.users_list_file = os.path.join(self.output_dir, "UsersList.json")
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self) -> None:
        """Clean up test directories after each test."""
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def _verify_training_plan_format(self, filename: str) -> None:
        """
        Verify that a training plan file has the correct format.
        
        Args:
            filename: Name of the training plan file to verify.
        """
        file_path = os.path.join(self.training_plans_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            training_plan = json.load(file)
            
        self.assertIn("sessions", training_plan)
        self.assertEqual(len(training_plan["sessions"]), 1)
        
        session = training_plan["sessions"][0]
        self.assertEqual(session["schedule_file"], filename)
        self.assertEqual(session["repetitions"], "1")

    def _verify_users_list_format(
        self, 
        participant_count: int, 
        prefix: str = ""
    ) -> None:
        """
        Verify that the UsersList.json file has the correct format.
        
        Args:
            participant_count: Expected number of participants.
            prefix: Expected user ID prefix.
        """
        with open(self.users_list_file, 'r', encoding='utf-8') as file:
            users_list = json.load(file)
        
        self.assertIn("users", users_list)
        self.assertEqual(len(users_list["users"]), participant_count)
        
        # Get all training plan filenames in the actual order they appear
        with open(self.users_list_file, 'r', encoding='utf-8') as file:
            users_data = json.load(file)
        
        # Get unique training plans in order of first appearance
        seen_plans = set()
        ordered_plans = []
        for user in users_data["users"]:
            if user["plan"] not in seen_plans:
                ordered_plans.append(user["plan"])
                seen_plans.add(user["plan"])
        
        training_plan_count = len(ordered_plans)
        
        for i, user in enumerate(users_list["users"]):
            self.assertIn("id", user)
            self.assertIn("plan", user)
            
            # Verify user ID format
            expected_number = f"{i:05d}"
            if prefix:
                expected_id = f"{prefix}_{expected_number}"
            else:
                expected_id = expected_number
            self.assertEqual(user["id"], expected_id)
            
            # Verify round-robin assignment using actual order
            expected_plan = ordered_plans[i % training_plan_count]
            self.assertEqual(user["plan"], expected_plan)

    @patch("builtins.input")
    def test_2_4_excl_theater_butterfly(self, mock_input) -> None:
        """Test 2 of 4 scenarios, excluding theater and butterfly."""
        mock_input.side_effect = [
            "mole, lab, theater, butterfly",  # scenarios
            "2",  # length
            "120.0",  # duration
            "theater,butterfly",  # exclusions
            self.output_dir,  # output dir
            "schedule",  # base name
            "",  # user ID prefix (none)
            "25"  # participant count
        ]

        main()

        # Check schedules directory
        schedule_files = os.listdir(self.schedules_dir)
        self.assertEqual(len(schedule_files), 10)

        # Check training plans directory
        training_plan_files = os.listdir(self.training_plans_dir)
        self.assertEqual(len(training_plan_files), 10)
        
        # Verify same files in both directories
        self.assertEqual(set(schedule_files), set(training_plan_files))

        expected_permutations = {
            ("mole", "lab"), ("lab", "mole"),
            ("mole", "theater"), ("theater", "mole"),
            ("mole", "butterfly"), ("butterfly", "mole"),
            ("lab", "theater"), ("theater", "lab"),
            ("lab", "butterfly"), ("butterfly", "lab"),
        }

        expected_filenames = {
            f"schedule_{perm[0]}_{perm[1]}.json"
            for perm in expected_permutations
        }
        self.assertEqual(set(schedule_files), expected_filenames)

        # Verify training plan format
        for filename in training_plan_files:
            self._verify_training_plan_format(filename)

        # Verify users list
        self.assertTrue(os.path.exists(self.users_list_file))
        self._verify_users_list_format(25)

    @patch("builtins.input")
    def test_all_permutations_of_3(self, mock_input) -> None:
        """Test generating all permutations of 3 scenarios."""
        mock_input.side_effect = [
            "mole, lab, theater",  # scenarios
            "3",  # length
            "60.0",  # duration
            "",  # exclusions
            self.output_dir,  # output dir
            "test",  # base name
            "HSJ",  # user ID prefix
            "15"  # participant count
        ]

        main()

        # Check schedules directory
        schedule_files = os.listdir(self.schedules_dir)
        self.assertEqual(len(schedule_files), 6)

        # Check training plans directory
        training_plan_files = os.listdir(self.training_plans_dir)
        self.assertEqual(len(training_plan_files), 6)
        
        # Verify same files in both directories
        self.assertEqual(set(schedule_files), set(training_plan_files))

        scenarios = ["mole", "lab", "theater"]
        expected_permutations = set(permutations(scenarios, 3))
        expected_filenames = {
            f"test_{perm[0]}_{perm[1]}_{perm[2]}.json"
            for perm in expected_permutations
        }
        self.assertEqual(set(schedule_files), expected_filenames)

        # Verify training plan format
        for filename in training_plan_files:
            self._verify_training_plan_format(filename)

        # Verify users list with prefix
        self.assertTrue(os.path.exists(self.users_list_file))
        self._verify_users_list_format(15, "HSJ")

    @patch("builtins.input")
    def test_no_exclusions(self, mock_input) -> None:
        """Test with no exclusions."""
        mock_input.side_effect = [
            "mole, lab",  # scenarios
            "2",  # length
            "10.0",  # duration
            "",  # exclusions
            self.output_dir,  # output dir
            "no_exclusions",  # base name
            "TEST",  # user ID prefix
            "5"  # participant count
        ]

        main()

        # Check schedules directory
        schedule_files = os.listdir(self.schedules_dir)
        self.assertEqual(len(schedule_files), 2)

        # Check training plans directory  
        training_plan_files = os.listdir(self.training_plans_dir)
        self.assertEqual(len(training_plan_files), 2)
        
        # Verify same files in both directories
        self.assertEqual(set(schedule_files), set(training_plan_files))

        scenarios = ["mole", "lab"]
        expected_permutations = set(permutations(scenarios, 2))
        expected_filenames = {
            f"no_exclusions_{perm[0]}_{perm[1]}.json"
            for perm in expected_permutations
        }
        self.assertEqual(set(schedule_files), expected_filenames)

        # Verify training plan format
        for filename in training_plan_files:
            self._verify_training_plan_format(filename)

        # Verify users list with prefix
        self.assertTrue(os.path.exists(self.users_list_file))
        self._verify_users_list_format(5, "TEST")

    @patch("builtins.input")
    def test_round_robin_assignment(self, mock_input) -> None:
        """Test round-robin assignment functionality."""
        # Test the core functions directly instead of through main()
        from generator import generate_users_list_data, generate_user_id
        
        # Test user ID generation
        self.assertEqual(generate_user_id(0, ""), "00000")
        self.assertEqual(generate_user_id(1, ""), "00001")
        self.assertEqual(generate_user_id(0, "TEST"), "TEST_00000")
        self.assertEqual(generate_user_id(1, "TEST"), "TEST_00001")
        
        # Test round-robin assignment
        training_plans = ["plan1.json", "plan2.json"]
        user_details = {"prefix": "", "count": 5}
        
        result = generate_users_list_data(training_plans, user_details)
        
        # Verify structure
        self.assertIn("users", result)
        self.assertEqual(len(result["users"]), 5)
        
        # Verify round-robin assignment
        expected_assignments = [
            {"id": "00000", "plan": "plan1.json"},
            {"id": "00001", "plan": "plan2.json"},
            {"id": "00002", "plan": "plan1.json"},
            {"id": "00003", "plan": "plan2.json"},
            {"id": "00004", "plan": "plan1.json"},
        ]
        
        for i, user in enumerate(result["users"]):
            self.assertEqual(user["id"], expected_assignments[i]["id"])
            self.assertEqual(user["plan"], expected_assignments[i]["plan"])
        
        # Test with prefix
        user_details_with_prefix = {"prefix": "HSJ", "count": 3}
        result_with_prefix = generate_users_list_data(training_plans, user_details_with_prefix)
        
        expected_with_prefix = [
            {"id": "HSJ_00000", "plan": "plan1.json"},
            {"id": "HSJ_00001", "plan": "plan2.json"},
            {"id": "HSJ_00002", "plan": "plan1.json"},
        ]
        
        for i, user in enumerate(result_with_prefix["users"]):
            self.assertEqual(user["id"], expected_with_prefix[i]["id"])
            self.assertEqual(user["plan"], expected_with_prefix[i]["plan"])


if __name__ == "__main__":
    unittest.main() 
