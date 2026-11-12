# ECE-055: Electronics E-Waste Collection and Recycling Credit Engine

This repository contains the work for the ECE-055 engineering capstone. The project models how an authorised recycler can process collection requests from households and bulk sources, calculate recycling credits or amounts payable, and assign accepted pickups to vehicle days.

The project is a command-line application. It reads source, rate-card, request, and item data from CSV files by following a `commands.txt` file. It has no graphical interface or database.

## Understanding the project

Think of the engine as a small operations desk. It receives a list of registered collection sources and pickup requests. For each request, it totals item weights, checks source-specific eligibility, calculates the financial result, and looks for the earliest vehicle day with enough room. The vehicle must satisfy the weight, stop-count, and hazardous-material limits at the same time.

For example, a household request can include a computer, cable, and battery. The engine looks up the rate-card value and hazard flag for each category, totals the request weight, applies the household hazardous-material deduction to the battery, calculates any distance charge, and then schedules the complete request if a vehicle day can accept it. A request is never split between vehicle days.

## Repository layout

| Folder or file | Purpose |
| --- | --- |
| `e_waste_engine/` | Actual capstone implementation, currently at Phase 2 (loading, calculations, refusals, and scheduling). |
| `e_waste_engine/README.md` | Run instructions for the current engine. |
| `e_waste_engine/phase_2_guide.md` | Learning guide with file roles, rule flow, and code landmarks. |
| `learning_demo/` | Earlier learning implementation that writes example CSV reports. Keep it separate from the actual engine. |
| `E030-ECE-055-sample-data/` | Instructor-provided input pack. The nested folder contains the CSVs, command file, and pack README. |
| `.gitignore` | Excludes Python bytecode and virtual-environment folders from Git. |

The sample pack is retained as supplied and is read-only input for these programs. The two Python implementations are separate so the learning demo is not confused with the phased capstone implementation.

## Business rules

These are the rules implemented or planned from the project brief and sample-pack conventions:

| ID | Rule |
| --- | --- |
| BR-01 | Category credit is item weight multiplied by that category's rate-card value. |
| BR-02 | For HOUSEHOLD requests, hazardous categories BATTERY and CRT receive a Rs 15/kg handling deduction instead of a rate-card credit. BULK sources receive the normal rate-card credit for hazardous items. |
| BR-03 | Pickup is free through 10 km. Beyond 10 km, distance is rounded up to a whole kilometre and charged at Rs 12 per kilometre above 10 km. The charge is waived for requests of at least 200 kg. |
| BR-04 | A HOUSEHOLD request below 5 kg is refused as `BELOW_MINIMUM`; exactly 5 kg is eligible. BULK has no minimum. |
| BR-05 | Requests are processed in input order and considered from the day after the request date. Vehicle days are Monday to Saturday. |
| BR-06 | Each vehicle day can hold at most 1,200 kg and 8 stops. A request is assigned whole to the earliest day where it fits. |
| BR-07 | Hazardous material is limited to 300 kg per vehicle day. Weight, stop count, and hazard room are checked together before assignment. A request with over 300 kg hazardous material is refused as `HAZARD_OVER_LIMIT`. |
| BR-08 | A request with total weight over 1,200 kg is refused as `OVER_CAPACITY`. |
| BR-09 | Net amount is credits minus deductions and pickup charge, rounded half up to whole rupees. A negative result is represented as `AMOUNT_PAYABLE` by the source. |
| BR-10 | A source collecting at least 500 kg during a month receives a `RECYCLING_CERTIFICATE` line in that month's summary. |

## Current status

The actual engine is at **Phase 2**. It loads the sample pack, links request item rows to requests, calculates credits/deductions/charges, applies refusal conditions, and schedules accepted requests into one vehicle's days. It prints a compact processing summary.

Phase 3 will add the required credit-note, pickup-schedule, and monthly-summary report files. Phase 4 will compare those files against the official expected outputs when they are provided, address discrepancies, and prepare final submission documentation. The current sample pack does not include official expected-output files, so current run totals are not a claim of matching hidden evaluation results.

The separate `learning_demo/` can generate example output CSVs, but those are demo results and are not official expected answers. Its own README explains how to run it.

## Run the actual engine

Use Python 3.10 or later. Open PowerShell in the repository root and run:

```powershell
python -m e_waste_engine.main
```

The default command path points to the supplied sample pack. To choose another command file:

```powershell
python -m e_waste_engine.main --commands "path/to/commands.txt"
```

The command file determines which CSVs are loaded and when requests are processed. The engine prints loading progress, scheduled/refused totals, vehicle-day count, and a highest-load-day snapshot. At this phase it does not write the three final report files yet.

## Suggested study order

1. Read this README and the support pack README to understand the requirements and input format.
2. Read `e_waste_engine/models.py` to see the records passed between modules.
3. Read `e_waste_engine/main.py` to follow command parsing and CSV loading.
4. Read `e_waste_engine/engine.py` to follow money calculations and scheduling decisions.
5. Use `e_waste_engine/phase_2_guide.md` as a map to the important functions.

The learning demo is a separate implementation with its own [README](learning_demo/README.md), generated report examples, and suggested reading order.
