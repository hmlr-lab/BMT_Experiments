# BMT_Experiments

This example demonstrates how to generate symbolic facts from simulation logs and learn logical rules automatically.

## Usage
    File Name: Learning.py
    Execution : Python3 Learning.py

```python
from util import *

bk_path = "BK.pl"
hypothesis_files = "rules.txt"

file_path_log = [
    "../260605_examples/log_0.txt",
    "../260605_examples/log_1.txt",
    "../260605_examples/log_2.txt",
    "../260605_examples/log_3.txt",
    "../260605_examples/log_4.txt",
]

# Generate facts and examples from logs
facts, examples = generate_bk_from_log(file_path_log, verbose=True)

# Learn rules
H = learn_rules(facts, examples, bk_path)

# Save learned rules
with open(hypothesis_files, "w") as f:
    for rule in H:
        pretty_print_prolog(rule)
        f.write(rule + ".\n")

print("Rules written to rules.txt")
```

## Input

* `BK.pl` – Background knowledge.
* `log_*.txt` – Simulation log files.

## Output

* `rules.txt` – Learned Prolog rules.

## Workflow

```text
Log Files
    ↓
generate_bk_from_log()
    ↓
Facts + Examples
    ↓
learn_rules()
    ↓
Learned Rules
    ↓
rules.txt
```

