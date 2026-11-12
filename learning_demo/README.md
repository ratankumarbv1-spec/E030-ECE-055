# Sample Pack Learning Demo

This is a teaching implementation that reads the supplied ECE-055 sample pack using its actual four CSV files and `commands.txt`. It is still a learning demo, not the official capstone implementation. The sample pack is read in place and is never edited.

## Run it

Open PowerShell in the project root and run:

```powershell
python -m learning_demo.run_demo
```

The program reads `commands.txt`, follows its commands from top to bottom, and writes:

- `learning_demo/output/credit_notes.csv`
- `learning_demo/output/pickup_schedule.csv`
- `learning_demo/output/monthly_summary.csv`

The console prints how many records were loaded and scheduled or refused, plus daily weight and hazardous totals. The CSV files contain the field-for-field output layout described in the pack README. These generated files demonstrate this implementation; the pack does not include official expected outputs.

To provide the command file and output location explicitly:

```powershell
python -m learning_demo.run_demo --commands "E030-ECE-055-sample-data/E030-ECE-055-sample-data/commands.txt" --output-dir "learning_demo/output"
```

In PowerShell, spaces separate command parts. `python` starts Python, `-m learning_demo.run_demo` runs this module, `--commands` selects the pack's command list, and `--output-dir` chooses where the reports are saved.

## How the input files connect

| Pack file | Fields the demo uses | What they mean |
| --- | --- | --- |
| `sources.csv` | `source_id`, `source_name`, `source_type`, `area`, `distance_km` | Registered pickup source and depot distance. `contact_mobile` is present in the file but isn't needed for calculations. |
| `rate_card.csv` | `category`, `credit_per_kg_rs`, `hazardous` | Rate and hazardous classification for each category. |
| `requests.csv` | `request_id`, `request_date`, `source_id` | Request identity, its submitted date, and the registered source. The file row order is processing order. |
| `request_items.csv` | `request_id`, `line_no`, `category`, `item_count`, `weight_kg` | Item lines linked to their request. `item_count` is retained as source data but does not affect rules. |
| `commands.txt` | command name and arguments separated by `|` | Tells the demo which files to load, when to process, and which outputs to write. |

Item rows are attached to their request by matching `request_id`, and kept in `line_no` order. The demo resolves file names in `commands.txt` relative to the folder containing that file.

## What each Python file does

- `run_demo.py` reads and executes the command file in order. It prints progress and calls the report writers when the corresponding print command appears.
- `data_loader.py` reads the CSV headers and rows, turns values into typed Python data, joins item lines to requests, and reports malformed references.
- `models.py` defines the data containers for a source, rate, item, request, vehicle day, and processed result.
- `engine.py` calculates hazardous weight and money, refuses requests that cannot be accepted, and schedules the rest.
- `reports.py` writes the three CSV files in the exact column order specified by the sample pack.

Suggested reading order: start with `models.py`, then `data_loader.py`, `engine.py`, `reports.py`, and finally `run_demo.py` to see how the pieces connect.

## Rules implemented in the demo

1. Item-line credit is `weight_kg × category rate`, rounded to two decimals per line.
2. For a HOUSEHOLD source, a rate-card hazardous item receives a Rs 15/kg handling deduction instead of rate-card credit. BULK receives the rate-card credit.
3. Pickup charge is Rs 12 for each whole kilometre above the free 10 km, rounding distance up. The charge is waived at a total request weight of 200 kg or more.
4. A HOUSEHOLD request below 5 kg is refused as `BELOW_MINIMUM`. Exactly 5 kg is eligible. BULK has no minimum.
5. A vehicle day runs Monday-Saturday, has one vehicle, and permits at most 1,200 kg, 8 stops, and 300 kg hazardous material.
6. Requests are processed in file order. Each request is first considered on the next eligible vehicle day after its request date, then on later days until all three limits fit.
7. A request above 300 kg hazardous is refused as `HAZARD_OVER_LIMIT`; one above 1,200 kg total is refused as `OVER_CAPACITY`. Refused notes have `NONE` in their money fields and no pickup date.
8. The final net is rounded half up to a whole rupee. A negative net is represented by a positive `net_rs` and `net_type=AMOUNT_PAYABLE`.
9. Monthly totals use the month of scheduled pickup. A source reaching 500 kg or more in that month receives `RECYCLING_CERTIFICATE` in its summary row.

The rules and assumptions above follow the sample pack's README. If the instructor later provides a clarification or expected output that differs, treat that as authoritative and update the demo only after discussing the change.

## Useful sample cases

- `PKR-002` is 15.7 kg from a source exactly 10 km away, so it has no pickup charge.
- `PKR-004` is 10 kg from 10.1 km away, which rounds to 11 km and gives a Rs 12 pickup charge.
- `PKR-006` is exactly 200 kg, so its distance charge is waived.
- `PKR-009` is a HOUSEHOLD request exactly at 5 kg; `PKR-010` is 4.9 kg and is refused.
- `PKR-015` through `PKR-021` fill 2026-10-14 to 7 stops and 1,150 kg. `PKR-022` adds 50 kg as the eighth stop and reaches exactly 1,200 kg. `PKR-023` has to move to a later day because the stop limit is full.
- `PKR-026` is a 350 kg all-battery BULK request, so it is refused as `HAZARD_OVER_LIMIT`.
- `PKR-040` and `PKR-041` demonstrate that hazardous room is checked together with vehicle weight and stops.
- `SRC-01` has three requests totaling exactly 500 kg in the pack's certificate scenario.

## Interpretation notes for learning

- A shared neighborhood collection point is not part of this supplied sample pack. The pack registers individual named HOUSEHOLD sources, so the demo applies the minimum rule to each request as supplied. The pooling idea can be discussed separately with the instructor; it must not be silently applied to these records.
- The README says the monthly summary has one row per source and a `certificate` field. This demo puts `RECYCLING_CERTIFICATE` or `NONE` in that field on the source row.
- The current demo includes a source in a monthly summary only when it has at least one request scheduled within that pickup month; its request count and money totals cover those scheduled requests. The pack's phrase “one row per source with at least one request” could also be read to include sources with refused-only requests. Confirm that detail with the instructor before treating this interpretation as final.
- The line-credit rule specifies two decimal places, and the net uses half-up rounding to a whole rupee. The demo uses decimal arithmetic to avoid binary-float rounding surprises.
- The pack gives no expected-output files. Compare generated rows to the written rules and planted scenarios, but do not call them official expected answers.
