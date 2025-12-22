"""Unit tests for the bWell Session Scheduler Generator.

This module contains test cases to verify the correct generation of
schedule files, training plan files, and users list with various 
configurations. Tests include validation of the new optimal permutation 
ordering that minimizes repetition through round-robin assignment.
"""

import json
import os
import shutil
import unittest
from unittest.mock import patch

from generator import main


class TestBwellSchedulegen(unittest.TestCase):
    """Test cases for the bWell session scheduler generator."""

    def setUp(self) -> None:
        """Set up test directories before each test."""
        self.output_dir = "test_output"
        self.schedules_dir = os.path.join(self.output_dir, "schedules")
        self.training_plans_dir = os.path.join(
            self.output_dir, "training_plans"
        )
        self.users_list_file = os.path.join(self.output_dir, "UsersList.json")
        
        # Clean up any existing directories first
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        if os.path.exists("./output"):
            shutil.rmtree("./output")
            
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self) -> None:
        """Clean up test directories after each test."""
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        # Also clean up the ./output directory if it exists
        if os.path.exists("./output"):
            shutil.rmtree("./output")

    def _verify_training_plan_format(self, filename: str) -> None:
        """Verify that a training plan file has the correct format.
        
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

    def _run_main_with_inputs(self, inputs: list[str]) -> None:
        """Helper to run main with mocked inputs.
        
        Args:
            inputs: List of input strings to mock.
        """
        with patch('builtins.input', side_effect=inputs):
            main()

    def _load_users_list(self) -> dict[str, list[dict[str, str]]]:
        """Load and return the users list JSON data.
        
        Returns:
            Parsed users list data.
        """
        with open(self.users_list_file, 'r', encoding='utf-8') as file:
            return json.load(file)

    def test_two_scenario_permutations(self) -> None:
        """Test generating permutations with two scenarios."""
        inputs = [
            "mole,lab",  # scenarios
            "2",  # permutation length
            "10.0",  # duration
            "",  # practice scenes (skip)
            "",  # exclusions
            "",  # clinical preferences
            self.output_dir,  # output directory
            "schedule",  # base name
            "u",  # user prefix
            "5",  # digit count
            "25"  # participant count
        ]
        
        self._run_main_with_inputs(inputs)
        
        # Verify files were created
        self.assertTrue(os.path.exists(self.schedules_dir))
        self.assertTrue(os.path.exists(self.training_plans_dir))
        self.assertTrue(os.path.exists(self.users_list_file))
        
        # Verify correct number of files
        schedule_files = os.listdir(self.schedules_dir)
        training_plan_files = os.listdir(self.training_plans_dir)
        
        self.assertEqual(len(schedule_files), 2)
        self.assertEqual(len(training_plan_files), 2)
        
        # Verify users list has correct structure
        users_list = self._load_users_list()
        
        self.assertIn("users", users_list)
        self.assertEqual(len(users_list["users"]), 25)
        
        # Verify round-robin assignment (files are in optimal order now)
        for user in users_list["users"]:
            self.assertIn(user["plan"], training_plan_files)

    def test_three_scenario_permutations(self) -> None:
        """Test generating permutations with three scenarios."""
        inputs = [
            "mole,lab,theater",  # scenarios
            "3",  # permutation length
            "15.0",  # duration
            "",  # practice scenes (skip)
            "",  # exclusions
            "",  # clinical preferences
            self.output_dir,  # output directory
            "test",  # base name
            "",  # user prefix
            "5",  # digit count
            "15"  # participant count
        ]
        
        self._run_main_with_inputs(inputs)
        
        # Verify files were created
        schedule_files = os.listdir(self.schedules_dir)
        training_plan_files = os.listdir(self.training_plans_dir)
        
        self.assertEqual(len(schedule_files), 6)
        self.assertEqual(len(training_plan_files), 6)
        
        # Verify users list
        users_list = self._load_users_list()
        self.assertEqual(len(users_list["users"]), 15)
        
        # Verify round-robin assignment (files are in optimal order now)
        for user in users_list["users"]:
            self.assertIn(user["plan"], training_plan_files)

    def test_partial_permutations(self) -> None:
        """Test generating partial permutations."""
        inputs = [
            "mole,lab,theater",  # scenarios
            "2",  # permutation length
            "5.0",  # duration
            "",  # practice scenes (skip)
            "",  # exclusions
            "",  # clinical preferences
            self.output_dir,  # output directory
            "test",  # base name
            "user",  # user prefix
            "5",  # digit count
            "12"  # participant count
        ]
        
        self._run_main_with_inputs(inputs)
        
        # Verify files were created
        schedule_files = os.listdir(self.schedules_dir)
        training_plan_files = os.listdir(self.training_plans_dir)
        
        self.assertEqual(len(schedule_files), 6)
        self.assertEqual(len(training_plan_files), 6)
        
        # Verify users list
        users_list = self._load_users_list()
        self.assertEqual(len(users_list["users"]), 12)
        
        # Verify user IDs have correct prefix
        for user in users_list["users"]:
            self.assertTrue(user["id"].startswith("user_"))

    def test_exclusions(self) -> None:
        """Test generating permutations with exclusions."""
        inputs = [
            "mole,lab,theater,butterfly",  # scenarios
            "2",  # permutation length
            "7.5",  # duration
            "",  # practice scenes (skip)
            "mole,lab",  # exclusions
            "",  # clinical preferences
            self.output_dir,  # output directory
            "no_exclusions",  # base name
            "",  # user prefix
            "5",  # digit count
            "5"  # participant count
        ]
        
        self._run_main_with_inputs(inputs)
        
        # Verify files were created
        schedule_files = os.listdir(self.schedules_dir)
        training_plan_files = os.listdir(self.training_plans_dir)
        
        # Should have 12 total minus exclusions
        self.assertLess(len(schedule_files), 12)
        self.assertLess(len(training_plan_files), 12)
        
        # Verify no excluded combinations were created
        for filename in schedule_files:
            self.assertFalse(
                ("mole" in filename and "lab" in filename),
                f"Excluded combination found in {filename}"
            )

    def test_practice_session_insertion(self) -> None:
        """Test that practice sessions are inserted before selected scenarios."""
        inputs = [
            "lab,theater",  # scenarios
            "1",  # permutation length
            "60.0",  # duration
            "lab",  # practice scenes
            "15",  # practice duration
            "",  # clinical preferences
            self.output_dir,  # output directory
            "practice",  # base name
            "",  # user prefix
            "3"  # participant count
        ]

        self._run_main_with_inputs(inputs)

        lab_schedule_path = os.path.join(self.schedules_dir, "practice_lab.json")
        with open(lab_schedule_path, "r", encoding="utf-8") as file:
            schedule = json.load(file)

        steps = schedule.get("steps", [])

        self.assertGreaterEqual(len(steps), 2)
        self.assertEqual(steps[0]["scenarioName"], "lab")
        self.assertFalse(steps[0]["isTutorial"])
        self.assertEqual(steps[0]["duration"], 15.0)

        self.assertEqual(steps[1]["scenarioName"], "lab")
        self.assertFalse(steps[1]["isTutorial"])
        self.assertEqual(steps[1]["duration"], 60.0)

    def test_optimal_permutation_ordering(self) -> None:
        """Test that optimal permutation ordering minimizes overlaps."""
        from generator import (
            create_optimal_permutation_order, 
            calculate_permutation_overlap
        )
        
        # Test with known permutations
        test_permutations = [
            ("mole", "lab"),
            ("mole", "theater"),
            ("lab", "theater"),
            ("theater", "mole"),
            ("butterfly", "lab"),
            ("butterfly", "theater")
        ]
        
        optimal_order = create_optimal_permutation_order(test_permutations)
        
        # Verify we got all permutations back
        self.assertEqual(len(optimal_order), len(test_permutations))
        self.assertEqual(set(optimal_order), set(test_permutations))
        
        # Calculate total overlap score
        total_overlap = sum(
            calculate_permutation_overlap(optimal_order[i-1], optimal_order[i])
            for i in range(1, len(optimal_order))
        )
        
        # Verify the ordering reduces overlap compared to original
        original_overlap = sum(
            calculate_permutation_overlap(
                test_permutations[i-1], test_permutations[i]
            )
            for i in range(1, len(test_permutations))
        )
        
        self.assertLessEqual(total_overlap, original_overlap)

    def test_calculate_permutation_overlap(self) -> None:
        """Test calculation of permutation overlap."""
        from generator import calculate_permutation_overlap
        
        # Test identical permutations
        overlap = calculate_permutation_overlap(
            ("mole", "lab"), ("mole", "lab")
        )
        self.assertEqual(overlap, 2)
        
        # Test partial overlap
        overlap = calculate_permutation_overlap(
            ("mole", "lab"), ("lab", "theater")
        )
        self.assertEqual(overlap, 1)
        
        # Test no overlap
        overlap = calculate_permutation_overlap(
            ("mole", "lab"), ("theater", "butterfly")
        )
        self.assertEqual(overlap, 0)
        
        # Test different length permutations
        overlap = calculate_permutation_overlap(
            ("mole", "lab", "theater"), ("mole", "theater")
        )
        self.assertEqual(overlap, 2)

    def test_generate_users_list_data(self) -> None:
        """Test users list generation with round-robin assignment."""
        from generator import generate_users_list_data
        
        training_plans = ["plan1.json", "plan2.json", "plan3.json"]
        user_details = {"prefix": "test", "digits": 5, "count": 10}
        
        users_data = generate_users_list_data(training_plans, user_details)
        
        # Verify structure
        self.assertIn("users", users_data)
        self.assertEqual(len(users_data["users"]), 10)
        
        # Verify round-robin assignment
        for i, user in enumerate(users_data["users"]):
            expected_plan = training_plans[i % 3]
            self.assertEqual(user["plan"], expected_plan)
            self.assertEqual(user["id"], f"test_{i:05d}")

    def test_round_robin_distribution(self) -> None:
        """Test that round-robin assignment distributes plans evenly."""
        from generator import generate_users_list_data
        
        training_plans = ["plan1.json", "plan2.json", "plan3.json"]
        user_details = {"prefix": "", "digits": 5, "count": 15}
        
        users_data = generate_users_list_data(training_plans, user_details)
        
        # Count plan usage
        plan_counts: dict[str, int] = {}
        for user in users_data["users"]:
            plan = user["plan"]
            plan_counts[plan] = plan_counts.get(plan, 0) + 1
        
        # Verify even distribution
        for plan in training_plans:
            self.assertEqual(plan_counts[plan], 5)

    def test_user_id_generation(self) -> None:
        """Test user ID generation with and without prefix, and custom digit counts."""
        from generator import generate_user_id
        
        # Test without prefix, default digits (5)
        user_id = generate_user_id(0, "")
        self.assertEqual(user_id, "00000")
        
        user_id = generate_user_id(123, "")
        self.assertEqual(user_id, "00123")
        
        # Test with prefix, default digits (5)
        user_id = generate_user_id(0, "test")
        self.assertEqual(user_id, "test_00000")
        
        user_id = generate_user_id(456, "user")
        self.assertEqual(user_id, "user_00456")
        
        # Test with custom digit counts
        user_id = generate_user_id(0, "", 3)
        self.assertEqual(user_id, "000")
        
        user_id = generate_user_id(42, "", 4)
        self.assertEqual(user_id, "0042")
        
        user_id = generate_user_id(7, "test", 6)
        self.assertEqual(user_id, "test_000007")
        
        user_id = generate_user_id(999, "id", 2)
        self.assertEqual(user_id, "id_999")  # Should handle overflow gracefully

    def test_custom_digit_count_integration(self) -> None:
        """Test integration with custom digit count settings."""
        inputs = [
            "mole,lab",  # scenarios
            "1",  # permutation length
            "10.0",  # duration
            "",  # exclusions
            "",  # clinical preferences
            self.output_dir,  # output directory
            "test",  # base name
            "USER",  # user prefix
            "3",  # digit count (custom 3 digits)
            "10"  # participant count
        ]
        
        self._run_main_with_inputs(inputs)
        
        # Get actual directory paths (handles both test and ./output dirs)
        schedules_dir, training_plans_dir, users_list_file = (
            self._get_actual_directories()
        )
        
        # Verify users list was created
        with open(users_list_file, 'r', encoding='utf-8') as file:
            users_list = json.load(file)
        
        # Verify all user IDs have 3 digits
        for user in users_list["users"]:
            # Should have format USER_XXX where XXX is 3 digits
            self.assertTrue(user["id"].startswith("USER_"))
            user_number = user["id"].split("_")[1]
            self.assertEqual(len(user_number), 3)
            self.assertTrue(user_number.isdigit())

    def test_four_digit_user_ids(self) -> None:
        """Test generating 4-digit user IDs as mentioned in the requirements."""
        inputs = [
            "mole",  # scenarios
            "1",  # permutation length
            "5.0",  # duration
            "",  # exclusions
            "",  # clinical preferences
            self.output_dir,  # output directory
            "four_digit",  # base name
            "SICKKIDS",  # user prefix
            "4",  # digit count (4 digits as requested)
            "5"  # participant count
        ]
        
        self._run_main_with_inputs(inputs)
        
        # Get actual directory paths (handles both test and ./output dirs)
        schedules_dir, training_plans_dir, users_list_file = (
            self._get_actual_directories()
        )
        
        # Verify users list was created
        with open(users_list_file, 'r', encoding='utf-8') as file:
            users_list = json.load(file)
        
        # Verify all user IDs have 4 digits
        expected_ids = ["SICKKIDS_0000", "SICKKIDS_0001", "SICKKIDS_0002", 
                       "SICKKIDS_0003", "SICKKIDS_0004"]
        
        actual_ids = [user["id"] for user in users_list["users"]]
        self.assertEqual(actual_ids, expected_ids)

    def test_single_scenario_permutation(self) -> None:
        """Test generating single scenario permutations."""
        inputs = [
            "mole",  # scenarios
            "1",  # permutation length
            "20.0",  # duration
            "",  # practice scenes (skip)
            "",  # exclusions
            "",  # clinical preferences
            self.output_dir,  # output directory
            "single",  # base name
            "participant",  # user prefix
            "5",  # digit count
            "8"  # participant count
        ]
        
        self._run_main_with_inputs(inputs)
        
        # Verify files were created (check both possible directories)
        schedules_dir, training_plans_dir, users_list_file = (
            self._get_actual_directories()
        )
        
        schedule_files = os.listdir(schedules_dir)
        training_plan_files = os.listdir(training_plans_dir)
        
        self.assertEqual(len(schedule_files), 1)
        self.assertEqual(len(training_plan_files), 1)
        
        # Verify users list
        with open(users_list_file, 'r', encoding='utf-8') as file:
            users_list = json.load(file)
            
        self.assertEqual(len(users_list["users"]), 8)
        
        # All users should get the same plan
        for user in users_list["users"]:
            self.assertEqual(user["plan"], training_plan_files[0])

    def test_all_four_scenarios(self) -> None:
        """Test generating permutations with all four scenarios."""
        inputs = [
            "mole,lab,theater,butterfly",  # scenarios
            "2",  # permutation length
            "12.0",  # duration
            "",  # practice scenes (skip)
            "",  # exclusions
            "",  # clinical preferences
            self.output_dir,  # output directory
            "schedule",  # base name
            "u",  # user prefix
            "5",  # digit count
            "25"  # participant count
        ]
        
        self._run_main_with_inputs(inputs)
        
        # Verify files were created
        schedule_files = os.listdir(self.schedules_dir)
        training_plan_files = os.listdir(self.training_plans_dir)
        
        # Should have 12 permutations (4P2)
        self.assertEqual(len(schedule_files), 12)
        self.assertEqual(len(training_plan_files), 12)
        
        # Verify users list
        users_list = self._load_users_list()
        self.assertEqual(len(users_list["users"]), 25)
        
        # Verify round-robin assignment (files are in optimal order now)
        for user in users_list["users"]:
            self.assertIn(user["plan"], training_plan_files)

    def test_new_schema_format(self) -> None:
        """Test that generated schedules follow the new schema format."""
        inputs = [
            "mole,lab",  # scenarios
            "2",  # permutation length
            "10.0",  # duration
            "",  # practice scenes (skip)
            "",  # exclusions
            "prefer_mole_over_lab",  # clinical preferences
            self.output_dir,  # output directory
            "schema_test",  # base name
            "u",  # user prefix
            "5",  # digit count
            "5"  # participant count
        ]
        
        self._run_main_with_inputs(inputs)
        
        # Verify files were created
        schedule_files = os.listdir(self.schedules_dir)
        self.assertTrue(len(schedule_files) > 0)
        
        # Pick the first schedule file and verify its schema
        schedule_file = schedule_files[0]
        schedule_path = os.path.join(self.schedules_dir, schedule_file)
        
        with open(schedule_path, 'r', encoding='utf-8') as file:
            schedule_data = json.load(file)
        
        # Verify top-level structure
        self.assertIn("steps", schedule_data)
        self.assertIsInstance(schedule_data["steps"], list)
        self.assertTrue(len(schedule_data["steps"]) > 0)
        
        # Verify each step has the required fields
        for step in schedule_data["steps"]:
            self.assertIn("clinicalPreferences", step)
            self.assertIn("introVideo", step)
            self.assertIn("duration", step)
            self.assertIn("isTutorial", step)
            self.assertIn("scenarioName", step)
            
            # Verify field types and values
            self.assertIsInstance(step["clinicalPreferences"], str)
            self.assertEqual(step["clinicalPreferences"], "prefer_mole_over_lab")
            self.assertIsInstance(step["introVideo"], str)
            self.assertEqual(step["introVideo"], "")
            self.assertIsInstance(step["duration"], (int, float))
            self.assertEqual(step["duration"], 10.0)
            self.assertIsInstance(step["isTutorial"], bool)
            self.assertEqual(step["isTutorial"], False)
            self.assertIsInstance(step["scenarioName"], str)
            self.assertIn(step["scenarioName"], ["mole", "lab"])

    def _get_actual_directories(self) -> tuple[str, str, str]:
        """Get actual directory paths (handles both test and ./output dirs).
        
        Returns:
            Tuple of (schedules_dir, training_plans_dir, users_list_file).
        """
        if os.path.exists(self.schedules_dir):
            return (
                self.schedules_dir,
                self.training_plans_dir,
                self.users_list_file
            )
        else:
            # Files might be in ./output instead
            return (
                "./output/schedules",
                "./output/training_plans",
                "./output/UsersList.json"
            )


if __name__ == "__main__":
    unittest.main() 
