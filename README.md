# ECE-055: Electronics E-Waste Collection and Recycling Credit Engine

An educational command-line project that models how an authorised recycler registers sources, prices e-waste pickups, schedules a vehicle, and prepares credit notes and monthly reports. It uses Python 3.10+ and CSV files; there is no web interface or database.

## What the project does

Treat it as a small operations desk. The input files describe collection sources, category rates, pickup requests, and the item lines in each request. The engine connects those records, totals the weights, decides whether each request is eligible, calculates money, and schedules accepted requests into a vehicle day. It then writes three CSV reports.

For example, suppose a household request contains a computer, cable, and battery. The engine looks up the rate and hazard flag for each category, totals all item weights, gives normal rate-card credit for non-hazardous items, and applies the hazardous handling deduction to the household battery. It calculates any pickup charge, then searches for the earliest eligible vehicle day. The complete request must fit the day’s stop, weight, and hazardous-weight limits together; requests are not split across days.

## Business rules

| ID | Rule |
| --- | --- |
| BR-01 | Category credit is item weight × category rate. Item-line credit is rounded to two decimal places. |
| BR-02 | For HOUSEHOLD sources, hazardous BATTERY and CRT items get a Rs 15/kg handling deduction instead of rate-card credit. BULK sources receive rate-card credit for hazardous items. |
| BR-03 | Pickup is free up to and including 10 km. Beyond 10 km, distance is rounded up to a whole kilometre and charged Rs 12 for each kilometre beyond 10. The charge is waived when request weight is at least 200 kg. |
| BR-04 | HOUSEHOLD requests below 5 kg are refused as `BELOW_MINIMUM`; exactly 5 kg is eligible. BULK has no minimum. |
| BR-05 | Process requests in input order. Each is tried starting the day after its request date. Vehicle days are Monday–Saturday; Sunday is skipped. |
| BR-06 | One vehicle day allows up to 1,200 kg and 8 stops. An accepted request is assigned whole to the earliest day that fits. |
| BR-07 | Hazardous items are limited to 300 kg per vehicle day. Stop count, total weight, and hazardous weight must all fit at once. A request with more than 300 kg hazardous weight is refused as `HAZARD_OVER_LIMIT`. |
| BR-08 | A request weighing more than 1,200 kg is refused as `OVER_CAPACITY`. |
| BR-09 | Net = credits − deductions − pickup charge, rounded half up to whole rupees. A negative net is shown as a positive amount with `net_type=AMOUNT_PAYABLE`. |
| BR-10 | A source collecting at least 500 kg in the requested month receives `RECYCLING_CERTIFICATE` in the monthly summary. |

## Repository map

| Path | Role |
| --- | --- |
| `e_waste_engine/` | Actual capstone implementation. |
| `e_waste_engine/main.py` | Reads `commands.txt`, loads CSVs, calls the engine, and writes reports when report commands occur. |
| `e_waste_engine/models.py` | Defines the Source, Rate, Item, Request, VehicleDay, and Result records. |
| `e_waste_engine/engine.py` | Calculates money and hazardous weight; applies refusal rules; schedules requests. |
| `e_waste_engine/reports.py` | Writes credit notes, pickup schedule, and monthly summary CSVs. |
| `e_waste_engine/phase_2_guide.md` | Additional code walkthrough and key code landmarks. |
| `learning_demo/` | Earlier teaching version, kept separate from the actual engine. It has its own README. |
| `E030-ECE-055-sample-data/` | Supplied input pack and its specification README. The nested folder contains `commands.txt` and the four input CSVs. |
| `E030-ECE-055-sample-data/E030-ECE-055-sample-data/output/` | Reports written by the actual engine using the default command file. |

The supplied input files are not edited by the program. The report files are generated under the pack’s `output/` folder.

## Run the actual engine

Open PowerShell in the repository root and run:

```powershell
python -m e_waste_engine.main
```

Python 3.10 or later is required. The default command file is:

```text
E030-ECE-055-sample-data/E030-ECE-055-sample-data/commands.txt
```

To use a different command file:

```powershell
python -m e_waste_engine.main --commands "path/to/commands.txt"
```

The command file lists the input files and commands in execution order. File paths in it are resolved relative to the folder containing that command file. The program prints concise loading and processing progress, followed by the paths of the three reports.

## Generated reports

The default run creates:

- `credit_notes.csv` — one row per request in request order. Refused requests have reason codes and `NONE` in money and pickup-date fields.
- `pickup_schedule.csv` — one row per accepted request, ordered by pickup date and request order; includes stop number and running day totals.
- `monthly_summary.csv` — one row per source with a scheduled pickup during the month requested by `MONTHLY_SUMMARY`; includes collected weight, credit/payable totals, and certificate status.

Column names and order follow the supplied pack README. The command in the sample pack asks for October 2026.

## How to understand the code

Suggested learning path:

1. Read the sample-pack README for input fields, output columns, and planted scenarios.
2. Read `e_waste_engine/models.py`. These dataclasses are the shapes of the information passed between program parts.
3. Read `e_waste_engine/main.py`. Follow `main()` as it reads one command at a time. The `load_*` functions convert CSV rows into records and catch malformed references.
4. Read `e_waste_engine/engine.py`. `calculate_money()` applies rates, deductions, pickup charges, and rounding. `schedule_one()` first handles refusals, then checks all three vehicle limits together for each candidate day. `process()` preserves request order.
5. Read `e_waste_engine/reports.py`. Each report function turns the in-memory results into rows with the required fields and ordering.
6. Run the program and inspect the CSV headers and a few planted examples from the pack README.
7. Read `learning_demo/README.md` for the earlier guided implementation and its input-to-code mapping. It is a learning aid, separate from the actual engine.

### Scheduling both capacity limits

For each candidate day, the scheduler checks this combined condition before assigning a request:

```text
stops after adding request <= 8
AND total kg after adding request <= 1,200
AND hazardous kg after adding request <= 300
```

If any check fails, it tries the next Monday–Saturday vehicle day. This is why a request can move to a later day even if the vehicle still has total-weight room: hazardous capacity or stop capacity may be full.

## Phase 4 validation and limits

The program has been run against the supplied pack and its output files inspected for the specified headers, column order, and sample scenarios. The run loaded 20 sources, 5 categories, 45 requests, and 80 item lines; it scheduled 43 requests, refused 2, and used 21 vehicle days. The 2026-10-14 schedule reaches exactly 8 stops and 1,200 kg. The monthly report shows SRC-01 at 500 kg with a certificate.

The pack does **not** contain official expected-output CSVs. Therefore, this project has been checked against the written requirements and planted examples, but an exact field-by-field match to the instructor’s hidden evaluation set cannot be claimed. When expected files are provided, compare each generated CSV field by field and resolve any differences before submission.

## Current scope

This implementation follows the supplied one-vehicle rules. Optional multiple-vehicle support and EPR-style category tonnage reports are not included. Shared neighborhood collection points are also outside the supplied input model; the engine treats each registered household request separately.
