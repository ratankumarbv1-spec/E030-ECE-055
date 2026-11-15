# ECE-055 Decision Log

This log records the main implementation choices for the Electronics E-Waste Collection and Recycling Credit Engine. Entries describe the decisions reflected in the current project; add new entries when the design changes.

| ID | Decision | Reason | Effect |
| --- | --- | --- | --- |
| DL-01 | Use Python 3.10+ for the implementation. | Python was selected by the team because it is readable and approachable for learning and explaining the code. | The engine uses Python dataclasses, `Decimal`, and the built-in `unittest` framework. |
| DL-02 | Build a command-line application, not a web interface. | The brief requires a command-file-driven engine and does not require a user interface. | The program reads `commands.txt`, processes CSV data, and prints concise progress messages. |
| DL-03 | Use the provided CSV files and command file as the input contract. | The evaluation supplies data in this format and expects the engine to follow command order. | Input records are loaded and linked by identifiers; the support pack is preserved as supplied. |
| DL-04 | Use `Decimal` for monetary and weight calculations. | Binary floating-point can produce unexpected rounding differences in money calculations. | Credits, deductions, charges, and totals use decimal arithmetic; the final net uses half-up whole-rupee rounding. |
| DL-05 | Process requests in their input-file order. | The support-pack specification explicitly defines this order for scheduling. | Earlier requests can use available capacity before later requests are considered. |
| DL-06 | Assign each accepted request as one whole stop to the earliest eligible vehicle day. | The supplied specification describes whole requests and earliest-day scheduling. | A request is never split across vehicle days; if it does not fit, the scheduler tries a later day. |
| DL-07 | Check stop, weight, and hazardous limits together before scheduling. | Any one of these limits can make a vehicle day unavailable for a request. | A day is selected only when stops are at most 8, total weight at most 1,200 kg, and hazardous weight at most 300 kg after assignment. |
| DL-08 | Keep the earlier learning demo separate from the actual engine. | The demo was created to understand the workflow before building the capstone implementation. | `learning_demo/` remains a learning reference; the submission engine is in `e_waste_engine/`. |
| DL-09 | Use Python's built-in `unittest` for automated rule checks. | It is available with Python and requires no added test dependency. | Rule tests run with `python -m unittest discover -s tests -v`. |
| DL-10 | Keep generated CSV reports and visual evidence organized separately from source code. | This makes submission outputs and run evidence easier to review. | Machine-readable reports stay in the sample pack's output folder; screenshots are organized under `output/reports/` and the test screenshot under `output/test_evidence/`. |

## Updating this log

When adding or changing an important design choice, append a new `DL-` entry. State the decision and its reason in your own words so you can explain it during the viva. If a decision is later replaced, add a new entry describing the change instead of silently rewriting the earlier history.
