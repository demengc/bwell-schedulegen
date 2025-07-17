"""
bWell Session Scheduler Generator

This module generates session schedule configuration files and corresponding
training plans for the bWell platform. It creates permutations of scenarios
with user-specified duration and exclusion rules, and generates a users list
with round-robin training plan assignments.
"""

import json
import os
from itertools import permutations
from typing import Dict, List, Set, Tuple, Union

# Constants
AVAILABLE_SCENARIOS = ["mole", "lab", "theater", "butterfly"]
DEFAULT_OUTPUT_DIR = "./output"
DEFAULT_BASE_NAME = "schedule"
DEFAULT_REPETITIONS = "1"
USERS_LIST_FILENAME = "UsersList.json"


def print_section_header(title: str) -> None:
    """
    Print a formatted section header.
    
    Args:
        title: The title of the section.
    """
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_subsection_header(title: str) -> None:
    """
    Print a formatted subsection header.
    
    Args:
        title: The title of the subsection.
    """
    print(f"\n--- {title} ---")


def normalize_path_for_display(path: str) -> str:
    """
    Normalize a file path for consistent display using forward slashes.
    
    Args:
        path: The file path to normalize.
        
    Returns:
        str: Normalized path with forward slashes.
    """
    return path.replace(os.sep, '/')


def get_scenario_configuration() -> Tuple[List[str], int, float, List[Tuple[str, ...]]]:
    """
    Get all scenario-related configuration from the user.
    
    Returns:
        Tuple containing scenarios, permutation length, duration, and exclusions.
    """
    print_section_header("SCENARIO CONFIGURATION")
    
    # Get scenarios
    scenarios = get_scenarios()
    if not scenarios:
        raise ValueError("No scenarios selected")
    
    # Get permutation length
    perm_length = get_permutation_length(scenarios)
    
    # Get duration
    duration = get_duration()
    
    # Get exclusions (only if applicable)
    exclusions = []
    if len(scenarios) > 1 and perm_length > 1:
        exclusions = get_exclusions()
    
    return scenarios, perm_length, duration, exclusions


def get_output_configuration() -> Dict[str, str]:
    """
    Get all output-related configuration from the user.
    
    Returns:
        Dict containing output directory and base name.
    """
    print_section_header("OUTPUT CONFIGURATION")
    
    output_dir = (
        input(f"Enter the output directory (default: {DEFAULT_OUTPUT_DIR}): ").strip()
        or DEFAULT_OUTPUT_DIR
    )
    
    base_name = (
        input(f"Enter a base name for the output files (default: {DEFAULT_BASE_NAME}): ").strip()
        or DEFAULT_BASE_NAME
    )
    
    return {"dir": output_dir, "base_name": base_name}


def get_user_configuration() -> Dict[str, Union[str, int]]:
    """
    Get all user-related configuration from the user.
    
    Returns:
        Dict containing user ID prefix and participant count.
    """
    print_section_header("USER CONFIGURATION")
    
    user_id_prefix = input(
        "Enter user ID prefix (default: none - just 5-digit numbers): "
    ).strip()
    
    while True:
        try:
            participant_count = int(
                input("Enter the number of participants to generate: ")
            )
            
            if participant_count > 0:
                break
            else:
                print("Number of participants must be greater than 0.")
                
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    return {"prefix": user_id_prefix, "count": participant_count}


def get_scenarios() -> List[str]:
    """
    Get scenario choices from the user.
    
    Returns:
        List[str]: List of valid scenario names selected by the user.
    """
    print(f"Available scenarios: {', '.join(AVAILABLE_SCENARIOS)}")
    
    while True:
        try:
            scenarios_input = input(
                "Enter scenarios to include (comma-separated): "
            ).strip()
            
            if not scenarios_input:
                raise ValueError("No scenarios entered")
                
            scenarios = [s.strip() for s in scenarios_input.split(",")]
            
            if not scenarios or not all(
                s in AVAILABLE_SCENARIOS for s in scenarios
            ):
                raise ValueError("Invalid scenario selection")
                
            return scenarios
            
        except ValueError:
            print(
                "Invalid input. Please enter valid, comma-separated scenarios."
            )


def get_permutation_length(scenarios: List[str]) -> int:
    """
    Get the number of scenarios per permutation from the user.
    
    Args:
        scenarios: List of available scenarios.
        
    Returns:
        int: Number of scenarios for each permutation.
    """
    max_length = len(scenarios)
    
    while True:
        try:
            prompt = (
                f"Enter the number of scenarios for each permutation "
                f"(1-{max_length}): "
            )
            length = int(input(prompt))
            
            if 1 <= length <= max_length:
                return length
            else:
                print(f"Please enter a number between 1 and {max_length}.")
                
        except ValueError:
            print("Invalid input. Please enter a number.")


def get_duration() -> float:
    """
    Get the duration for each scenario from the user.
    
    Returns:
        float: Duration in seconds for each scenario.
    """
    while True:
        try:
            duration = float(
                input("Enter the duration in seconds for each scenario: ")
            )
            
            if duration >= 0:
                return duration
            else:
                print("Duration cannot be negative.")
                
        except ValueError:
            print("Invalid input. Please enter a number.")


def get_exclusions() -> List[Tuple[str, ...]]:
    """
    Get scenario combinations to exclude from the user.
    
    Returns:
        List[Tuple[str, ...]]: List of scenario tuples to exclude.
    """
    print(
        "Enter scenario pairs to exclude "
        "(e.g., mole,lab;theater,butterfly). Press Enter to skip."
    )
    exclusions_input = input("Exclusions: ").strip()
    
    if not exclusions_input:
        return []
    
    exclusion_pairs = [
        tuple(pair.strip().split(","))
        for pair in exclusions_input.split(";")
    ]
    
    return exclusion_pairs


def create_directory_structure(output_dir: str) -> Tuple[str, str]:
    """
    Create the directory structure for schedules and training plans.
    
    Args:
        output_dir: Base output directory path.
        
    Returns:
        Tuple[str, str]: Paths to schedules and training plans directories.
    """
    schedules_dir = os.path.join(output_dir, "schedules")
    training_plans_dir = os.path.join(output_dir, "training_plans")
    
    os.makedirs(schedules_dir, exist_ok=True)
    os.makedirs(training_plans_dir, exist_ok=True)
    
    return schedules_dir, training_plans_dir


def filter_exclusions(
    permutation_list: List[Tuple[str, ...]],
    exclusions: List[Tuple[str, ...]]
) -> List[Tuple[str, ...]]:
    """
    Filter out permutations that contain excluded scenario combinations.
    
    Args:
        permutation_list: List of scenario permutations.
        exclusions: List of scenario combinations to exclude.
        
    Returns:
        List[Tuple[str, ...]]: Filtered list of permutations.
    """
    if not exclusions:
        return permutation_list
    
    excluded_permutations: Set[Tuple[str, ...]] = set()
    
    for exclusion in exclusions:
        for permutation in permutation_list:
            if set(exclusion).issubset(set(permutation)):
                excluded_permutations.add(permutation)
    
    return [
        perm for perm in permutation_list
        if perm not in excluded_permutations
    ]


def generate_schedule_data(
    scenarios: Tuple[str, ...], duration: float
) -> Dict[str, List[Dict[str, Union[str, float]]]]:
    """
    Generate schedule data structure for given scenarios and duration.
    
    Args:
        scenarios: Tuple of scenario names.
        duration: Duration for each scenario step.
        
    Returns:
        Dict: Schedule data structure.
    """
    return {
        "steps": [
            {"scenarioName": scenario, "duration": duration}
            for scenario in scenarios
        ]
    }


def generate_training_plan_data(schedule_filename: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Generate training plan data structure for given schedule file.
    
    Args:
        schedule_filename: Name of the corresponding schedule file.
        
    Returns:
        Dict: Training plan data structure.
    """
    return {
        "sessions": [
            {
                "schedule_file": schedule_filename,
                "repetitions": DEFAULT_REPETITIONS
            }
        ]
    }


def generate_user_id(user_index: int, prefix: str) -> str:
    """
    Generate user ID based on index and optional prefix.
    
    Args:
        user_index: Zero-based user index.
        prefix: Optional prefix for user ID.
        
    Returns:
        str: Generated user ID.
    """
    user_number = f"{user_index:05d}"
    
    if prefix:
        return f"{prefix}_{user_number}"
    
    return user_number


def generate_users_list_data(
    training_plan_filenames: List[str],
    user_details: Dict[str, Union[str, int]]
) -> Dict[str, List[Dict[str, str]]]:
    """
    Generate users list data with round-robin training plan assignment.
    
    Args:
        training_plan_filenames: List of available training plan filenames.
        user_details: Dictionary containing user prefix and participant count.
        
    Returns:
        Dict: Users list data structure.
    """
    users = []
    participant_count = int(user_details["count"])
    prefix = str(user_details["prefix"])
    
    for i in range(participant_count):
        user_id = generate_user_id(i, prefix)
        # Round-robin assignment
        training_plan = training_plan_filenames[i % len(training_plan_filenames)]
        
        users.append({
            "id": user_id,
            "plan": training_plan
        })
    
    return {"users": users}


def create_filename(base_name: str, scenario_names: str) -> str:
    """
    Create filename based on base name and scenario combination.
    
    Args:
        base_name: Base name for the file.
        scenario_names: Underscore-separated scenario names.
        
    Returns:
        str: Generated filename.
    """
    if base_name:
        return f"{base_name}_{scenario_names}.json"
    return f"{scenario_names}.json"


def write_json_file(file_path: str, data: Dict) -> None:
    """
    Write data to JSON file with proper formatting.
    
    Args:
        file_path: Path to the output file.
        data: Data to write to the file.
    """
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def generate_files(
    final_permutations: List[Tuple[str, ...]],
    duration: float,
    base_name: str,
    schedules_dir: str,
    training_plans_dir: str
) -> List[str]:
    """
    Generate schedule and training plan files for all permutations.
    
    Args:
        final_permutations: List of scenario permutations to generate files for.
        duration: Duration for each scenario step.
        base_name: Base name for the files.
        schedules_dir: Directory for schedule files.
        training_plans_dir: Directory for training plan files.
        
    Returns:
        List[str]: List of generated training plan filenames.
    """
    print_section_header("GENERATING FILES")
    
    training_plan_filenames = []
    
    for i, permutation in enumerate(final_permutations, 1):
        scenario_names = "_".join(permutation)
        filename = create_filename(base_name, scenario_names)
        
        # Generate and write schedule file
        schedule_data = generate_schedule_data(permutation, duration)
        schedule_path = os.path.join(schedules_dir, filename)
        write_json_file(schedule_path, schedule_data)
        
        # Generate and write training plan file
        training_plan_data = generate_training_plan_data(filename)
        training_plan_path = os.path.join(training_plans_dir, filename)
        write_json_file(training_plan_path, training_plan_data)
        
        training_plan_filenames.append(filename)
        
        print(f"Generated {i}/{len(final_permutations)}: {filename}")
    
    return training_plan_filenames


def generate_users_list(
    training_plan_filenames: List[str],
    user_details: Dict[str, Union[str, int]],
    output_dir: str
) -> None:
    """
    Generate the users list file.
    
    Args:
        training_plan_filenames: List of training plan filenames.
        user_details: User configuration details.
        output_dir: Output directory path.
    """
    if not training_plan_filenames:
        return
    
    users_list_data = generate_users_list_data(
        training_plan_filenames, user_details
    )
    users_list_path = os.path.join(output_dir, USERS_LIST_FILENAME)
    write_json_file(users_list_path, users_list_data)


def display_results(
    files_generated: int,
    schedules_dir: str,
    training_plans_dir: str,
    output_dir: str,
    participant_count: int
) -> None:
    """
    Display the final results in a formatted manner.
    
    Args:
        files_generated: Number of files generated.
        schedules_dir: Path to schedules directory.
        training_plans_dir: Path to training plans directory.
        output_dir: Path to output directory.
        participant_count: Number of participants generated.
    """
    print_section_header("GENERATION COMPLETE")
    
    print(f"✓ Generated {files_generated} schedule files")
    print(f"  Location: {normalize_path_for_display(schedules_dir)}")
    
    print(f"\n✓ Generated {files_generated} training plan files")
    print(f"  Location: {normalize_path_for_display(training_plans_dir)}")
    
    print(f"\n✓ Generated users list with {participant_count} participants")
    print(f"  Location: {normalize_path_for_display(os.path.join(output_dir, USERS_LIST_FILENAME))}")
    
    print(f"\n{'='*60}")
    print("All files generated successfully!")
    print(f"{'='*60}")


def main() -> None:
    """
    Main function to generate bWell session scheduler configuration files.
    
    Generates schedule files, corresponding training plan files, and a users
    list with round-robin training plan assignments based on user input for
    scenarios, permutation length, duration, exclusion rules, and user details.
    """
    print("Welcome to the bWell Session Scheduler Generator!")

    try:
        # Get user input in organized sections
        scenarios, perm_length, duration, exclusions = get_scenario_configuration()
        output_details = get_output_configuration()
        user_details = get_user_configuration()
        
        output_dir = output_details["dir"]
        base_name = output_details["base_name"]

        # Create directory structure
        schedules_dir, training_plans_dir = create_directory_structure(output_dir)

        # Generate and filter permutations
        all_permutations = list(permutations(scenarios, perm_length))
        final_permutations = filter_exclusions(all_permutations, exclusions)

        # Generate files
        training_plan_filenames = generate_files(
            final_permutations, duration, base_name, schedules_dir, training_plans_dir
        )

        # Generate users list
        generate_users_list(training_plan_filenames, user_details, output_dir)

        # Display results
        display_results(
            len(final_permutations),
            schedules_dir,
            training_plans_dir,
            output_dir,
            int(user_details["count"])
        )

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Please try again.")


if __name__ == "__main__":
    main() 