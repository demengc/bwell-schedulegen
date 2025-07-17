# bwell-schedulegen

A command-line tool for generating session scheduler configuration files for the National Research Council's (NRC) [bWell](https://nrc.canada.ca/en/research-development/products-services/technical-advisory-services/bwell) application.

## Features

- Generate permutations of training scenarios (mole, lab, theater, butterfly)
- Create schedule files, training plans, and user lists
- Configure scenario duration and exclusion rules
- Round-robin user assignment to training plans

## Usage

```bash
python generator.py
```

The tool guides you through three configuration sections:

1. **Scenario Configuration** - Select scenarios, permutation length, duration, and exclusions
2. **Output Configuration** - Set output directory and file naming
3. **User Configuration** - Configure user IDs and participant count

### Output Structure

```
output/
├── schedules/          # Schedule configuration files
├── training_plans/     # Training plan files
└── UsersList.json      # User assignments
```

### Example

```
Available scenarios: mole, lab, theater, butterfly
Enter scenarios to include: mole,lab,theater,butterfly
Enter the number of scenarios for each permutation (1-4): 2
Enter the duration in seconds for each scenario: 300
Exclusions: theater,butterfly;mole,lab
Output directory: ./output
Base name: training
User ID prefix: SICKKIDS
Number of participants: 50
```

Generates 8 schedule files (12 total permutations minus 4 excluded), 8 training plans, and assigns 50 users with round-robin distribution.

## Disclaimer

This project is not affiliated with or endorsed by the National Research Council (NRC).