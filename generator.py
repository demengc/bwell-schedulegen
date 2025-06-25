import os
import json
import itertools
# from InquirerPy import prompt
# from InquirerPy.validator import EmptyInputValidator

def get_scenarios():
    """Gets scenario choices from the user."""
    print("Available scenarios: mole, lab, theater, butterfly")
    while True:
        try:
            scenarios_str = input("Enter scenarios to include (comma-separated): ")
            scenarios = [s.strip() for s in scenarios_str.split(",")]
            if not all(s in ["mole", "lab", "theater", "butterfly"] for s in scenarios) or not scenarios:
                raise ValueError
            return scenarios
        except ValueError:
            print("Invalid input. Please enter valid, comma-separated scenarios.")

def get_permutation_length(scenarios):
    """Gets the number of scenarios per permutation from the user."""
    while True:
        try:
            length = int(input(f"Enter the number of scenarios for each permutation (1-{len(scenarios)}): "))
            if 1 <= length <= len(scenarios):
                return length
            else:
                print(f"Please enter a number between 1 and {len(scenarios)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_duration():
    """Gets the duration for each scenario from the user."""
    while True:
        try:
            duration = float(input("Enter the duration in seconds for each scenario: "))
            if duration >= 0:
                return duration
            else:
                print("Duration cannot be negative.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_exclusions(scenarios):
    """Gets scenario combinations to exclude from the user."""
    print("Enter scenario pairs to exclude (e.g., mole,lab;theater,butterfly). Press Enter to skip.")
    exclusions_str = input("Exclusions: ")
    if not exclusions_str:
        return []
    
    exclusion_pairs = [tuple(p.strip().split(",")) for p in exclusions_str.split(";")]
    return exclusion_pairs

def get_output_details():
    """Gets the output directory and base filename from the user."""
    output_dir = input("Enter the output directory (default: ./output): ") or "./output"
    basename = input("Enter a base name for the output files (default: schedule): ") or "schedule"
    return {"dir": output_dir, "basename": basename}

def main():
    """Main function to generate bWell session scheduler configuration files."""
    print("Welcome to the bWell Session Scheduler Generator!")

    scenarios = get_scenarios()
    if not scenarios:
        return

    perm_length = get_permutation_length(scenarios)
    if not perm_length:
        return

    duration = get_duration()
    if duration is None:
        return

    exclusions = []
    if len(scenarios) > 1 and perm_length > 1:
        exclusions = get_exclusions(scenarios)

    output_details = get_output_details()
    output_dir = output_details["dir"]
    base_name = output_details["basename"]

    os.makedirs(output_dir, exist_ok=True)

    permutations = list(itertools.permutations(scenarios, perm_length))
    
    excluded_permutations = set()
    for exclusion in exclusions:
        for p in permutations:
            if set(exclusion).issubset(set(p)):
                excluded_permutations.add(p)

    final_permutations = [p for p in permutations if p not in excluded_permutations]

    count = 0
    for i, p in enumerate(final_permutations):
        data = {"steps": [{"scenarioName": s, "duration": duration} for s in p]}
        scenario_names = "_".join(p)
        if base_name:
            filename = os.path.join(output_dir, f"{base_name}_{scenario_names}.json")
        else:
            filename = os.path.join(output_dir, f"{scenario_names}.json")
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        count += 1

    print(f"\nSuccessfully generated {count} configuration files in '{output_dir}'.")

if __name__ == "__main__":
    main() 