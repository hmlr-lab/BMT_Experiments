from util import *

bk_path = "BK.pl"
hypothesis_files = "rules.txt"

# Example log files
file_path_log = ["260605_examples/log_0.txt",
                 "260605_examples/log_1.txt",
                "260605_examples/log_2.txt",
                "260605_examples/log_3.txt",
                "260605_examples/log_4.txt",
                 ]

# Generate stage 1 BK files from log files
facts, examples =  generate_bk_from_log(file_path_log, verbose=True)

# Learn Rules

H = learn_rules(facts, examples, bk_path)

# Write rules into a file
with open(hypothesis_files, "w") as f:
    for rule in H:
        pretty_print_prolog(rule)
        f.write(rule + ".\n")
print("Rules written to rules.txt")
