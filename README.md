# bwell-schedulegen

A command-line tool for generating session scheduler configuration files for the National Research Council's (NRC) [bWell](https://nrc.canada.ca/en/research-development/products-services/technical-advisory-services/bwell) application. You can specify the scenarios, the number of scenarios per session, the duration of each scenario, and any scenario combinations to exclude.

## Usage

Execute the `generator.py` script:

```bash
python generator.py
```

Follow the prompts to configure the session generation.

The generated files will be placed in the specified output directory (defaults to `./output`). Filenames are generated based on the base name provided and the scenarios included in the permutation (e.g., `basename_scenario1_scenario2.json`).
