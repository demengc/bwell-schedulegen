import os
import json
import itertools
from InquirerPy import prompt
from InquirerPy.validator import EmptyInputValidator

def get_scenarios():
    """Gets scenario choices from the user."""
    questions = [
        {
            "type": "checkbox",
            "message": "Select scenarios to include:",
            "choices": ["mole", "lab", "theater", "butterfly"],
            "name": "scenarios",
            "validate": lambda result: len(result) >= 1,
            "invalid_message": "Please select at least one scenario.",
        }
    ]
    return prompt(questions)["scenarios"]

def get_permutation_length(scenarios):
    """Gets the number of scenarios per permutation from the user."""
    questions = [
        {
            "type": "number",
            "message": f"Enter the number of scenarios for each permutation (1-{len(scenarios)}):",
            "name": "length",
            "min_allowed": 1,
            "max_allowed": len(scenarios),
            "validate": EmptyInputValidator(),
            "filter": lambda val: int(val),
        }
    ]
    return prompt(questions)["length"]

def get_duration():
    """Gets the duration for each scenario from the user."""
    questions = [
        {
            "type": "number",
            "message": "Enter the duration in seconds for each scenario:",
            "name": "duration",
            "min_allowed": 0,
            "float_allowed": True,
            "validate": EmptyInputValidator(),
            "filter": lambda val: float(val),
        }
    ]
    return prompt(questions)["duration"]

def get_exclusions(scenarios):
    """Gets scenario combinations to exclude from the user."""
    questions = [
        {
            "type": "checkbox",
            "message": "Select combinations to exclude (if any):",
            "choices": [", ".join(p) for p in itertools.combinations(scenarios, 2)],
            "name": "exclusions",
        }
    ]
    return [tuple(e.split(", ")) for e in prompt(questions)["exclusions"]]

def get_output_details():
    """Gets the output directory and base filename from the user."""
    questions = [
        {"type": "input", "message": "Enter the output directory:", "name": "dir", "default": "./output"},
        {"type": "input", "message": "Enter a base name for the output files:", "name": "basename", "default": "schedule"},
    ]
    return prompt(questions)

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