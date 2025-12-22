"""bWell Session Scheduler Generator.

This module generates session schedule configuration files and corresponding
training plans for the bWell platform. It creates permutations of scenarios
with user-specified duration and exclusion rules, and generates a users list
with optimized training plan assignments that minimize back-to-back games.
"""

import json
import os
from itertools import permutations
from typing import Any, Optional, TypedDict

# Constants
AVAILABLE_SCENARIOS = ["mole", "lab", "theater", "butterfly"]
DEFAULT_OUTPUT_DIR = "./output"
DEFAULT_BASE_NAME = "schedule"
DEFAULT_REPETITIONS = "1"
USERS_LIST_FILENAME = "UsersList.json"
SMALL_THRESHOLD = 12  # Exact algorithm threshold for TSP optimization
SECTION_WIDTH = 60


class PracticeConfig(TypedDict):
    """Typed configuration for optional practice sessions."""

    scenes: list[str]
    duration: Optional[float]


def print_section_header(title: str) -> None:
    """Print a formatted section header.
    
    Args:
        title: The title of the section.
    """
    print(f"\n{'=' * SECTION_WIDTH}")
    print(f"  {title}")
    print(f"{'=' * SECTION_WIDTH}")


def print_subsection_header(title: str) -> None:
    """Print a formatted subsection header.
    
    Args:
        title: The title of the subsection.
    """
    print(f"\n--- {title} ---")


def normalize_path_for_display(path: str) -> str:
    """Normalize a file path for consistent display using forward slashes.
    
    Args:
        path: The file path to normalize.
        
    Returns:
        Normalized path with forward slashes.
    """
    return path.replace(os.sep, '/')


def get_scenario_configuration() -> tuple[
    list[str], int, float, list[tuple[str, ...]], str, PracticeConfig
]:
    """Get all scenario-related configuration from the user.
    
    Returns:
        Tuple containing scenarios, permutation length, duration, 
        exclusions, clinical preferences, and optional practice configuration.
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

    # Get practice session configuration
    practice_config = get_practice_configuration(scenarios)
    
    # Get exclusions (only if applicable)
    exclusions = []
    if len(scenarios) > 1 and perm_length > 1:
        exclusions = get_exclusions()
    
    # Get clinical preferences
    clinical_preferences = get_clinical_preferences()
    
    return (
        scenarios,
        perm_length,
        duration,
        exclusions,
        clinical_preferences,
        practice_config
    )


def get_output_configuration() -> dict[str, str]:
    """Get all output-related configuration from the user.
    
    Returns:
        Dict containing output directory and base name.
    """
    print_section_header("OUTPUT CONFIGURATION")
    
    output_dir = (
        input(f"Enter the output directory (default: {DEFAULT_OUTPUT_DIR}): ")
        .strip() or DEFAULT_OUTPUT_DIR
    )
    
    base_name = (
        input(f"Enter a base name for the output files "
              f"(default: {DEFAULT_BASE_NAME}): ")
        .strip() or DEFAULT_BASE_NAME
    )
    
    return {"dir": output_dir, "base_name": base_name}


def get_user_configuration() -> dict[str, str | int]:
    """Get all user-related configuration from the user.
    
    Returns:
        Dict containing user ID prefix, digit count, and participant count.
    """
    print_section_header("USER CONFIGURATION")
    
    user_id_prefix = input(
        "Enter user ID prefix (default: none - just numbers): "
    ).strip()
    
    while True:
        try:
            digit_count = int(
                input("Enter the number of digits for user IDs (default: 5): ")
                .strip() or "5"
            )
            
            if 1 <= digit_count <= 10:
                break
            else:
                print("Number of digits must be between 1 and 10.")
                
        except ValueError:
            print("Invalid input. Please enter a number.")
    
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
    
    return {
        "prefix": user_id_prefix, 
        "digits": digit_count,
        "count": participant_count
    }


def get_scenarios() -> list[str]:
    """Get scenario choices from the user.
    
    Returns:
        List of valid scenario names selected by the user.
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


def get_permutation_length(scenarios: list[str]) -> int:
    """Get the number of scenarios per permutation from the user.
    
    Args:
        scenarios: List of available scenarios.
        
    Returns:
        Number of scenarios for each permutation.
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
    """Get the duration for each scenario from the user.

    Returns:
        Duration in seconds for each scenario.
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


def get_practice_configuration(
    selected_scenarios: list[str]
) -> PracticeConfig:
    """Get optional practice session settings from the user.

    Args:
        selected_scenarios: Scenarios chosen for schedule generation.

    Returns:
        Practice configuration containing selected scenes and duration.
    """
    print(
        "\nIf you'd like to include practice sessions before certain scenarios, "
        "list them below. Press Enter to skip."
    )

    while True:
        practice_input = input(
            "Enter scenes for practice sessions (comma-separated): "
        ).strip()

        if not practice_input:
            return {"scenes": [], "duration": None}

        practice_scenes = [
            scene.strip() for scene in practice_input.split(",") if scene.strip()
        ]

        if not practice_scenes:
            print("Please enter at least one valid scene name or press Enter to skip.")
            continue

        invalid_scenes = [
            scene for scene in practice_scenes if scene not in selected_scenarios
        ]

        if invalid_scenes:
            print(
                "Invalid scene(s) for practice: "
                + ", ".join(invalid_scenes)
                + ". Please choose from your selected scenarios."
            )
            continue

        while True:
            try:
                practice_duration = float(
                    input("Enter the duration in seconds for the practice session: ")
                )

                if practice_duration >= 0:
                    return {
                        "scenes": practice_scenes,
                        "duration": practice_duration
                    }

                print("Duration cannot be negative.")

            except ValueError:
                print("Invalid input. Please enter a number.")


def get_exclusions() -> list[tuple[str, ...]]:
    """Get scenario combinations to exclude from the user.
    
    Returns:
        List of scenario tuples to exclude.
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


def get_clinical_preferences() -> str:
    """Get clinical preferences from the user.
    
    Returns:
        String containing clinical preferences.
    """
    print(
        "Enter clinical preferences (e.g., 'norming', 'level1', 'level3'). "
        "Press Enter to skip."
    )
    clinical_preferences_input = input("Clinical Preferences: ").strip()
    
    if not clinical_preferences_input:
        return ""
    
    return clinical_preferences_input


def create_directory_structure(output_dir: str) -> tuple[str, str]:
    """Create the directory structure for schedules and training plans.
    
    Args:
        output_dir: Base output directory path.
        
    Returns:
        Tuple of paths to schedules and training plans directories.
    """
    schedules_dir = os.path.join(output_dir, "schedules")
    training_plans_dir = os.path.join(output_dir, "training_plans")
    
    os.makedirs(schedules_dir, exist_ok=True)
    os.makedirs(training_plans_dir, exist_ok=True)
    
    return schedules_dir, training_plans_dir


def filter_exclusions(
    permutation_list: list[tuple[str, ...]],
    exclusions: list[tuple[str, ...]]
) -> list[tuple[str, ...]]:
    """Filter out permutations that contain excluded scenario combinations.
    
    Args:
        permutation_list: List of scenario permutations.
        exclusions: List of scenario combinations to exclude.
        
    Returns:
        Filtered list of permutations.
    """
    if not exclusions:
        return permutation_list
    
    excluded_permutations: set[tuple[str, ...]] = set()
    
    for exclusion in exclusions:
        for permutation in permutation_list:
            if set(exclusion).issubset(set(permutation)):
                excluded_permutations.add(permutation)
    
    return [
        perm for perm in permutation_list
        if perm not in excluded_permutations
    ]


def generate_schedule_data(
    scenarios: tuple[str, ...],
    duration: float,
    clinical_preferences: str,
    practice_config: Optional[PracticeConfig] = None
) -> dict[str, list[dict[str, str | float | bool]]]:
    """Generate schedule data structure for given scenarios and duration.
    
    Args:
        scenarios: Tuple of scenario names.
        duration: Duration for each scenario step.
        clinical_preferences: String containing clinical preferences.
        practice_config: Optional configuration for practice sessions.
        
    Returns:
        Schedule data structure.
    """
    steps: list[dict[str, str | float | bool]] = []

    practice_scenes: set[str] = set()
    practice_duration: Optional[float] = None

    if practice_config:
        practice_scenes = set(practice_config.get("scenes", []))
        practice_duration = practice_config.get("duration")

    for scenario in scenarios:
        if practice_duration is not None and scenario in practice_scenes:
            steps.append(
                {
                    "clinicalPreferences": clinical_preferences,
                    "introVideo": "",
                    "duration": practice_duration,
                    "isTutorial": False,
                    "scenarioName": scenario
                }
            )

        steps.append(
            {
                "clinicalPreferences": clinical_preferences,
                "introVideo": "",
                "duration": duration,
                "isTutorial": False,
                "scenarioName": scenario
            }
        )

    return {"steps": steps}


def generate_training_plan_data(
    schedule_filename: str
) -> dict[str, list[dict[str, str]]]:
    """Generate training plan data structure for given schedule file.
    
    Args:
        schedule_filename: Name of the corresponding schedule file.
        
    Returns:
        Training plan data structure.
    """
    return {
        "sessions": [
            {
                "schedule_file": schedule_filename,
                "repetitions": DEFAULT_REPETITIONS
            }
        ]
    }


def generate_user_id(user_index: int, prefix: str, digit_count: int = 5) -> str:
    """Generate user ID based on index, optional prefix, and digit count.
    
    Args:
        user_index: Zero-based user index.
        prefix: Optional prefix for user ID.
        digit_count: Number of digits for the user number (default: 5).
        
    Returns:
        Generated user ID.
    """
    user_number = f"{user_index:0{digit_count}d}"
    return f"{prefix}_{user_number}" if prefix else user_number


def calculate_permutation_overlap(
    perm1: tuple[str, ...], perm2: tuple[str, ...]
) -> int:
    """Calculate the number of overlapping scenarios between two permutations.
    
    Args:
        perm1: First permutation.
        perm2: Second permutation.
        
    Returns:
        Number of overlapping scenarios.
    """
    return len(set(perm1).intersection(set(perm2)))


def reconstruct_path(
    dp: list[list[tuple[int, int]]], 
    end_idx: int, 
    full_mask: int
) -> list[int]:
    """Reconstruct the optimal path from dynamic programming table.
    
    Args:
        dp: Dynamic programming table.
        end_idx: Ending index of the path.
        full_mask: Bitmask representing all visited nodes.
        
    Returns:
        List of node indices in the optimal path.
    """
    path = []
    mask = full_mask
    curr = end_idx
    
    while curr != -1:
        path.append(curr)
        _, parent = dp[mask][curr]
        mask ^= (1 << curr)
        curr = parent
    
    path.reverse()
    return path


def calculate_max_consecutive_runs(sequence: list[tuple[str, ...]]) -> int:
    """Calculate the maximum consecutive runs of any scenario.
    
    Args:
        sequence: Sequence of permutations to analyze.
        
    Returns:
        Maximum number of consecutive occurrences of any scenario.
    """
    max_count = 0
    
    for scenario in AVAILABLE_SCENARIOS:
        count = 0
        best = 0
        
        # Include wrap-around by appending first element
        for perm in sequence + sequence[:1]:
            if scenario in perm:
                count += 1
            else:
                best = max(best, count)
                count = 0
        
        best = max(best, count)
        max_count = max(max_count, best)
    
    return max_count


def find_optimal_rotation(
    permutations: list[tuple[str, ...]]
) -> list[tuple[str, ...]]:
    """Find the optimal rotation of permutations to minimize consecutive runs.
    
    Args:
        permutations: List of permutations to rotate.
        
    Returns:
        Optimally rotated list of permutations.
    """
    rotation_best = permutations
    run_best = calculate_max_consecutive_runs(permutations)
    
    for start in range(1, len(permutations)):
        rotated = permutations[start:] + permutations[:start]
        runs = calculate_max_consecutive_runs(rotated)
        
        if runs < run_best:
            rotation_best, run_best = rotated, runs
    
    return rotation_best


def solve_tsp_exact(
    permutations: list[tuple[str, ...]], 
    cost_matrix: list[list[int]]
) -> list[tuple[str, ...]]:
    """Solve TSP exactly using Held-Karp dynamic programming.
    
    Args:
        permutations: List of permutations.
        cost_matrix: Pairwise cost matrix.
        
    Returns:
        Optimal tour of permutations.
    """
    n = len(permutations)
    full_mask = (1 << n) - 1
    
    # dp[mask][i] -> (cost, parent)
    dp: list[list[tuple[int, int]]] = [
        [(float('inf'), -1) for _ in range(n)] for _ in range(1 << n)
    ]
    
    # Start at node 0
    dp[1][0] = (0, -1)
    
    # Fill DP table
    for mask in range(1, full_mask + 1):
        for j in range(n):
            if not (mask & (1 << j)):
                continue
                
            cost_to_j, _ = dp[mask][j]
            if cost_to_j == float('inf'):
                continue
                
            for k in range(n):
                if mask & (1 << k):
                    continue
                    
                new_mask = mask | (1 << k)
                new_cost = cost_to_j + cost_matrix[j][k]
                
                if new_cost < dp[new_mask][k][0]:
                    dp[new_mask][k] = (new_cost, j)
    
    # Find best tour completion
    best_cost = float('inf')
    candidate_ends = []
    
    for j in range(1, n):
        tour_cost = dp[full_mask][j][0] + cost_matrix[j][0]
        if tour_cost < best_cost:
            best_cost = tour_cost
            candidate_ends = [j]
        elif tour_cost == best_cost:
            candidate_ends.append(j)
    
    # Find best rotation among optimal tours
    best_rotation = None
    best_run = float('inf')
    
    for end in candidate_ends:
        path_indices = reconstruct_path(dp, end, full_mask)
        perms = [permutations[i] for i in path_indices]
        rotation_best = find_optimal_rotation(perms)
        run_best = calculate_max_consecutive_runs(rotation_best)
        
        if run_best < best_run:
            best_run = run_best
            best_rotation = rotation_best
    
    return best_rotation or permutations


def solve_tsp_greedy(
    permutations: list[tuple[str, ...]], 
    cost_matrix: list[list[int]]
) -> list[tuple[str, ...]]:
    """Solve TSP using greedy multi-start heuristic.
    
    Args:
        permutations: List of permutations.
        cost_matrix: Pairwise cost matrix.
        
    Returns:
        Good tour of permutations.
    """
    n = len(permutations)
    best_order = None
    best_score = float('inf')
    
    for start_idx in range(n):
        ordered = [permutations[start_idx]]
        remaining = [p for i, p in enumerate(permutations) if i != start_idx]
        
        while remaining:
            last = ordered[-1]
            last_idx = permutations.index(last)
            
            # Choose candidate with minimal cost to last; tie-break by 
            # minimal cumulative cost to all already chosen
            best_candidate = min(
                remaining,
                key=lambda perm: (
                    cost_matrix[last_idx][permutations.index(perm)],
                    sum(cost_matrix[permutations.index(perm)]
                        [permutations.index(o)] for o in ordered)
                )
            )
            
            ordered.append(best_candidate)
            remaining.remove(best_candidate)
        
        # Calculate cyclic cost
        total_cost = sum(
            cost_matrix[permutations.index(ordered[i])]
            [permutations.index(ordered[(i + 1) % n])]
            for i in range(n)
        )
        
        if total_cost < best_score:
            best_score = total_cost
            best_order = ordered
    
    return best_order or permutations


def create_optimal_permutation_order(
    permutations: list[tuple[str, ...]]
) -> list[tuple[str, ...]]:
    """Create an optimal ordering of permutations to minimize consecutive 
    overlaps.
 
    The function treats the problem as a travelling-salesperson tour where
    the "distance" between two nodes is the number of overlapping scenarios.
    An optimal tour therefore minimises the sum of overlaps between each pair
    of consecutive permutations *including* the wrap-around from the last back
    to the first.  

    For small problem sizes (<= 12 permutations) an exact Held-Karp dynamic
    programming algorithm is used to obtain the optimal cycle. For larger
    instances an enhanced greedy heuristic (multi-start nearest-neighbour)
    provides a good approximation while avoiding exponential blow-up.
    
    Args:
        permutations: List of permutations to order.
        
    Returns:
        Optimally ordered list of permutations.
    """
    if not permutations:
        return []
    
    n = len(permutations)
    
    # Trivial case
    if n == 1:
        return permutations
    
    # Pre-compute pairwise overlap costs
    cost_matrix = [
        [calculate_permutation_overlap(p1, p2) for p2 in permutations]
        for p1 in permutations
    ]
    
    # Choose algorithm based on problem size
    if n <= SMALL_THRESHOLD:
        return solve_tsp_exact(permutations, cost_matrix)
    else:
        return solve_tsp_greedy(permutations, cost_matrix)


def generate_users_list_data(
    training_plan_filenames: list[str],
    user_details: dict[str, str | int],
    base_name: str = "",
    permutations_order: list[tuple[str, ...]] | None = None
) -> dict[str, list[dict[str, str]]]:
    """Generate users list data using simple round-robin assignment.
    
    Args:
        training_plan_filenames: List of available training plan filenames.
        user_details: Dictionary containing user prefix and participant count.
        base_name: Base name used in filename generation.
        permutations_order: Optional pre-ordered list of permutations for 
            display.
        
    Returns:
        Users list data structure.
    """
    users = []
    participant_count = int(user_details["count"])
    prefix = str(user_details["prefix"])
    digit_count = int(user_details["digits"])
    
    if not training_plan_filenames:
        return {"users": users}
    
    # Simple round-robin assignment
    for i in range(participant_count):
        user_id = generate_user_id(i, prefix, digit_count)
        plan_index = i % len(training_plan_filenames)
        assigned_plan = training_plan_filenames[plan_index]
        
        users.append({
            "id": user_id,
            "plan": assigned_plan
        })
    
    return {"users": users}


def display_assignment_order(
    optimal_order: list[tuple[str, ...]], 
    base_name: str
) -> None:
    """Display the optimal assignment order of permutations.
    
    Args:
        optimal_order: List of permutations in optimal order.
        base_name: Base name used in filename generation.
    """
    print_section_header("OPTIMIZED ASSIGNMENT ORDER")
    
    print("Training plans will be assigned in this order to minimize "
          "repetition:")
    print("(Users will cycle through this list using round-robin assignment)")
    print()
    
    for i, permutation in enumerate(optimal_order, 1):
        scenario_names = "_".join(permutation)
        filename = create_filename(base_name, scenario_names)
        
        # Calculate overlap with previous permutation
        overlap_info = ""
        if i > 1:
            prev_permutation = optimal_order[i-2]
            overlap = calculate_permutation_overlap(prev_permutation, 
                                                  permutation)
            overlap_info = f" (overlap with previous: {overlap})"
        
        print(f"{i:2d}. {filename}{overlap_info}")
    
    # Calculate and display total overlap score *including* last -> first
    total_overlap = sum(
        calculate_permutation_overlap(
            optimal_order[i], 
            optimal_order[(i + 1) % len(optimal_order)]
        )
        for i in range(len(optimal_order))
    )

    print(f"\nTotal consecutive overlap score (cyclic): {total_overlap}")
    print("(Lower scores indicate better distribution with less repetition, "
          "including wrap-around)")


def create_filename(base_name: str, scenario_names: str) -> str:
    """Create filename based on base name and scenario combination.
    
    Args:
        base_name: Base name for the file.
        scenario_names: Underscore-separated scenario names.
        
    Returns:
        Generated filename.
    """
    if base_name:
        return f"{base_name}_{scenario_names}.json"
    return f"{scenario_names}.json"


def write_json_file(file_path: str, data: dict[str, Any]) -> None:
    """Write data to JSON file with proper formatting.
    
    Args:
        file_path: Path to the output file.
        data: Data to write to the file.
    """
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def generate_files(
    final_permutations: list[tuple[str, ...]],
    duration: float,
    base_name: str,
    schedules_dir: str,
    training_plans_dir: str,
    clinical_preferences: str,
    practice_config: Optional[PracticeConfig] = None
) -> list[str]:
    """Generate schedule and training plan files for all permutations.
    
    Args:
        final_permutations: List of scenario permutations to generate files 
            for.
        duration: Duration for each scenario step.
        base_name: Base name for the files.
        schedules_dir: Directory for schedule files.
        training_plans_dir: Directory for training plan files.
        clinical_preferences: String containing clinical preferences.
        practice_config: Optional configuration for practice sessions.
        
    Returns:
        List of generated training plan filenames.
    """
    print_section_header("GENERATING FILES")
    
    training_plan_filenames = []
    
    for i, permutation in enumerate(final_permutations, 1):
        scenario_names = "_".join(permutation)
        filename = create_filename(base_name, scenario_names)
        
        # Generate and write schedule file
        schedule_data = generate_schedule_data(
            permutation,
            duration,
            clinical_preferences,
            practice_config
        )
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
    training_plan_filenames: list[str],
    user_details: dict[str, str | int],
    output_dir: str,
    base_name: str = "",
    optimal_order: list[tuple[str, ...]] | None = None
) -> None:
    """Generate the users list file.
    
    Args:
        training_plan_filenames: List of training plan filenames.
        user_details: User configuration details.
        output_dir: Output directory path.
        base_name: Base name used in filename generation.
        optimal_order: Optimal order of permutations for display.
    """
    if not training_plan_filenames:
        return
    
    users_list_data = generate_users_list_data(
        training_plan_filenames, user_details, base_name, optimal_order
    )
    users_list_path = os.path.join(output_dir, USERS_LIST_FILENAME)
    write_json_file(users_list_path, users_list_data)

    # Display the assignment order if provided
    if optimal_order:
        display_assignment_order(optimal_order, base_name)


def display_results(
    files_generated: int,
    schedules_dir: str,
    training_plans_dir: str,
    output_dir: str,
    participant_count: int
) -> None:
    """Display the final results in a formatted manner.
    
    Args:
        files_generated: Number of files generated.
        schedules_dir: Path to schedules directory.
        training_plans_dir: Path to training plans directory.
        output_dir: Path to output directory.
        participant_count: Number of participants generated.
    """
    print_section_header("GENERATION COMPLETE")
    
    print(f"[+] Generated {files_generated} schedule files")
    print(f"    Location: {normalize_path_for_display(schedules_dir)}")
    
    print(f"\n[+] Generated {files_generated} training plan files")
    print(f"    Location: {normalize_path_for_display(training_plans_dir)}")
    
    print(f"\n[+] Generated users list with {participant_count} participants")
    users_list_path = os.path.join(output_dir, USERS_LIST_FILENAME)
    print(f"    Location: {normalize_path_for_display(users_list_path)}")
    
    print(f"\n{'=' * SECTION_WIDTH}")
    print("All files generated successfully!")
    print(f"{'=' * SECTION_WIDTH}")


def main() -> None:
    """Generate bWell session scheduler configuration files.
    
    Generates schedule files, corresponding training plan files, and a users
    list with round-robin training plan assignments based on user input for
    scenarios, permutation length, duration, exclusion rules, and user 
    details.
    """
    print("Welcome to the bWell Session Scheduler Generator!")

    try:
        # Get user input in organized sections
        (
            scenarios,
            perm_length,
            duration,
            exclusions,
            clinical_preferences,
            practice_config
        ) = get_scenario_configuration()
        output_details = get_output_configuration()
        user_details = get_user_configuration()
        
        output_dir = output_details["dir"]
        base_name = output_details["base_name"]

        # Create directory structure
        schedules_dir, training_plans_dir = create_directory_structure(
            output_dir
        )

        # Generate and filter permutations
        all_permutations = list(permutations(scenarios, perm_length))
        final_permutations = filter_exclusions(all_permutations, exclusions)
        
        # Create optimal ordering for minimal repetition
        optimal_order = create_optimal_permutation_order(final_permutations)

        # Generate files using optimal order
        training_plan_filenames = generate_files(
            optimal_order,
            duration,
            base_name,
            schedules_dir,
            training_plans_dir,
            clinical_preferences,
            practice_config
        )

        # Generate users list with optimal order
        generate_users_list(
            training_plan_filenames, user_details, output_dir, base_name, 
            optimal_order
        )

        # Display results
        display_results(
            len(optimal_order),
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
